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

from operator import index
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

# Criptografía asimétrica
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

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
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")

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
# DIFFICULTY_PREFIX = "0000" 
# ==============================================================================
# DIFICULTAD DINÁMICA DE MINERÍA
# ==============================================================================

INITIAL_DIFFICULTY_LEN = int(os.environ.get("INITIAL_DIFFICULTY_LEN", 4))
MIN_DIFFICULTY_LEN = int(os.environ.get("MIN_DIFFICULTY_LEN", 1))
MAX_DIFFICULTY_LEN = int(os.environ.get("MAX_DIFFICULTY_LEN", 8))

# Si un bloque se resuelve por debajo de este tiempo, subimos dificultad.
POW_TOO_FAST_SECONDS = float(os.environ.get("POW_TOO_FAST_SECONDS", 3.0))

# Si un bloque tarda más que este tiempo, bajamos dificultad.
POW_TOO_SLOW_SECONDS = float(os.environ.get("POW_TOO_SLOW_SECONDS", 20.0))

current_difficulty_len = INITIAL_DIFFICULTY_LEN

# Guarda tiempos de inicio de minado por índice de bloque.
mining_started_at = {}


def get_current_difficulty_prefix():
    """
    Devuelve el prefijo actual de dificultad.
    Ejemplo:
        current_difficulty_len = 4 -> "0000"
    """
    return "0" * current_difficulty_len


def ajustar_dificultad(segundos_resolucion):
    """
    Ajusta dinámicamente la dificultad según el tiempo de resolución.

    - Si se resuelve muy rápido, agrega un cero.
    - Si tarda demasiado, quita un cero.
    - Respeta límites mínimo y máximo.
    """
    global current_difficulty_len

    dificultad_anterior = current_difficulty_len

    if segundos_resolucion < POW_TOO_FAST_SECONDS:
        current_difficulty_len = min(
            current_difficulty_len + 1,
            MAX_DIFFICULTY_LEN
        )
    elif segundos_resolucion > POW_TOO_SLOW_SECONDS:
        current_difficulty_len = max(
            current_difficulty_len - 1,
            MIN_DIFFICULTY_LEN
        )

    if current_difficulty_len != dificultad_anterior:
        print(
            "NCT [DIFFICULTAD]: "
            f"Tiempo={segundos_resolucion:.3f}s. "
            f"Dificultad {dificultad_anterior} -> {current_difficulty_len} "
            f"({get_current_difficulty_prefix()})"
        )
    else:
        print(
            "NCT [DIFICULTAD]: "
            f"Tiempo={segundos_resolucion:.3f}s. "
            f"Se mantiene dificultad {current_difficulty_len} "
            f"({get_current_difficulty_prefix()})"
        )

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
            EQUIPOS_MUNDIAL[equipo_actual] = []
        elif linea.startswith("JUGADORES DESTACADOS"):
            modo = "destacados"
        elif linea.startswith("PLANTILLA COMPLETA"):
            modo = "plantilla"
        elif linea.startswith("*") and modo == "destacados":
            jugador = linea.replace("*", "").strip()
            if jugador not in JUGADORES_DORADOS:
                JUGADORES_DORADOS.append(jugador)
        elif modo == "plantilla" and linea and linea[0].isdigit():
            partes = linea.split(".", 1)
            if len(partes) == 2:
                num = int(partes[0].strip())
                jugador = partes[1].strip()
                if num <= 20:
                    if jugador == "[Jugador por confirmar]":
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

class SignedTransaction(BaseModel):
    public_key: str = Field(..., description="Clave pública PEM de la billetera")
    payload: dict = Field(..., description="Diccionario con los datos de la transacción")
    signature: str = Field(..., description="Firma digital hexadecimal generada con la Clave Privada")

