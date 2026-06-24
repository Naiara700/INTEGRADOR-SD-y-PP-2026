"""
Módulo de Persistencia y Estado: db_blockchain.py
Este componente gestiona la capa de persistencia de StickerChain utilizando Redis.
Actúa como un Ledger (Libro Mayor) distribuido y en memoria, proporcionando:
1. Almacenamiento seguro e inmutable (simulado) de los bloques minados.
2. Indexación rápida para consultas por índice de bloque o por hash criptográfico.
3. Funcionalidad analítica (UTXO-like) para recorrer la cadena temporalmente 
   y derivar el balance exacto de Puntos y Figuritas de cualquier billetera.
"""

import os
import json
import time
import redis
from typing import Dict, List, Any, Optional, cast

class DBBlockchain:
    def __init__(self):
        """
        Inicializa la conexión con Redis utilizando variables de entorno para
        facilitar el despliegue en contenedores (Docker/Kubernetes).
        Si la base de datos está vacía, aprovisiona automáticamente el Bloque Génesis.
        """
        redis_host = os.environ.get("REDIS_HOST", "localhost")
        redis_port = int(os.environ.get("REDIS_PORT", 6379))
        
        # Conexión sincrónica a Redis con decode_responses para facilitar el manejo de strings
        self.client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # Verificación del estado inicial de la cadena
        if not self.client.exists("blockchain:state:height"):
            self._create_genesis_block()

    def _create_genesis_block(self):
        """
        Genera y persiste el Bloque Génesis. Este es el bloque fundamental (index 0)
        que inicializa matemáticamente la cadena criptográfica.
        """
        genesis_block = {
            "index": 0,
            "previous_hash": "0" * 32, # El hash previo es una constante de ceros
            "nonce": 0,
            "timestamp": int(time.time()),
            "transactions": json.dumps([]),
            "block_hash": "genesis_block_hash_placeholder"
        }
        self.save_block(genesis_block)

    def get_latest_block(self) -> Optional[Dict[str, Any]]:
        """
        Recupera el último bloque válido añadido a la cadena.
        Crucial para que el Nodo Coordinador construya el "Bloque Candidato" 
        referenciando correctamente el 'previous_hash'.
        """
        height_str = self.client.get("blockchain:state:height")
        if not height_str:
            return None
            
        height = int(height_str)
        # Recupera el hash map completo del bloque desde Redis
        bloque_redis = self.client.hgetall(f"block:{height}")
        return cast(Dict[str, Any], bloque_redis) if bloque_redis else None

    def save_block(self, block_data: Dict[str, Any]) -> bool:
        """
        Persiste un nuevo bloque en Redis de manera atómica (mediante transacciones lógicas).
        
        Estructura en Redis:
        - block:{index} -> Hash map con los datos del bloque.
        - block_hash:{hash} -> Llave/Valor apuntando al índice para búsquedas rápidas (O(1)).
        - blockchain:state:height -> Entero indicando el tope de la cadena.
        """
        try:
            index = block_data.get("index")
            block_hash = block_data.get("block_hash")
            
            if index is None or block_hash is None:
                print("DB Error: Bloque inválido (falta index o block_hash).")
                return False
            
            # Verificar si ya existe un bloque consolidado con este índice
            # El Bloque Génesis (index 0) es la única excepción permitida
            if int(index) > 0 and self.client.exists(f"block:{index}"):
                print(f"DB: Bloque {index} ya existe. Rechazando duplicado (First-Writer-Wins).")
                return False
            
            pipeline = self.client.pipeline()
            
            # Guardar atributos del bloque (hashmap en Redis)
            mapping_data = {k: str(v) for k, v in block_data.items()}
            pipeline.hset(f"block:{index}", mapping=cast(Any, mapping_data))
            
            # Actualizar punteros de estado e índices de búsqueda
            pipeline.set("blockchain:state:height", str(index))
            pipeline.set(f"block_hash:{block_hash}", str(index))
            
            pipeline.execute()
            
            return True
        except Exception as e:
            print(f"Error guardando bloque {block_data.get('index')}: {e}")
            return False

    def get_wallet_state(self, wallet_id: str) -> Dict[str, Any]:
        """
        Realiza un análisis completo del historial de la cadena (Time-Travel)
        para reconstruir el estado actual (balance) de un usuario específico.
        
        Procesa el concepto de transacciones, determinando si es un 
        movimiento de "Puntos" o transferencias de "Figuritas" (NFT-like).
        """
        height_str = self.client.get("blockchain:state:height")
        height = int(height_str) if height_str else -1
        
        balance_pts = 0
        inventario_figuritas = []
        
        # Recorrido temporal O(N) donde N es el tamaño de la blockchain
        for i in range(height + 1):
            block = self.client.hgetall(f"block:{i}")
            if not block:
                continue
            
            # Deserializar transacciones del bloque
            transactions = json.loads(block.get("transactions", "[]"))
            
            for tx in transactions:
                sender = tx.get("usuario_a")
                receiver = tx.get("usuario_b")
                monto = int(tx.get("monto", tx.get("puntos", 0)))
                metadata = tx.get("metadata", {})
                
                # Reglas de negocio analíticas
                is_points = "concepto" in metadata
                is_sticker = "fig_id" in metadata
                
                # Computar débitos y créditos de Puntos
                if is_points:
                    if sender == wallet_id:
                        balance_pts -= monto
                    if receiver == wallet_id:
                        balance_pts += monto
                
                # Computar transferencias de propiedad de Figuritas
                if is_sticker:
                    fig_id = metadata.get("fig_id")
                    
                    if sender == wallet_id:
                        # Remover la figurita de forma segura buscando por fig_id
                        for idx, fig in enumerate(inventario_figuritas):
                            if isinstance(fig, dict) and fig.get("fig_id") == fig_id:
                                inventario_figuritas.pop(idx)
                                break
                            elif isinstance(fig, str) and fig == fig_id:
                                inventario_figuritas.pop(idx)
                                break
                                
                    if receiver == wallet_id:
                        # Guardamos la metadata completa para poder analizar rareza y equipo
                        inventario_figuritas.append(metadata)
                        
        return {
            "puntos_disponibles": balance_pts,
            "figuritas_poseidas": inventario_figuritas
        }

    # ==============================================================================
    # Funciones Reales de Control de Estado (Oráculos y Prevención de Fraude)
    # ==============================================================================

    def fue_desafio_reclamado(self, wallet_id: str, desafio: str, es_diario: bool = True) -> bool:
        """Verifica en Redis si el usuario ya cobró este desafío para evitar abusos."""
        fecha = time.strftime('%Y-%m-%d') if es_diario else "unico"
        key = f"desafio_completado:{wallet_id}:{desafio}:{fecha}"
        return self.client.exists(key) > 0

    def marcar_desafio(self, wallet_id: str, desafio: str, es_diario: bool = True):
        """Registra el cobro en Redis. Si es diario, la llave expira a las 24 hs."""
        fecha = time.strftime('%Y-%m-%d') if es_diario else "unico"
        key = f"desafio_completado:{wallet_id}:{desafio}:{fecha}"
        self.client.set(key, "1")
        if es_diario:
            self.client.expire(key, 86400) # Expira en 24 horas exactas

    def fue_qr_usado(self, nonce: str) -> bool:
        """Evita el doble gasto si dos personas escanean el mismo sticker físico."""
        return self.client.exists(f"qr_usado:{nonce}") > 0

    def marcar_qr_usado(self, nonce: str):
        self.client.set(f"qr_usado:{nonce}", "1")
