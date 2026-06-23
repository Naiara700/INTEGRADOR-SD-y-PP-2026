import React, { useState } from 'react';
import { signTransaction } from '../utils/cryptoUtils';
import { Gift, Star, Award, CheckCircle, BookOpen } from 'lucide-react';

export default function Album({ figuritas, privateKeyHex, publicKeyPem, onRewardClaimed }) {
    const [claiming, setClaiming] = useState(false);
    const [claimMessage, setClaimMessage] = useState('');
    const [template, setTemplate] = useState(null);
    const baseUrl = import.meta.env.VITE_BACKEND_URL || '/proxy-api';

    useEffect(() => {
        const fetchTemplate = async () => {
            try {
                const response = await fetch(`${baseUrl}/album_template`);
                if (response.ok) {
                    const data = await response.json();
                    setTemplate(data);
                }
            } catch (err) {
                console.error("Error cargando plantilla del álbum:", err);
            }
        };
        fetchTemplate();
    }, [baseUrl]);

    // Agrupar figuritas POSEÍDAS por equipo y jugador para búsqueda rápida
    const albumAgrupado = figuritas.reduce((acc, fig) => {
        const equipo = fig.equipo || 'Desconocido';
        if (!acc[equipo]) acc[equipo] = {};
        
        // Guardamos la mejor rareza poseída (por si tiene doradas y normales)
        if (!acc[equipo][fig.jugador] || fig.es_dorada) {
            acc[equipo][fig.jugador] = fig;
        }
        return acc;
    }, {});

    const equipos = template ? Object.keys(template.equipos).sort() : Object.keys(albumAgrupado).sort();

    // Obtener imagen de bandera (convirtiendo "Argentina" -> "argentina.png", "Arabia Saudita" -> "arabiaSaudita.png")
    const getFlagUrl = (equipo) => {
        if (!equipo) return '';
        // Convert to camelCase (e.g. "Arabia Saudita" -> "arabiaSaudita")
        const camel = equipo.split(' ').map((word, index) => {
            if (index === 0) return word.toLowerCase();
            return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
        }).join('');
        return `/assets/flags/${camel}.png`;
    };

    const claimReward = async (desafio_id) => {
        setClaiming(true);
        setClaimMessage('Firmando transacción de recompensa...');
        try {
            const payload = { desafio_id: desafio_id };
            const signature = await signTransaction(privateKeyHex, payload);

            const response = await fetch(`${baseUrl}/smart_contracts/claim_reward`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    public_key: publicKeyPem,
                    payload: payload,
                    signature: signature
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Error al reclamar la recompensa");

            setClaimMessage(data.message || '¡Recompensa Reclamada!');
            if (onRewardClaimed) onRewardClaimed();
            
            setTimeout(() => setClaimMessage(''), 3000);
        } catch (error) {
            setClaimMessage(error.message);
            setTimeout(() => setClaimMessage(''), 5000);
        }
        setClaiming(false);
    };

    return (
        <div style={{ marginTop: '30px' }}>
            <h2 style={{ fontSize: '2rem', marginBottom: '20px', color: 'var(--primary)', textAlign: 'center' }}>
                <BookOpen size={28} style={{ verticalAlign: 'middle', marginRight: '10px' }} />
                Mi Álbum Digital
            </h2>

            {/* Barra de Logros */}
            <div className="glass-panel" style={{ padding: '20px', marginBottom: '30px', display: 'flex', gap: '15px', flexWrap: 'wrap', justifyContent: 'center' }}>
                <h3 style={{ width: '100%', textAlign: 'center', marginBottom: '10px', fontSize: '1.2rem', color: 'var(--text-muted)' }}>
                    Reclamar Logros
                </h3>
                
                <button className="glass-button" onClick={() => claimReward('LOGIN_DIARIO')} disabled={claiming} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <Gift size={16} /> Login Diario (50 PTS)
                </button>
                <button className="glass-button" onClick={() => claimReward('COLECCIONISTA_PRINCIPIANTE')} disabled={claiming} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <Award size={16} /> +5 Figus (500 PTS)
                </button>
                <button className="glass-button" onClick={() => claimReward('FIGURITA_DORADA')} disabled={claiming} style={{ display: 'flex', alignItems: 'center', gap: '5px', borderColor: 'gold', color: 'gold' }}>
                    <Star size={16} /> 1 Dorada (2000 PTS)
                </button>
                <button className="glass-button" onClick={() => claimReward('HOJA_COMPLETA')} disabled={claiming} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <CheckCircle size={16} /> Plantilla (5000 PTS)
                </button>

                {claimMessage && (
                    <p style={{ width: '100%', textAlign: 'center', marginTop: '10px', color: 'var(--accent)', fontWeight: 'bold' }} className="animate-fade-in">
                        {claimMessage}
                    </p>
                )}
            </div>

            {/* Grilla de Equipos */}
            {!template ? (
                <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>Cargando plantilla del álbum...</p>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '40px' }}>
                    {equipos.map(equipo => {
                        const jugadoresEquipo = template.equipos[equipo] || [];
                        const figuritasPoseidas = albumAgrupado[equipo] || {};
                        const cantidadPoseidas = Object.keys(figuritasPoseidas).length;
                        
                        return (
                            <div key={equipo} className="glass-panel" style={{ padding: '20px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '20px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '10px' }}>
                                    <img 
                                        src={getFlagUrl(equipo)} 
                                        alt={`Bandera de ${equipo}`} 
                                        style={{ width: '50px', height: '35px', objectFit: 'cover', borderRadius: '4px', boxShadow: '0 2px 10px rgba(0,0,0,0.5)' }} 
                                        onError={(e) => { e.target.style.display = 'none'; }}
                                    />
                                    <h3 style={{ fontSize: '1.8rem', color: 'var(--text)', margin: 0, textTransform: 'uppercase', letterSpacing: '2px' }}>
                                        {equipo}
                                    </h3>
                                    <span style={{ marginLeft: 'auto', background: cantidadPoseidas === jugadoresEquipo.length ? 'rgba(16, 185, 129, 0.2)' : 'var(--glass-border)', color: cantidadPoseidas === jugadoresEquipo.length ? '#10b981' : 'white', padding: '5px 10px', borderRadius: '20px', fontSize: '0.9rem', fontWeight: cantidadPoseidas === jugadoresEquipo.length ? 'bold' : 'normal' }}>
                                        {cantidadPoseidas} / {jugadoresEquipo.length}
                                    </span>
                                </div>

                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '15px' }}>
                                    {jugadoresEquipo.map((jugador, idx) => {
                                        const fig = figuritasPoseidas[jugador]; // Check si la tiene
                                        const isOwned = !!fig;
                                        const isDorada = fig?.es_dorada;
                                        
                                        return (
                                            <div 
                                                key={idx} 
                                                className={`glass-panel ${isDorada ? 'holographic' : ''}`}
                                                style={{ 
                                                    padding: '15px 10px', 
                                                    textAlign: 'center', 
                                                    position: 'relative',
                                                    display: 'flex',
                                                    flexDirection: 'column',
                                                    justifyContent: 'center',
                                                    minHeight: '180px',
                                                    borderColor: isDorada ? 'gold' : isOwned ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                                                    background: isDorada ? 'linear-gradient(135deg, rgba(255,215,0,0.1), rgba(218,165,32,0.3))' : isOwned ? 'rgba(59, 130, 246, 0.1)' : 'rgba(0,0,0,0.3)',
                                                    filter: !isOwned ? 'grayscale(100%) opacity(0.5)' : 'none',
                                                    transition: 'all 0.3s ease'
                                                }}
                                            >
                                                {isDorada && (
                                                    <Star size={24} color="gold" fill="gold" style={{ position: 'absolute', top: '-10px', right: '-10px', filter: 'drop-shadow(0 0 10px gold)' }} />
                                                )}
                                                
                                                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '5px' }}>#{idx + 1}</p>
                                                <h4 style={{ fontSize: '1.1rem', margin: '0 0 10px 0', fontWeight: 'bold', color: isDorada ? 'gold' : isOwned ? 'var(--text)' : 'var(--text-muted)' }}>
                                                    {isOwned ? fig.jugador : '???'}
                                                </h4>
                                                
                                                {!isOwned && (
                                                    <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '-5px', marginBottom: '10px' }}>
                                                        {jugador}
                                                    </p>
                                                )}
                                                
                                                <img 
                                                    src={getFlagUrl(equipo)} 
                                                    alt="Bandera miniatura" 
                                                    style={{ width: '30px', margin: '0 auto', opacity: isOwned ? 0.8 : 0.3, borderRadius: '2px' }} 
                                                    onError={(e) => { e.target.style.display = 'none'; }}
                                                />
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
