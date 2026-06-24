import pika
import json
import os
import sys

# Agregar la raíz del proyecto al sys.path para poder importar el módulo del Hit 7 (Pilar 1)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Hit7.hit7_cpu import buscar_en_rango

# Configuración y Variables de Entorno
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
HOSTNAME = os.environ.get("HOSTNAME", "worker-cpu-local")

def generar_cadena_base(block_data):
    """
    Transforma la estructura de datos del bloque en un string de texto plano y determinista.
    Es vital que todas las máquinas hagan el dump exacto para que el hash coincida.
    """
    tx_str = json.dumps(block_data["transactions"], sort_keys=True)
    return f"{block_data['index']}{block_data['previous_hash']}{block_data['timestamp']}{tx_str}"

def procesar_tarea(ch, method, properties, body):
    """Callback invocado por RabbitMQ cada vez que entra un chunk de minería"""
    tarea = json.loads(body)
    block_data = tarea["block_data"]
    start_nonce = tarea["start_nonce"]
    end_nonce = tarea["end_nonce"]

    difficulty_prefix = (
        tarea.get("difficulty_prefix")
        or block_data.get("difficulty_prefix")
        or "0000"
    )
    
    cadena_base = generar_cadena_base(block_data)
    print(f"[*] Tarea recibida (CPU) - Bloque #{block_data['index']} Rango: [{start_nonce} - {end_nonce}]")
    
    nonce_encontrado = None
    hash_encontrado = None
    
    try:
        # Reutilizamos la función de fuerza bruta del Pilar 1 (Hit 7)
        resultado = buscar_en_rango(cadena_base, difficulty_prefix, start_nonce, end_nonce)
        
        if resultado is not None:
            nonce_encontrado, _, hash_encontrado = resultado
            
        # Evaluar resultado matemático
        if nonce_encontrado is not None:
            print(f"Hash encontrado por la CPU: {hash_encontrado} (Nonce: {nonce_encontrado})")
            
            respuesta = {
                "block_data": block_data,
                "nonce": nonce_encontrado,
                "hash": hash_encontrado,
                "miner_id": HOSTNAME
            }
            
            ch.basic_publish(
                exchange='',
                routing_key='solved_blocks',
                body=json.dumps(respuesta),
                properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent)
            )
        else:
            print(f"[-] Rango de nonces agotado sin éxito en CPU.")
            
    except Exception as e:
        print(f"[ERROR CRÍTICO] Fallo en el minero CPU: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        return
        
    # ACK: Confirma a RabbitMQ que la tarea se completó
    ch.basic_ack(delivery_tag=method.delivery_tag)

def iniciar_worker():
    """Conecta con RabbitMQ e inicia el bucle infinito del Daemon minero (CPU)"""
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        params.heartbeat = 0
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        
        channel.queue_declare(queue='tareas_mineria', durable=True)
        channel.queue_declare(queue='solved_blocks', durable=True)
        
        # balanceo de carga real
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='tareas_mineria', on_message_callback=procesar_tarea)
        
        print(f" [*] Worker Minero Inicializado (Modo CPU Nativo)")
        print(f" [*] Esperando tareas en RabbitMQ '{RABBITMQ_URL}'...")
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[!] Minero CPU detenido manualmente por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] No se pudo establecer conexión con RabbitMQ: {e}")
        sys.exit(1)

if __name__ == "__main__":
    iniciar_worker()