def verificar_firma_digital(public_key_pem: str, payload_dict: dict, signature_hex: str) -> str:
    try:
        payload_str = json.dumps(payload_dict, separators=(',', ':'), sort_keys=True).encode('utf-8')
        signature_bytes = bytes.fromhex(signature_hex)
        public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
        
        if not isinstance(public_key, rsa.RSAPublicKey):
             raise HTTPException(status_code=400, detail="FRAUDE: Formato de llave no soportado. Solo se admite RSA.")
             
        # Validar usando RSA PKCS#1 v1.5 y SHA256 (estándar ampliamente soportado en Web Crypto API)
        public_key.verify(
            signature_bytes,
            payload_str,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        # Derivar Wallet ID (dirección pública) del hash de la clave pública
        wallet_id = "0x" + hashlib.sha256(public_key_pem.encode('utf-8')).hexdigest()[:40]
        return wallet_id
    except InvalidSignature:
        raise HTTPException(status_code=403, detail="FRAUDE: La firma digital es inválida.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error criptográfico: {str(e)}")


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
    
    difficulty_prefix = get_current_difficulty_prefix()
    
    candidate_block = {
        "index": index,
        "previous_hash": previous_hash,
        "timestamp": int(time.time()),
        "transactions": pending_transactions.copy(),
        "difficulty_prefix": difficulty_prefix
    }
    
    # Registramos cuándo empezó el minado de este bloque para ajustar dificultad luego.
    mining_started_at[index] = time.time()

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

@app.post("/wallet/register_alias", summary="Registrar Alias de Billetera")
def register_alias(req: SignedTransaction):
    """Asocia un alias a una dirección de billetera pública (Wallet ID)."""
    wallet_id = verificar_firma_digital(req.public_key, req.payload, req.signature)
    alias = req.payload.get("alias")
    
    if not alias or len(alias) < 3:
        raise HTTPException(status_code=400, detail="Alias inválido. Debe tener al menos 3 caracteres.")
        
    # Verificar si el alias ya existe y pertenece a otro
    existing = db.client.get(f"alias:{alias.lower()}")
    if existing and existing != wallet_id:
        raise HTTPException(status_code=400, detail="El alias ya está en uso por otra billetera.")
        
    db.client.set(f"alias:{alias.lower()}", wallet_id)
    return {"status": "success", "message": f"Alias '{alias}' registrado correctamente para {wallet_id[:8]}..."}

@app.get("/wallet/resolve_alias", summary="Resolver Alias a Wallet ID")
def resolve_alias(alias: str):
    """Busca el Wallet ID asociado a un alias."""
    wallet_id = db.client.get(f"alias:{alias.lower()}")
    if not wallet_id:
        raise HTTPException(status_code=404, detail="Alias no encontrado.")
    return {"wallet_id": wallet_id}

@app.get("/album_template", summary="Obtener la plantilla base del álbum")
def get_album_template():
    """Devuelve la estructura completa del álbum (equipos y jugadores) para el Frontend."""
    return {
        "equipos": EQUIPOS_MUNDIAL,
        "jugadores_dorados": JUGADORES_DORADOS
    }

@app.get("/wallet/balance", summary="Consultar Saldo Público (Dashboard)")
def get_wallet_balance(address: str):
    """
    Endpoint de lectura pública. No requiere firma.
    Devuelve los PTS y figuritas de una dirección.
    """
    estado = db.get_wallet_state(address)
    return {"status": "success", "address": address, "estado": estado}

@app.post("/smart_contracts/mint_points", summary="Contrato de Emisión (MINT_POINTS)")
def mint_points_contract(req: SignedTransaction):
    wallet_id = verificar_firma_digital(req.public_key, req.payload, req.signature)
    
    nonce = req.payload.get("nonce")
    firma_hmac = req.payload.get("firma_hmac")
    
    if not nonce or not firma_hmac:
         raise HTTPException(status_code=400, detail="Faltan datos en el payload (nonce, firma_hmac).")

    if db.fue_qr_usado(nonce):
        raise HTTPException(status_code=400, detail="FRAUDE: Este QR físico ya fue escaneado y gastado anteriormente.")

    mensaje = f"{nonce}"
    firma_esperada = hmac.new(QR_SECRET_KEY.encode(), mensaje.encode(), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(firma_esperada, firma_hmac):
        raise HTTPException(status_code=403, detail="FRAUDE: Firma del QR inválida o falsificada matemáticamente.")

    db.marcar_qr_usado(nonce)
    tx = {
        "usuario_a": "Sistema_Sponsor",
        "usuario_b": wallet_id,
        "monto": 500,
        "metadata": {"concepto": f"Escaneo validado QR {nonce}"}
    }
    add_transaction_to_mempool(tx)
    return {"status": "success", "message": "Firma verificada exitosamente. 500 PTS asignados al mempool."}

@app.post("/smart_contracts/buy_pack", summary="Contrato de Apertura (BUY_PACK)")
def buy_pack_contract(req: SignedTransaction):
    wallet_id = verificar_firma_digital(req.public_key, req.payload, req.signature)
    
    estado_billetera = db.get_wallet_state(wallet_id)
    
    if estado_billetera["puntos_disponibles"] >= 500:
        tx_burn = {
            "usuario_a": wallet_id,
            "usuario_b": "Direccion_Nula_Tesoreria",
            "monto": 500,
            "metadata": {"concepto": "Pago por apertura de sobre virtual"}
        }
        add_transaction_to_mempool(tx_burn)
        
        cartas_reveladas = []
        for _ in range(5):
            fig_data = generar_figurita_rng()
            cartas_reveladas.append(fig_data)
            tx_mint = {
                "usuario_a": "Direccion_Nula_Tesoreria",
                "usuario_b": wallet_id,
                "monto": 1,
                "metadata": fig_data
            }
            add_transaction_to_mempool(tx_mint)
            
        return {"status": "success", "message": "Fondos verificados. Transacciones de sobre encoladas.", "cartas": cartas_reveladas}
    
    raise HTTPException(status_code=400, detail="Fondos insuficientes en la blockchain.")

@app.post("/smart_contracts/swap_stickers", summary="Contrato de Intercambio (SWAP_STICKERS)")
def swap_stickers_contract(req: SignedTransaction):
    wallet_id_a = verificar_firma_digital(req.public_key, req.payload, req.signature)
    
    usuario_b_input = req.payload.get("usuario_b") # Alias o Wallet B
    if not isinstance(usuario_b_input, str):
        raise HTTPException(status_code=400, detail="El destinatario debe ser un texto válido.")
        
    # Intento de resolución de alias
    usuario_b_redis = db.client.get(f"alias:{usuario_b_input.lower()}")
    if usuario_b_redis is not None:
        usuario_b = str(usuario_b_redis)
    else:
        usuario_b = usuario_b_input # Fallback: asumir que ingresó un Wallet ID directamente
    
    fig_x = req.payload.get("fig_x")
    fig_y = req.payload.get("fig_y")
    
    if not usuario_b or not fig_x or not fig_y:
        raise HTTPException(status_code=400, detail="Faltan datos en el payload del swap.")
        
    estado_a = db.get_wallet_state(wallet_id_a)
    estado_b = db.get_wallet_state(usuario_b)
    
    fig_x_data = next((f for f in estado_a["figuritas_poseidas"] if isinstance(f, dict) and f.get("fig_id") == fig_x), None)
    fig_y_data = next((f for f in estado_b["figuritas_poseidas"] if isinstance(f, dict) and f.get("fig_id") == fig_y), None)
    
    if not fig_x_data:
        raise HTTPException(status_code=400, detail=f"Inconsistencia: El emisor A no posee el token {fig_x}")
    if not fig_y_data:
        raise HTTPException(status_code=400, detail=f"Inconsistencia: El emisor B no posee el token {fig_y}")
        
    # 2. Validar regla de "Pegada vs Repetida"
    # Solo se puede intercambiar si el jugador está repetido (>1 copias en el inventario)
    count_jugador_a = sum(1 for f in estado_a["figuritas_poseidas"] if isinstance(f, dict) and f.get("jugador") == fig_x_data.get("jugador"))
    count_jugador_b = sum(1 for f in estado_b["figuritas_poseidas"] if isinstance(f, dict) and f.get("jugador") == fig_y_data.get("jugador"))
    
    if count_jugador_a <= 1:
        raise HTTPException(status_code=400, detail=f"Inconsistencia: El usuario A tiene su única copia de {fig_x_data.get('jugador')} pegada en el álbum. Solo puede intercambiar repetidas.")
    if count_jugador_b <= 1:
        raise HTTPException(status_code=400, detail=f"Inconsistencia: El usuario B tiene su única copia de {fig_y_data.get('jugador')} pegada en el álbum. Solo puede intercambiar repetidas.")
        
    tx_swap_1 = {
        "usuario_a": wallet_id_a, "usuario_b": usuario_b, "monto": 1,
        "metadata": {"fig_id": fig_x, "operacion": "SWAP_P2P"}
    }
    tx_swap_2 = {
        "usuario_a": usuario_b, "usuario_b": wallet_id_a, "monto": 1,
        "metadata": {"fig_id": fig_y, "operacion": "SWAP_P2P"}
    }
    
    add_transaction_to_mempool(tx_swap_1)
    add_transaction_to_mempool(tx_swap_2)
    return {"status": "success", "message": "Contrato P2P validado. Intercambio atómico encolado."}

@app.post("/smart_contracts/claim_reward", summary="Contrato de Recompensa (CLAIM_REWARD)")
def claim_reward_contract(req: SignedTransaction):
    wallet_id = verificar_firma_digital(req.public_key, req.payload, req.signature)
    
    tipo_desafio = req.payload.get("tipo_desafio")
    if not tipo_desafio:
         raise HTTPException(status_code=400, detail="Falta tipo_desafio en payload.")
         
    estado_billetera = db.get_wallet_state(wallet_id)
    figuritas_poseidas = estado_billetera["figuritas_poseidas"]
    
    if tipo_desafio == "LOGIN_DIARIO":
        if db.fue_desafio_reclamado(wallet_id, "LOGIN_DIARIO", es_diario=True):
            raise HTTPException(status_code=400, detail="FRAUDE: Ya reclamaste tu recompensa diaria de inicio de sesión hoy.")
            
        db.marcar_desafio(wallet_id, "LOGIN_DIARIO", es_diario=True)
        tx_premio = {"usuario_a": "Direccion_Nula_Tesoreria", "usuario_b": wallet_id, "monto": 50, "metadata": {"concepto": "Login Diario"}}
        add_transaction_to_mempool(tx_premio)
        return {"status": "success", "message": "50 PTS de login diario cobrados exitosamente."}
        
    elif tipo_desafio == "COLECCIONISTA_PRINCIPIANTE":
        if db.fue_desafio_reclamado(wallet_id, "COLECCIONISTA_PRINCIPIANTE", es_diario=False):
             raise HTTPException(status_code=400, detail="FRAUDE: Ya reclamaste este logro único.")
             
        jugadores_unicos = set()
        for fig in figuritas_poseidas:
            if isinstance(fig, dict) and "jugador" in fig:
                jugadores_unicos.add(fig["jugador"])
             
        if len(jugadores_unicos) >= 5:
            db.marcar_desafio(wallet_id, "COLECCIONISTA_PRINCIPIANTE", es_diario=False)
            tx_premio = {"usuario_a": "Direccion_Nula_Tesoreria", "usuario_b": wallet_id, "monto": 500, "metadata": {"concepto": "Logro: 5 Jugadores Únicos"}}
            add_transaction_to_mempool(tx_premio)
            return {"status": "success", "message": "Logro de Coleccionista Principiante completado! 500 PTS cobrados."}
            
    elif tipo_desafio == "FIGURITA_DORADA":
        if db.fue_desafio_reclamado(wallet_id, "FIGURITA_DORADA", es_diario=False):
             raise HTTPException(status_code=400, detail="FRAUDE: Ya reclamaste la recompensa por esta figurita dorada.")
             
        tiene_dorada = any(
            isinstance(fig, dict) and fig.get("jugador") in JUGADORES_DORADOS and fig.get("rareza") == "Legendaria"
            for fig in figuritas_poseidas
        )
             
        if tiene_dorada:
            db.marcar_desafio(wallet_id, "FIGURITA_DORADA", es_diario=False)
            tx_premio = {"usuario_a": "Direccion_Nula_Tesoreria", "usuario_b": wallet_id, "monto": 2000, "metadata": {"concepto": "Logro: Obtuviste un Jugador Dorado Legendario"}}
            add_transaction_to_mempool(tx_premio)
            return {"status": "success", "message": "Logro de Figurita Dorada completado! 2000 PTS cobrados."}

    elif tipo_desafio == "HOJA_COMPLETA":
        if db.fue_desafio_reclamado(wallet_id, "HOJA_COMPLETA", es_diario=False):
             raise HTTPException(status_code=400, detail="FRAUDE: Ya reclamaste el premio de hoja completa.")
             
        equipos_completos = False
        jugadores_por_equipo = {}
        
        for fig in figuritas_poseidas:
            if isinstance(fig, dict) and "equipo" in fig and "jugador" in fig:
                eq = fig["equipo"]
                if eq not in jugadores_por_equipo:
                    jugadores_por_equipo[eq] = set()
                jugadores_por_equipo[eq].add(fig["jugador"])
                
                if len(jugadores_por_equipo[eq]) >= 20:
                    equipos_completos = True
                    break
             
        if equipos_completos:
            db.marcar_desafio(wallet_id, "HOJA_COMPLETA", es_diario=False)
            tx_premio = {"usuario_a": "Direccion_Nula_Tesoreria", "usuario_b": wallet_id, "monto": 5000, "metadata": {"concepto": "Premio por Desafío: Selección Completada"}}
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
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
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
                        
                    # Medir tiempo y ajustar dificultad dinámica
                    block_index = candidate.get('index')
                    if block_index in mining_started_at:
                        tiempo_transcurrido = time.time() - mining_started_at[block_index]
                        ajustar_dificultad(tiempo_transcurrido)
                        del mining_started_at[block_index]
                        
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
