from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pika
import json
import os

app = FastAPI(title="Pool de Transacciones (Gestor Split)", description="Fragmentador y Distribuidor de Carga hacia RabbitMQ")

# Configuración
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
# Dividimos el espacio de 32-bits (4.2 billones) en partes.
# 100 partes por defecto = 42.9 millones de nonces por worker.
NUM_CHUNKS = int(os.environ.get("NUM_CHUNKS", 100))

class BlockCandidate(BaseModel):
    index: int
    previous_hash: str
    timestamp: float
    transactions: list
    difficulty: str

def get_rabbitmq_channel():
    """Establece conexión con RabbitMQ y asegura que la cola exista."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    # durable=True para no perder tareas si RabbitMQ se reinicia
    channel.queue_declare(queue='tareas_mineria', durable=True)
    return connection, channel

@app.post("/mine")
def mine_block(block: BlockCandidate):
    """
    Recibe un bloque candidato del Nodo Coordinador.
    Fragmenta el inmenso espacio de búsqueda de Nonces (0 a 4,294,967,295)
    y encola estos fragmentos (chunks) en RabbitMQ para que los workers CUDA compitan.
    """
    MAX_NONCE = 4294967295 # Máximo valor para un entero sin signo de 32 bits
    chunk_size = MAX_NONCE // NUM_CHUNKS
    
    try:
        connection, channel = get_rabbitmq_channel()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo crítico: No se pudo conectar a RabbitMQ: {str(e)}")

    tareas_enviadas = 0
    
    # Lógica "Split": Dividir el trabajo en rangos fijos
    for i in range(NUM_CHUNKS):
        start_nonce = i * chunk_size
        # Asegurar que el último chunk llegue exactamente hasta el final
        end_nonce = (i + 1) * chunk_size - 1 if i < NUM_CHUNKS - 1 else MAX_NONCE
        
        tarea = {
            "block_data": block.model_dump(),
            "start_nonce": start_nonce,
            "end_nonce": end_nonce
        }
        
        # Publicar tarea en la cola de RabbitMQ
        channel.basic_publish(
            exchange='',
            routing_key='tareas_mineria',
            body=json.dumps(tarea),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent
            )
        )
        tareas_enviadas += 1

    connection.close()
    
    return {
        "status": "success", 
        "message": f"Bloque {block.index} fragmentado exitosamente en {tareas_enviadas} sub-tareas.",
        "queue": "tareas_mineria",
        "chunks": NUM_CHUNKS
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
