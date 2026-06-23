import pika
import json
import os
import subprocess

# Configuración y Variables de Entorno
RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
# En entorno local/Windows será .exe, en Kubernetes (Linux) será el binario sin extensión.
# Por defecto apuntamos a la carpeta Hit7 como definió el compañero
CUDA_BINARY = os.environ.get("CUDA_BINARY", os.path.join("..", "Hit7", "hit7_cuda.exe"))

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

    # El prefijo puede venir en la tarea o dentro del bloque candidato.
    # Dejamos fallback a "0000" para compatibilidad.
    difficulty_prefix = (
        tarea.get("difficulty_prefix")
        or block_data.get("difficulty_prefix")
        or "0000"
    )
    
    cadena_base = generar_cadena_base(block_data)
    print(f"[*] Tarea recibida - Bloque #{block_data['index']} Rango: [{start_nonce} - {end_nonce}]")
    
    try:
        # Llamada al binario de C++/CUDA que exprime la placa de video
        # Argumentos posicionales asumidos para hit7_cuda: <cadena_base> <prefijo> <inicio> <fin>
        print(f"    Ejecutando proceso CUDA en la GPU...")
        resultado = subprocess.run(
            [CUDA_BINARY, cadena_base, difficulty_prefix, str(start_nonce), str(end_nonce)],
            capture_output=True,
            text=True
        )
        
        salida_stdout = resultado.stdout.strip()
        salida_stderr = resultado.stderr.strip()

        if resultado.returncode != 0:
            print("[ERROR CUDA] El binario devolvió error.")
            print(salida_stderr)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return

        nonce_encontrado = None
        hash_encontrado = None
        
        # Analizamos la salida de la consola del programa C++
        # Suponemos un formato de salida exitosa estilo "12345:0000abcdef..."
        for linea in salida_stdout.splitlines():
            linea = linea.strip()
            # if "0000" in linea and ":" in linea:
            #     partes = linea.strip()
            #     if len(partes) == 2 and partes[0].strip().isdigit():
            #         nonce_encontrado = int(partes[0].strip())
            #         hash_encontrado = partes[1].strip()
            #         break

            if linea == "NO_ENCONTRADO":
                continue

            if ":" not in linea:
                continue

            nonce_txt, hash_txt = linea.split(":", 1)
            nonce_txt = nonce_txt.strip()
            hash_txt = hash_txt.strip().lower()

            if nonce_txt.isdigit() and len(hash_txt) == 32:
                if hash_txt.startswith(difficulty_prefix):
                    nonce_encontrado = int(nonce_txt)
                    hash_encontrado = hash_txt
                    break
        
        # Evaluar resultado matemático
        if nonce_encontrado is not None:
            print(f"Hash encontrado por la GPU: {hash_encontrado} (Nonce: {nonce_encontrado})")
            
            # Avisamos a la red que el bloque fue resuelto para que lo asienten en la DB
            respuesta = {
                "block_data": block_data,
                "nonce": nonce_encontrado,
                "hash": hash_encontrado,
                "miner_id": os.environ.get("HOSTNAME", "worker-gpu-local")
            }
            
            ch.basic_publish(
                exchange='',
                routing_key='solved_blocks',
                body=json.dumps(respuesta),
                properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent)
            )
        else:
            print(f"[-] Rango de nonces agotado sin éxito.")
            
    except FileNotFoundError:
        print(f"[ERROR CRITICO] Binario CUDA '{CUDA_BINARY}' no encontrado.")
        print("Devolviendo tarea a la cola general para que otro nodo la procese...")
        # NACK: Rechaza el mensaje y lo devuelve a la cola porque hubo un error de sistema
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        return
    except Exception as e:
        print(f"[ERROR DESCONOCIDO] Fallo al ejecutar binario CUDA: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        return
        
    # ACK: Confirma a RabbitMQ que la tarea se completó (sin importar si hubo o no hit)
    # y borra el mensaje de la cola
    ch.basic_ack(delivery_tag=method.delivery_tag)

def iniciar_worker():
    """Conecta con RabbitMQ e inicia el bucle infinito del Daemon minero"""
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        
        # Declaramos ambas colas (por si no las creó el Gestor Split todavía)
        channel.queue_declare(queue='tareas_mineria', durable=True)
        channel.queue_declare(queue='solved_blocks', durable=True)
        
        # prefetch_count=1 asegura balanceo de carga real (solo toma 1 tarea a la vez por Worker)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='tareas_mineria', on_message_callback=procesar_tarea)
        
        print(f" [*] Worker Minero Inicializado (Modo GPU)")
        print(f" [*] Esperando tareas en RabbitMQ '{RABBITMQ_URL}'...")
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[!] Minero detenido manualmente por el usuario.")
    except Exception as e:
        print(f"\n[ERROR] No se pudo establecer conexión con RabbitMQ: {e}")

if __name__ == "__main__":
    iniciar_worker()
