import hmac
import hashlib
import time
import os
import json
import qrcode

# Asegurate de que esto sea idéntico al QR_SECRET_KEY en nodo_coordinador.py
SECRET_KEY = os.environ.get("QR_SECRET_KEY", "sdypp2026")

def generar_qr_fisico():
    """
    Simula la impresión física de un QR en un paquete de figuritas.
    Genera el JSON exacto que el celular del usuario leería al escanearlo.
    """
    # 1. Generamos un Nonce único basado en el timestamp actual
    nonce = f"QR_{int(time.time() * 1000)}"
    
    # 2. Construimos el mensaje y lo firmamos con la llave del servidor
    mensaje = f"{nonce}"
    firma = hmac.new(SECRET_KEY.encode(), mensaje.encode(), hashlib.sha256).hexdigest()
    
    # 3. Este sería el string JSON que va impreso en código de barras bidimensional (QR)
    json_para_enviar = {
        "nonce": nonce,
        "firma_hmac": firma
    }
    
    print("\n==============================================")
    print("🎟️  QR FÍSICO GENERADO EXITOSAMENTE 🎟️")
    print("==============================================")
    print(f"JSON del QR (Mint Points):")
    print("----------------------------------------------")
    json_string = json.dumps(json_para_enviar, indent=4)
    print(json_string)
    print("----------------------------------------------")
    print("TIP: Si lo envías dos veces, el Oráculo lo rechazará por Fraude (Doble Gasto).")
    
    # 4. Generar la imagen física PNG
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(json_para_enviar))
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    output_path = os.path.join(os.path.dirname(__file__), "qr_fisico.png")
    img.save(output_path)
    print(f"\n✅ ¡Imagen del QR guardada exitosamente en:\n{output_path}\nPodés abrir esa foto y escanearla con la cámara desde tu app!")

if __name__ == "__main__":
    generar_qr_fisico()
