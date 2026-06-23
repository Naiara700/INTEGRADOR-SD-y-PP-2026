"""
Microservicio: Nodo Coordinador de Tareas (NCT) - Backend y Oráculo
Este componente es el corazón de la red StickerChain. Implementa una API REST asíncrona
con FastAPI. Cumple el rol de 'Join' dentro de la topología distribuida.

Responsabilidades Arquitectónicas:
1. Recepción y Validación: Actúa como Oráculo verificando las reglas de los 4 Smart Contracts
   antes de autorizar una transacción.
2. Empaquetado (Block Proposal): Agrupa transacciones autorizadas en un "Bloque Candidato" y
   las delega al Pool de Transacciones (TrP) para su fragmentación y minado.
3. Consenso y Persistencia (Join): Escucha eventos asíncronos desde RabbitMQ. Cuando un Worker
   encuentra el hash matemático correcto, este nodo valida criptográficamente la Prueba de Trabajo (PoW)
   y, de ser válida, adjunta formalmente el bloque al estado distribuido en Redis.
"""

import os
import json
import time
import hashlib
import hmac
import threading
import pika
import requests
import random
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from contextlib import asynccontextmanager

from db_blockchain import DBBlockchain

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Hook de FastAPI moderno (lifespan). Inicializa los hilos daemon.
    """
    monitor_thread = threading.Thread(target=bully_monitor, daemon=True)
    monitor_thread.start()
    
    join_thread = threading.Thread(target=rabbitmq_join_listener, daemon=True)
    join_thread.start()
    yield

# Inicialización de la aplicación FastAPI y conexión a la base de datos (Redis)
app = FastAPI(
    title="NCT - StickerChain", 
    description="Nodo Coordinador y Oráculo de Contratos Inteligentes",
    lifespan=lifespan
)
db = DBBlockchain()

# Variables de configuración extraídas del entorno para adaptabilidad en Kubernetes
TRP_URL = os.environ.get("TRP_URL", "http://integrador-trp:8001")
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")

# ==============================================================================
# ESTADO DEL ALGORITMO DE BULLY
# ==============================================================================
IS_LEADER = False
HOSTNAME = os.environ.get("HOSTNAME", "nct-0")
try:
    NODE_ID = int(HOSTNAME.split("-")[-1])
except:
    NODE_ID = 0

PEERS_ENV = os.environ.get("PEERS", "nct-0.nct-svc:8000,nct-1.nct-svc:8000,nct-2.nct-svc:8000")
PEERS = [p.strip() for p in PEERS_ENV.split(",") if p.strip()]
LEADER_ID = None
LAST_HEARTBEAT = time.time()
ELECTION_IN_PROGRESS = False

def get_leader_peer_hostname():
    for peer in PEERS:
        try:
            peer_id = int(peer.split(".")[0].split("-")[-1])
            if peer_id == LEADER_ID:
                return peer
        except:
            pass
    return None

def start_election():
    global IS_LEADER, LEADER_ID, ELECTION_IN_PROGRESS
    ELECTION_IN_PROGRESS = True
    higher_peers = []
    
    for peer in PEERS:
        try:
            peer_id = int(peer.split(".")[0].split("-")[-1])
            if peer_id > NODE_ID:
                higher_peers.append(peer)
        except:
            pass
            
    got_response = False
    for peer in higher_peers:
        try:
            resp = requests.post(f"http://{peer}/bully/election", json={"node_id": NODE_ID, "hostname": HOSTNAME}, timeout=2)
            if resp.status_code == 200:
                got_response = True
        except:
            pass
            
    if not got_response:
        IS_LEADER = True
        LEADER_ID = NODE_ID
        ELECTION_IN_PROGRESS = False
        print(f"NCT {NODE_ID}: SOY EL NUEVO LIDER!")
        for peer in PEERS:
            try:
                peer_id = int(peer.split(".")[0].split("-")[-1])
                if peer_id < NODE_ID:
                    requests.post(f"http://{peer}/bully/coordinator", json={"node_id": NODE_ID, "hostname": HOSTNAME}, timeout=2)
            except:
                pass
    else:
        IS_LEADER = False

def bully_monitor():
    global LAST_HEARTBEAT, IS_LEADER, LEADER_ID
    while True:
        time.sleep(5)
        if IS_LEADER:
            continue
            
        if LEADER_ID is None:
            start_election()
            continue
            
        leader_peer = get_leader_peer_hostname()
        if leader_peer:
            try:
                resp = requests.get(f"http://{leader_peer}/bully/heartbeat", timeout=2)
                if resp.status_code == 200 and resp.json().get("is_leader"):
                    LAST_HEARTBEAT = time.time()
                else:
                    raise Exception("Not leader anymore")
            except:
                print(f"NCT {NODE_ID}: Líder {LEADER_ID} no responde. Iniciando elección...")
                LEADER_ID = None
                start_election()

@app.middleware("http")
async def bully_leadership_middleware(request: Request, call_next):
    if request.url.path.startswith("/smart_contracts/") and not request.url.path.startswith("/bully/"):
        if not IS_LEADER:
            leader_host = get_leader_peer_hostname()
            if not leader_host:
                return JSONResponse(status_code=503, content={"detail": "Elección de líder en progreso. Intente nuevamente en unos segundos."})
            url = f"http://{leader_host}{request.url.path}"
            # 307 preserve method and body
            return RedirectResponse(url=url, status_code=307)
    response = await call_next(request)
    return response

class BullyMessage(BaseModel):
    node_id: int
    hostname: str

@app.post("/bully/election")
def bully_election(msg: BullyMessage):
    global ELECTION_IN_PROGRESS
    if msg.node_id < NODE_ID:
        threading.Thread(target=start_election, daemon=True).start()
        return {"status": "ok", "message": "I will take over"}
    return {"status": "ignored"}

@app.post("/bully/coordinator")
def bully_coordinator(msg: BullyMessage):
    global IS_LEADER, LEADER_ID, ELECTION_IN_PROGRESS, LAST_HEARTBEAT
    IS_LEADER = False
    LEADER_ID = msg.node_id
    ELECTION_IN_PROGRESS = False
    LAST_HEARTBEAT = time.time()
    return {"status": "ok"}

@app.get("/bully/heartbeat")
def bully_heartbeat():
    return {"status": "alive", "node_id": NODE_ID, "is_leader": IS_LEADER}

# Mempool temporal en memoria para agrupar transacciones antes del minado
pending_transactions: List[Dict[str, Any]] = []

# Dificultad objetivo. (Se exige que el hash generado comience con este prefijo)
DIFFICULTY_PREFIX = "0000" 

# ==============================================================================
# Pool de Figuritas y RNG (Gacha System - Mundial 2026)
# ==============================================================================

EQUIPOS_MUNDIAL = {}
JUGADORES_DORADOS = []

def cargar_base_datos_mundial():
    global EQUIPOS_MUNDIAL, JUGADORES_DORADOS
    # Ruta al archivo .txt ubicado en la raíz del proyecto
    archivo = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mundial_2026_album_figuritas.txt")
    if not os.path.exists(archivo):
        print("ADVERTENCIA: No se encontró el archivo del Mundial 2026.")
        return
        
    with open(archivo, "r", encoding="utf-8") as f:
        lineas = f.readlines()
        
    equipo_actual = None
    modo = None
    
    for linea in lineas:
        linea = linea.strip()
        if linea.startswith("EQUIPO:"):
            equipo_actual = linea.split("EQUIPO:")[1].strip()
            # Añadir automáticamente Escudo y Foto Grupal para llegar a las 20 requeridas
            EQUIPOS_MUNDIAL[equipo_actual] = ["Escudo Oficial", "Foto Grupal"]
        elif linea.startswith("JUGADORES DESTACADOS"):
            modo = "destacados"
        elif linea.startswith("PLANTILLA COMPLETA"):
            modo = "plantilla"
        elif linea.startswith("*") and modo == "destacados":
            jugador = linea.replace("*", "").strip()
            if jugador not in JUGADORES_DORADOS:
                JUGADORES_DORADOS.append(jugador)
        elif modo == "plantilla" and linea and linea[0].isdigit():
            # Formato: 01. Nombre
            partes = linea.split(".", 1)
            if len(partes) == 2:
                num = int(partes[0].strip())
                jugador = partes[1].strip()
                # Solo tomamos los primeros 18 jugadores para llegar a 20 tokens por equipo
                if num <= 18:
                    if jugador == "[Jugador por confirmar]":
                        # Hacemos el nombre único para no romper el conteo de figuritas únicas
                        jugador = f"Jugador {num} (Por confirmar)"
                    EQUIPOS_MUNDIAL[equipo_actual].append(jugador)

cargar_base_datos_mundial()

RAREZAS = [
    {"nivel": "Común", "probabilidad": 0.70},
    {"nivel": "Épica", "probabilidad": 0.25},
    {"nivel": "Legendaria", "probabilidad": 0.05}
]

def generar_figurita_rng():
    """
    Algoritmo de Probabilidad para generar figuritas.
    Garantiza la escasez matemática de las rarezas mayores.
    """
    rand_rareza = random.random()
    acumulado = 0.0
    rareza_elegida = "Común"
    for r in RAREZAS:
        acumulado += float(r["probabilidad"])
        if rand_rareza <= acumulado:
            rareza_elegida = r["nivel"]
            break
            
    equipo = random.choice(list(EQUIPOS_MUNDIAL.keys()))
    jugador = random.choice(EQUIPOS_MUNDIAL[equipo])
    
    # Generar ID único usando criptografía simple para rastrear la figurita
    fig_id = f"FIG_{hashlib.md5(f'{jugador}{time.time()}{random.random()}'.encode()).hexdigest()[:8]}"
    
    return {
        "fig_id": fig_id,
        "tipo": "NFT_Sticker",
        "jugador": jugador,
        "equipo": equipo,
        "rareza": rareza_elegida
    }

# Clave secreta para validación de QRs físicos (No compartir en entornos reales)
QR_SECRET_KEY = os.environ.get("QR_SECRET_KEY", "sdypp2026")

# ==============================================================================
# Modelos de Datos (Pydantic) para Validación Rigurosa de Payloads REST
# ==============================================================================

class QRRequest(BaseModel):
    wallet_id: str = Field(..., description="ID de la billetera del usuario")
    nonce: str = Field(..., description="ID único e irrepetible impreso en el QR físico")
    firma_hmac: str = Field(..., description="Firma criptográfica HMAC-SHA256 validando la autenticidad")

class BuyPackRequest(BaseModel):
    wallet_id: str = Field(..., description="ID de la billetera que desea comprar un sobre")

class SwapRequest(BaseModel):
    usuario_a: str = Field(..., description="ID del emisor de la figurita X")
    usuario_b: str = Field(..., description="ID del emisor de la figurita Y")
    fig_x: str = Field(..., description="ID de la figurita entregada por Usuario A")
    fig_y: str = Field(..., description="ID de la figurita entregada por Usuario B")

class ClaimRewardRequest(BaseModel):
    wallet_id: str = Field(..., description="ID de la billetera reclamante del premio final")
    tipo_desafio: str = Field(..., description="Puede ser LOGIN_DIARIO, COLECCIONISTA_PRINCIPIANTE, FIGURITA_DORADA, u HOJA_COMPLETA")


# ==============================================================================
# Funciones Internas de Arquitectura (Empaquetado y Derivación)
# ==============================================================================

def add_transaction_to_mempool(tx_data: Dict[str, Any]):
    """
    Agrega una transacción verificada al mempool en memoria.
    Si el mempool alcanza el límite establecido (e.g., 5 TXs), gatilla
    la creación del "Bloque Candidato" y lo expide al clúster de minería.
    """
    global pending_transactions
    pending_transactions.append(tx_data)
    
    # Batch threshold: 5 transacciones por bloque para mantener fluidez
    if len(pending_transactions) >= 5:
        pack_candidate_block()

def pack_candidate_block():
    """
    Construye la estructura inmutable del Bloque Candidato.
    Enlaza criptográficamente el bloque con el historial previo obteniendo
    el hash del último bloque cerrado. Luego, emite una solicitud HTTP POST
    hacia el Pool de Transacciones (TrP) para que este fragmente matemáticamente
    la búsqueda del nonce y despache tareas a RabbitMQ.
    """
    global pending_transactions
    if not pending_transactions:
        return
        
    latest_block = db.get_latest_block()
    
    # Reglas de enlace causal de la blockchain
    index = int(latest_block["index"]) + 1 if latest_block else 0
    previous_hash = latest_block["block_hash"] if latest_block else ("0" * 32)
    
    candidate_block = {
        "index": index,
        "previous_hash": previous_hash,
        "timestamp": int(time.time()),
        "transactions": pending_transactions.copy(),
        "difficulty_prefix": DIFFICULTY_PREFIX
    }
    
    # Delegar la carga de trabajo intensiva al microservicio de fragmentación (TrP)
    try:
        response = requests.post(f"{TRP_URL}/split", json=candidate_block, timeout=5)
        response.raise_for_status()
        print(f"NCT: Bloque {index} enviado exitosamente al Pool de Transacciones para Split.")
        
        # Limpiamos el mempool tras despachar exitosamente
        pending_transactions = []
    except requests.exceptions.RequestException as e:
        print(f"NCT Error CRÍTICO: No se pudo contactar al TrP en {TRP_URL}. Detalle: {e}")


# ==============================================================================
# Smart Contracts - Lógica de Negocio y Oráculo Rest
# ==============================================================================

@app.post("/smart_contracts/mint_points", summary="Contrato de Emisión (MINT_POINTS)")
def mint_points_contract(req: QRRequest):
    """
    Valida criptográficamente un QR físico mediante HMAC-SHA256 con prevención de doble gasto.
    Actúa como un Oráculo seguro.
    """
    # 1. Verificar Doble Gasto en Redis
    if db.fue_qr_usado(req.nonce):
        raise HTTPException(status_code=400, detail="FRAUDE: Este QR físico ya fue escaneado y gastado anteriormente.")

    # 2. Validación de Firma Criptográfica
    mensaje = f"{req.nonce}:{req.wallet_id}"
    firma_esperada = hmac.new(QR_SECRET_KEY.encode(), mensaje.encode(), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(firma_esperada, req.firma_hmac):
        raise HTTPException(status_code=403, detail="FRAUDE: Firma del QR inválida o falsificada matemáticamente.")

    # 3. Éxito: Marcar usado y emitir transacción
    db.marcar_qr_usado(req.nonce)
    
    tx = {
        "usuario_a": "Sistema_Sponsor",
        "usuario_b": req.wallet_id,
        "monto": 500,
        "metadata": {"concepto": f"Escaneo validado QR {req.nonce}"}
    }
    add_transaction_to_mempool(tx)
    return {"status": "success", "message": "Firma verificada exitosamente. 500 PTS asignados al mempool."}

@app.post("/smart_contracts/buy_pack", summary="Contrato de Apertura (BUY_PACK)")
def buy_pack_contract(req: BuyPackRequest):
    """
    Verifica los fondos disponibles en el ledger y, de ser suficientes, 
    ejecuta una transacción atómica doble: 
    1) Quema (burn) los puntos del usuario.
    2) Emite (mint) 5 tokens no fungibles (figuritas) asociadas criptográficamente a la billetera.
    """
    estado_billetera = db.get_wallet_state(req.wallet_id)
    
    if estado_billetera["puntos_disponibles"] >= 500:
        # Transacción de debito (Burn)
        tx_burn = {
            "usuario_a": req.wallet_id,
            "usuario_b": "Direccion_Nula_Tesoreria",
            "monto": 500,
            "metadata": {"concepto": "Pago por apertura de sobre virtual"}
        }
        add_transaction_to_mempool(tx_burn)
        
        # Transacción de Emisión de Activos (Minting de Figuritas con RNG)
        for _ in range(5):
            fig_data = generar_figurita_rng()
            tx_mint = {
                "usuario_a": "Direccion_Nula_Tesoreria",
                "usuario_b": req.wallet_id,
                "monto": 1,
                "metadata": fig_data
            }
            add_transaction_to_mempool(tx_mint)
            
        return {"status": "success", "message": "Fondos verificados. Transacciones de sobre encoladas."}
    
    raise HTTPException(status_code=400, detail="Fondos insuficientes en la blockchain.")

@app.post("/smart_contracts/swap_stickers", summary="Contrato de Intercambio (SWAP_STICKERS)")
def swap_stickers_contract(req: SwapRequest):
    """
    Ejecuta un swap atómico P2P entre dos billeteras. Verifica rígidamente en la blockchain 
    que ambos usuarios posean el activo subyacente que desean intercambiar.
    Previene el doble gasto y operaciones fraudulentas.
    """
    estado_a = db.get_wallet_state(req.usuario_a)
    estado_b = db.get_wallet_state(req.usuario_b)
    
    # 1. Encontrar la metadata de los tokens solicitados
    fig_x_data = next((f for f in estado_a["figuritas_poseidas"] if isinstance(f, dict) and f.get("fig_id") == req.fig_x), None)
    fig_y_data = next((f for f in estado_b["figuritas_poseidas"] if isinstance(f, dict) and f.get("fig_id") == req.fig_y), None)
    
    if not fig_x_data:
        raise HTTPException(status_code=400, detail=f"Inconsistencia: El emisor A no posee el token {req.fig_x}")
    if not fig_y_data:
        raise HTTPException(status_code=400, detail=f"Inconsistencia: El emisor B no posee el token {req.fig_y}")
        
    # 2. Validar regla de "Pegada vs Repetida"
    # Solo se puede intercambiar si el jugador está repetido (>1 copias en el inventario)
    count_jugador_a = sum(1 for f in estado_a["figuritas_poseidas"] if isinstance(f, dict) and f.get("jugador") == fig_x_data.get("jugador"))
    count_jugador_b = sum(1 for f in estado_b["figuritas_poseidas"] if isinstance(f, dict) and f.get("jugador") == fig_y_data.get("jugador"))
    
    if count_jugador_a <= 1:
        raise HTTPException(status_code=400, detail=f"Inconsistencia: El usuario A tiene su única copia de {fig_x_data.get('jugador')} pegada en el álbum. Solo puede intercambiar repetidas.")
    if count_jugador_b <= 1:
        raise HTTPException(status_code=400, detail=f"Inconsistencia: El usuario B tiene su única copia de {fig_y_data.get('jugador')} pegada en el álbum. Solo puede intercambiar repetidas.")
        
    # Doble transacción atómica para el Swap
    tx_swap_1 = {
        "usuario_a": req.usuario_a, "usuario_b": req.usuario_b, "monto": 1,
        "metadata": {"fig_id": req.fig_x, "operacion": "SWAP_P2P"}
    }
    tx_swap_2 = {
        "usuario_a": req.usuario_b, "usuario_b": req.usuario_a, "monto": 1,
        "metadata": {"fig_id": req.fig_y, "operacion": "SWAP_P2P"}
    }
    
    add_transaction_to_mempool(tx_swap_1)
    add_transaction_to_mempool(tx_swap_2)
    return {"status": "success", "message": "Contrato P2P validado. Intercambio atómico encolado."}

@app.post("/smart_contracts/claim_reward", summary="Contrato de Recompensa (CLAIM_REWARD)")
def claim_reward_contract(req: ClaimRewardRequest):
    """
    Audita el estado actual en la blockchain y la base Redis para liberar premios si y solo si 
    las reglas de negocio reales se cumplen, evitando abusos y reclamos dobles.
    """
    estado_billetera = db.get_wallet_state(req.wallet_id)
    figuritas_poseidas = estado_billetera["figuritas_poseidas"]
    
    # Evaluar los desafíos reales propuestos
    if req.tipo_desafio == "LOGIN_DIARIO":
        if db.fue_desafio_reclamado(req.wallet_id, "LOGIN_DIARIO", es_diario=True):
            raise HTTPException(status_code=400, detail="FRAUDE: Ya reclamaste tu recompensa diaria de inicio de sesión hoy.")
            
        db.marcar_desafio(req.wallet_id, "LOGIN_DIARIO", es_diario=True)
        tx_premio = {"usuario_a": "Direccion_Nula_Tesoreria", "usuario_b": req.wallet_id, "monto": 50, "metadata": {"concepto": "Login Diario"}}
        add_transaction_to_mempool(tx_premio)
        return {"status": "success", "message": "50 PTS de login diario cobrados exitosamente."}
        
    elif req.tipo_desafio == "COLECCIONISTA_PRINCIPIANTE":
        if db.fue_desafio_reclamado(req.wallet_id, "COLECCIONISTA_PRINCIPIANTE", es_diario=False):
             raise HTTPException(status_code=400, detail="FRAUDE: Ya reclamaste este logro único.")
             
        jugadores_unicos = set()
        for fig in figuritas_poseidas:
            if isinstance(fig, dict) and "jugador" in fig:
                jugadores_unicos.add(fig["jugador"])
             
        if len(jugadores_unicos) >= 5:
            db.marcar_desafio(req.wallet_id, "COLECCIONISTA_PRINCIPIANTE", es_diario=False)
            tx_premio = {"usuario_a": "Direccion_Nula_Tesoreria", "usuario_b": req.wallet_id, "monto": 500, "metadata": {"concepto": "Logro: 5 Jugadores Únicos"}}
            add_transaction_to_mempool(tx_premio)
            return {"status": "success", "message": "Logro de Coleccionista Principiante completado! 500 PTS cobrados."}
            
    elif req.tipo_desafio == "FIGURITA_DORADA":
        if db.fue_desafio_reclamado(req.wallet_id, "FIGURITA_DORADA", es_diario=False):
             raise HTTPException(status_code=400, detail="FRAUDE: Ya reclamaste la recompensa por esta figurita dorada.")
             
        # El logro se desbloquea si tienes una figurita Legendaria de alguna de las estrellas del Mundial
        tiene_dorada = any(
            isinstance(fig, dict) and fig.get("jugador") in JUGADORES_DORADOS and fig.get("rareza") == "Legendaria"
            for fig in figuritas_poseidas
        )
             
        if tiene_dorada:
            db.marcar_desafio(req.wallet_id, "FIGURITA_DORADA", es_diario=False)
            tx_premio = {"usuario_a": "Direccion_Nula_Tesoreria", "usuario_b": req.wallet_id, "monto": 2000, "metadata": {"concepto": "Logro: Obtuviste un Jugador Dorado Legendario"}}
            add_transaction_to_mempool(tx_premio)
            return {"status": "success", "message": "Logro de Figurita Dorada completado! 2000 PTS cobrados."}

    elif req.tipo_desafio == "HOJA_COMPLETA":
        if db.fue_desafio_reclamado(req.wallet_id, "HOJA_COMPLETA", es_diario=False):
             raise HTTPException(status_code=400, detail="FRAUDE: Ya reclamaste el premio de hoja completa.")
             
        equipos_completos = False
        jugadores_por_equipo = {}
        
        for fig in figuritas_poseidas:
            if isinstance(fig, dict) and "equipo" in fig and "jugador" in fig:
                eq = fig["equipo"]
                if eq not in jugadores_por_equipo:
                    jugadores_por_equipo[eq] = set()
                jugadores_por_equipo[eq].add(fig["jugador"])
                
                # Regla: 20 figuritas únicas de la misma selección del Mundial 2026 (18 Jugadores + Escudo + Foto Grupal)
                if len(jugadores_por_equipo[eq]) >= 20:
                    equipos_completos = True
                    break
             
        if equipos_completos:
            db.marcar_desafio(req.wallet_id, "HOJA_COMPLETA", es_diario=False)
            tx_premio = {"usuario_a": "Direccion_Nula_Tesoreria", "usuario_b": req.wallet_id, "monto": 5000, "metadata": {"concepto": "Premio por Desafío: Selección Completada"}}
            add_transaction_to_mempool(tx_premio)
            return {"status": "success", "message": "Hoja de Selección verificada criptográficamente. 5000 PTS emitidos."}
            
    raise HTTPException(status_code=400, detail="Progreso insuficiente para el desafío, o el desafío indicado no existe en los Smart Contracts.")


# ==============================================================================
# Hilo de Consenso Asíncrono - Función JOIN de RabbitMQ
# ==============================================================================

def rabbitmq_join_listener():
    """
    (Daemon Thread) Se suscribe a RabbitMQ solo si es Líder.
    """
    time.sleep(10) 
    while True:
        if not IS_LEADER:
            time.sleep(5)
            continue
            
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            channel = connection.channel()
            channel.queue_declare(queue='solved_blocks')
            
            def on_solved_block_received(ch, method, properties, body):
                data = json.loads(body)
                candidate = data.get("candidate", {})
                nonce = data.get("nonce")
                reported_hash = data.get("block_hash", "")
                
                base_string = f"{candidate.get('previous_hash', '')}{json.dumps(candidate.get('transactions', []))}"
                calculated_hash = hashlib.md5(f"{base_string}{nonce}".encode('utf-8')).hexdigest()
                
                if calculated_hash == reported_hash and calculated_hash.startswith(candidate.get('difficulty_prefix', '')):
                    print(f"NCT {NODE_ID} [JOIN]: Validación EXITOSA Bloque {candidate.get('index')}. Hash: {calculated_hash}")
                    
                    candidate["nonce"] = nonce
                    candidate["block_hash"] = calculated_hash
                    candidate["transactions"] = json.dumps(candidate["transactions"])
                    
                    if "difficulty_prefix" in candidate:
                        del candidate["difficulty_prefix"]
                        
                    if db.save_block(candidate):
                        print(f"NCT {NODE_ID} [JOIN]: Bloque {candidate.get('index')} persistido.")
                else:
                    print(f"NCT {NODE_ID} [JOIN] CRÍTICO: Bloque rechazado.")
                    
            channel.basic_consume(queue='solved_blocks', on_message_callback=on_solved_block_received, auto_ack=True)
            print(f"NCT {NODE_ID} [LÍDER]: Escuchando Proof of Works...")
            
            # Consume events without blocking indefinitely, allowing us to check IS_LEADER
            while IS_LEADER:
                connection.process_data_events(time_limit=2)
                
            connection.close()
            print(f"NCT {NODE_ID}: Perdí el liderazgo. Desconectando de RabbitMQ.")
            
        except Exception as e:
            print(f"NCT Error CRÍTICO: Fallo en la conexión asíncrona con RabbitMQ: {e}")
            time.sleep(5)

# Entrada para entorno de ejecución local (Desarrollo)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
