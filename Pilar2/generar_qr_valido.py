import hmac
import hashlib
import time
import os

# Asegurate de que esto sea idéntico al QR_SECRET_KEY en nodo_coordinador.py
SECRET_KEY = os.environ.get("QR_SECRET_KEY", "sdypp2026")

def generar_qr_fisico(wallet_id: str):
    """
    Simula la impresión física de un QR en un paquete de figuritas.
    Genera el JSON exacto que el celular del usuario leería al escanearlo.
    """
    # 1. Generamos un Nonce único basado en el timestamp actual
    nonce = f"QR_{int(time.time() * 1000)}"
    
    # 2. Construimos el mensaje y lo firmamos con la llave del servidor
    mensaje = f"{nonce}:{wallet_id}"
    firma = hmac.new(SECRET_KEY.encode(), mensaje.encode(), hashlib.sha256).hexdigest()
    
    # 3. Este sería el string JSON que va impreso en código de barras bidimensional (QR)
    json_para_enviar = {
        "wallet_id": wallet_id,
        "nonce": nonce,
        "firma_hmac": firma
    }
    
    print("\n==============================================")
    print("🎟️  QR FÍSICO GENERADO EXITOSAMENTE 🎟️")
    print("==============================================")
    print(f"Envía este JSON exacto al endpoint /smart_contracts/mint_points:")
    print("----------------------------------------------")
    import json
    print(json.dumps(json_para_enviar, indent=4))
    print("----------------------------------------------")
    print("TIP: Si lo envías dos veces, el Oráculo lo rechazará por Fraude (Doble Gasto).")

if __name__ == "__main__":
    billetera_destino = input("Ingresa la wallet_id que va a escanear el QR (Ej: MiBilletera123): ")
    generar_qr_fisico(billetera_destino)
