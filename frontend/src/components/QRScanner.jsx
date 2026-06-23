import React, { useEffect, useState } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { signTransaction } from '../utils/cryptoUtils';
import { Camera, CheckCircle, XCircle } from 'lucide-react';

export default function QRScanner({ privateKeyHex, publicKeyPem, onSuccess }) {
    const [scanState, setScanState] = useState('scanning'); // 'scanning', 'processing', 'success', 'error'
    const [message, setMessage] = useState('');
    const [scannedData, setScannedData] = useState(null);

    const baseUrl = import.meta.env.VITE_BACKEND_URL || '/proxy-api';

    useEffect(() => {
        // Inicializar el escáner si estamos en modo escaneo
        if (scanState !== 'scanning') return;

        const scanner = new Html5QrcodeScanner(
            "reader",
            { fps: 10, qrbox: { width: 250, height: 250 } },
            /* verbose= */ false
        );

        scanner.render(onScanSuccess, onScanFailure);

        function onScanSuccess(decodedText) {
            scanner.clear(); // Detener la cámara al detectar un QR exitosamente
            handleQRData(decodedText);
        }

        function onScanFailure(error) {
            // Se ignora silenciosamente porque se dispara muchas veces por segundo buscando el QR
        }

        return () => {
            scanner.clear().catch(err => console.error("Error limpiando scanner:", err));
        };
    }, [scanState]);

    const handleQRData = async (jsonString) => {
        setScanState('processing');
        setMessage('Cifrando y validando código QR con el Nodo Coordinador...');

        try {
            // 1. Parsear el QR físico
            const qrData = JSON.parse(jsonString);
            
            if (!qrData.nonce || !qrData.firma_hmac) {
                throw new Error("El código QR no tiene el formato correcto de StickerChain.");
            }

            setScannedData(qrData);

            // 2. Armar el Payload y firmarlo con nuestra Billetera
            const payload = {
                nonce: qrData.nonce,
                firma_hmac: qrData.firma_hmac
            };
            
            const signature = await signTransaction(privateKeyHex, payload);

            const requestBody = {
                public_key: publicKeyPem,
                payload: payload,
                signature: signature
            };

            // 3. Consumir el contrato inteligente MINT_POINTS
            const response = await fetch(`${baseUrl}/smart_contracts/mint_points`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Error al procesar el código QR.");
            }

            setScanState('success');
            setMessage(data.message || '¡500 PTS reclamados exitosamente!');
            
            if (onSuccess) {
                setTimeout(() => {
                    onSuccess(); // Actualiza el dashboard después de unos segundos
                }, 2500);
            }

        } catch (error) {
            console.error("Error escaneando QR:", error);
            setScanState('error');
            setMessage(error.message || "Error desconocido al procesar el QR.");
        }
    };

    const resetScanner = () => {
        setScanState('scanning');
        setMessage('');
        setScannedData(null);
    };

    return (
        <div style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
            <h2 style={{ fontSize: '1.8rem', marginBottom: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
                <Camera color="var(--accent)" /> Escáner de Recompensas
            </h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: '30px' }}>
                Escaneá el código QR físico impreso en tu paquete promocional para canjear PTS en la Blockchain.
            </p>

            <div className="glass-panel" style={{ padding: '20px', minHeight: '350px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                
                {scanState === 'scanning' && (
                    <div id="reader" style={{ width: '100%', overflow: 'hidden', borderRadius: '12px' }}></div>
                )}

                {scanState === 'processing' && (
                    <div className="animate-fade-in">
                        <div className="loading-spinner" style={{ width: '50px', height: '50px', borderWidth: '5px', borderColor: 'var(--primary)', borderTopColor: 'transparent', margin: '0 auto 20px' }}></div>
                        <h3 style={{ color: 'var(--primary)' }}>Validando Transacción...</h3>
                        <p style={{ color: 'var(--text-muted)', marginTop: '10px' }}>{message}</p>
                    </div>
                )}

                {scanState === 'success' && (
                    <div className="animate-fade-in">
                        <CheckCircle size={80} color="#10b981" style={{ margin: '0 auto 20px' }} />
                        <h3 style={{ color: '#10b981', fontSize: '1.5rem', marginBottom: '10px' }}>¡Transacción Aprobada!</h3>
                        <p>{message}</p>
                        <button onClick={resetScanner} className="glass-button" style={{ marginTop: '30px' }}>
                            Escanear otro código
                        </button>
                    </div>
                )}

                {scanState === 'error' && (
                    <div className="animate-fade-in">
                        <XCircle size={80} color="#ef4444" style={{ margin: '0 auto 20px' }} />
                        <h3 style={{ color: '#ef4444', fontSize: '1.5rem', marginBottom: '10px' }}>Transacción Rechazada</h3>
                        <p style={{ color: '#fca5a5' }}>{message}</p>
                        <button onClick={resetScanner} className="glass-button" style={{ marginTop: '30px', background: 'rgba(239, 68, 68, 0.2)' }}>
                            Intentar de nuevo
                        </button>
                    </div>
                )}

            </div>

            {/* Estilos locales para inyectar en la librería html5-qrcode */}
            <style>{`
                #reader__scan_region {
                    background: transparent;
                }
                #reader__dashboard_section_csr button {
                    background-color: var(--primary);
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    margin: 5px;
                }
                #reader__dashboard_section_swaplink {
                    color: var(--accent);
                    text-decoration: none;
                }
            `}</style>
        </div>
    );
}
