import React, { useState } from 'react';
import { signTransaction } from '../utils/cryptoUtils';
import { ArrowRightLeft, Search, User } from 'lucide-react';

export default function SwapP2P({ figuritas, privateKeyHex, publicKeyPem, onSuccess }) {
    const [aliasB, setAliasB] = useState('');
    const [figGive, setFigGive] = useState('');
    const [figReceive, setFigReceive] = useState('');
    const [status, setStatus] = useState({ type: '', message: '' });
    const [loading, setLoading] = useState(false);

    const baseUrl = import.meta.env.VITE_BACKEND_URL || '/proxy-api';

    const handleSwap = async (e) => {
        e.preventDefault();
        setLoading(true);
        setStatus({ type: 'info', message: 'Iniciando intercambio en la Blockchain...' });

        try {
            if (!aliasB || !figGive || !figReceive) {
                throw new Error("Por favor completa todos los campos.");
            }

            // Validar que realmente posee la figurita que quiere entregar
            const poseeFigurita = figuritas.find(f => f.fig_id === figGive || f.jugador === figGive);
            if (!poseeFigurita) {
                throw new Error("No posees la figurita que intentas entregar.");
            }

            const payload = {
                usuario_b: aliasB, // El backend ahora acepta el Alias directamente y lo resuelve
                fig_x: figGive,
                fig_y: figReceive
            };

            const signature = await signTransaction(privateKeyHex, payload);

            const response = await fetch(`${baseUrl}/smart_contracts/swap_stickers`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    public_key: publicKeyPem,
                    payload: payload,
                    signature: signature
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Error en el intercambio.");
            }

            setStatus({ type: 'success', message: '¡Intercambio realizado exitosamente!' });
            
            if (onSuccess) {
                setTimeout(() => {
                    onSuccess();
                }, 2000);
            }

        } catch (error) {
            setStatus({ type: 'error', message: error.message });
        }
        
        setLoading(false);
    };

    // Obtener figuritas únicas para el select (para no mostrar repetidas)
    const figuritasUnicas = [];
    const idsVistos = new Set();
    figuritas.forEach(f => {
        if (!idsVistos.has(f.jugador)) {
            idsVistos.add(f.jugador);
            figuritasUnicas.push(f);
        }
    });

    return (
        <div style={{ marginTop: '30px', maxWidth: '600px', margin: '30px auto 0' }}>
            <h2 style={{ fontSize: '2rem', marginBottom: '20px', color: 'var(--primary)', textAlign: 'center' }}>
                <ArrowRightLeft size={28} style={{ verticalAlign: 'middle', marginRight: '10px' }} />
                Mercado de Intercambio
            </h2>
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', marginBottom: '30px' }}>
                Cambiá figuritas repetidas con otros coleccionistas de forma directa y segura.
            </p>

            <form onSubmit={handleSwap} className="glass-panel animate-fade-in swap-form-container" style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                
                {/* Destinatario */}
                <div>
                    <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)' }}>
                        <User size={16} style={{ verticalAlign: 'middle', marginRight: '5px' }} />
                        Alias del Coleccionista
                    </label>
                    <input 
                        type="text" 
                        placeholder="Ej: Naiara, Ale, etc..."
                        value={aliasB}
                        onChange={(e) => setAliasB(e.target.value)}
                        className="glass-input"
                        style={{ width: '100%', padding: '12px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'white' }}
                    />
                </div>

                <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
                    {/* Figurita a Entregar */}
                    <div style={{ flex: 1 }}>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)' }}>Figurita que entregás</label>
                        <select 
                            value={figGive}
                            onChange={(e) => setFigGive(e.target.value)}
                            className="glass-input"
                            style={{ width: '100%', padding: '12px', borderRadius: '8px', background: 'rgba(0,0,0,0.5)', border: '1px solid var(--glass-border)', color: 'white' }}
                        >
                            <option value="">Seleccioná una...</option>
                            {figuritasUnicas.map((fig, idx) => (
                                <option key={idx} value={fig.fig_id}>{fig.jugador} ({fig.equipo})</option>
                            ))}
                        </select>
                    </div>

                    <ArrowRightLeft size={24} color="var(--primary)" style={{ marginTop: '25px' }} />

                    {/* Figurita a Recibir */}
                    <div style={{ flex: 1 }}>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)' }}>Figurita que querés</label>
                        <input 
                            type="text" 
                            placeholder="Ej: Messi, Mbappe..."
                            value={figReceive}
                            onChange={(e) => setFigReceive(e.target.value)}
                            className="glass-input"
                            style={{ width: '100%', padding: '12px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'white' }}
                        />
                    </div>
                </div>

                {status.message && (
                    <div style={{ 
                        padding: '10px', 
                        borderRadius: '8px', 
                        textAlign: 'center',
                        background: status.type === 'error' ? 'rgba(239, 68, 68, 0.2)' : status.type === 'success' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                        color: status.type === 'error' ? '#fca5a5' : status.type === 'success' ? '#6ee7b7' : '#93c5fd'
                    }}>
                        {status.message}
                    </div>
                )}

                <button 
                    type="submit" 
                    className="glass-button" 
                    disabled={loading}
                    style={{ marginTop: '10px', padding: '15px', fontSize: '1.1rem', background: 'var(--primary)' }}
                >
                    {loading ? 'Procesando Swap...' : 'Confirmar Intercambio P2P'}
                </button>
            </form>
        </div>
    );
}
