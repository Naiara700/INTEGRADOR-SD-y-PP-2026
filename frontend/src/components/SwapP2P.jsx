import React, { useState, useEffect } from 'react';
import { signTransaction, deriveAddress } from '../utils/cryptoUtils';
import { ArrowRightLeft, User, Inbox, Plus, Check } from 'lucide-react';

export default function SwapP2P({ figuritas, privateKey, publicKeyPem, onSuccess }) {
    const [activeTab, setActiveTab] = useState('create'); // 'create' or 'inbox'
    const [aliasB, setAliasB] = useState('');
    const [figGive, setFigGive] = useState('');
    const [figReceive, setFigReceive] = useState('');
    const [status, setStatus] = useState({ type: '', message: '' });
    const [loading, setLoading] = useState(false);
    
    const [inventoryB, setInventoryB] = useState([]);
    const [loadingInventoryB, setLoadingInventoryB] = useState(false);
    
    const [pendingOffers, setPendingOffers] = useState([]);
    const [loadingOffers, setLoadingOffers] = useState(false);

    const baseUrl = import.meta.env.VITE_BACKEND_URL || '/proxy-api';

    // Obtener figuritas repetidas del Usuario A (emisor)
    const countMapA = {};
    figuritas.forEach(f => {
        countMapA[f.jugador] = (countMapA[f.jugador] || 0) + 1;
    });
    const repetidasA = [];
    const vistasA = new Set();
    figuritas.forEach(f => {
        if (countMapA[f.jugador] > 1 && !vistasA.has(f.jugador)) {
            vistasA.add(f.jugador);
            repetidasA.push(f);
        }
    });

    const fetchInventoryB = async () => {
        if (!aliasB) return;
        setLoadingInventoryB(true);
        setStatus({ type: '', message: '' });
        try {
            const resAlias = await fetch(`${baseUrl}/wallet/resolve_alias?alias=${aliasB}`);
            const aliasData = await resAlias.json();
            if (!resAlias.ok) throw new Error(`El usuario ${aliasB} no existe.`);
            
            const resWallet = await fetch(`${baseUrl}/wallet/balance?address=${aliasData.wallet_id}`);
            const walletData = await resWallet.json();
            
            if (walletData.status === 'success') {
                const figsB = walletData.estado.figuritas_poseidas;
                const countMapB = {};
                figsB.forEach(f => {
                    countMapB[f.jugador] = (countMapB[f.jugador] || 0) + 1;
                });
                const repetidasB = [];
                const vistasB = new Set();
                figsB.forEach(f => {
                    if (countMapB[f.jugador] > 1 && !vistasB.has(f.jugador)) {
                        vistasB.add(f.jugador);
                        repetidasB.push(f);
                    }
                });
                setInventoryB(repetidasB);
                if (repetidasB.length === 0) {
                    setStatus({ type: 'error', message: `El usuario ${aliasB} no tiene figuritas repetidas para intercambiar.` });
                }
            }
        } catch (err) {
            setStatus({ type: 'error', message: err.message });
            setInventoryB([]);
        }
        setLoadingInventoryB(false);
    };

    const fetchOffers = async () => {
        if (!publicKeyPem) return;
        setLoadingOffers(true);
        try {
            const myAddress = await deriveAddress(publicKeyPem);
            const res = await fetch(`${baseUrl}/smart_contracts/pending_offers?wallet_id=${myAddress}`);
            const data = await res.json();
            if (res.ok) {
                setPendingOffers(data.ofertas);
            }
        } catch (err) {
            console.error("Error fetching offers", err);
        }
        setLoadingOffers(false);
    };

    useEffect(() => {
        if (activeTab === 'inbox') {
            fetchOffers();
        }
    }, [activeTab]);

    const handleCreateOffer = async (e) => {
        e.preventDefault();
        setLoading(true);
        setStatus({ type: 'info', message: 'Creando oferta de intercambio...' });

        try {
            if (!aliasB || !figGive || !figReceive) {
                throw new Error("Por favor completa todos los campos.");
            }

            const payload = {
                usuario_b: aliasB,
                fig_x: figGive,
                fig_y: figReceive,
                emisor_alias: "Tú" 
            };

            const signature = await signTransaction(privateKey, payload);

            const response = await fetch(`${baseUrl}/smart_contracts/create_swap_offer`, {
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
                throw new Error(data.detail || "Error al crear la oferta.");
            }

            setStatus({ type: 'success', message: '¡Oferta enviada exitosamente!' });
            setFigGive('');
            setFigReceive('');
            
        } catch (error) {
            setStatus({ type: 'error', message: error.message });
        }
        
        setLoading(false);
    };

    const handleAcceptOffer = async (offerId) => {
        setStatus({ type: 'info', message: 'Aceptando oferta...' });
        setLoading(true);
        try {
            const payload = { offer_id: offerId };
            const signature = await signTransaction(privateKey, payload);

            const response = await fetch(`${baseUrl}/smart_contracts/accept_swap_offer`, {
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
                throw new Error(data.detail || "Error al aceptar la oferta.");
            }

            setStatus({ type: 'success', message: '¡Intercambio realizado exitosamente!' });
            fetchOffers();
            
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

    return (
        <div style={{ marginTop: '30px', maxWidth: '600px', margin: '30px auto 0' }}>
            <h2 style={{ fontSize: '2rem', marginBottom: '20px', color: 'var(--primary)', textAlign: 'center' }}>
                <ArrowRightLeft size={28} style={{ verticalAlign: 'middle', marginRight: '10px' }} />
                Mercado de Intercambio P2P
            </h2>
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', marginBottom: '30px' }}>
                Cambiá figuritas repetidas con otros coleccionistas de forma directa y segura.
            </p>

            <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', justifyContent: 'center' }}>
                <button 
                    onClick={() => {setActiveTab('create'); setStatus({type:'', message:''});}}
                    className="glass-button"
                    style={{ background: activeTab === 'create' ? 'var(--primary)' : 'rgba(255,255,255,0.05)', padding: '10px 20px', borderRadius: '20px' }}
                >
                    <Plus size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />
                    Crear Oferta
                </button>
                <button 
                    onClick={() => {setActiveTab('inbox'); setStatus({type:'', message:''});}}
                    className="glass-button"
                    style={{ background: activeTab === 'inbox' ? 'var(--primary)' : 'rgba(255,255,255,0.05)', padding: '10px 20px', borderRadius: '20px', position: 'relative' }}
                >
                    <Inbox size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />
                    Buzón de Ofertas
                    {pendingOffers.length > 0 && (
                        <span style={{ position: 'absolute', top: '-5px', right: '-5px', background: 'red', color: 'white', borderRadius: '50%', padding: '2px 6px', fontSize: '0.8rem' }}>
                            {pendingOffers.length}
                        </span>
                    )}
                </button>
            </div>

            {status.message && (
                <div style={{ 
                    padding: '10px', 
                    borderRadius: '8px', 
                    textAlign: 'center',
                    marginBottom: '20px',
                    background: status.type === 'error' ? 'rgba(239, 68, 68, 0.2)' : status.type === 'success' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                    color: status.type === 'error' ? '#fca5a5' : status.type === 'success' ? '#6ee7b7' : '#93c5fd'
                }}>
                    {status.message}
                </div>
            )}

            {activeTab === 'create' && (
                <form onSubmit={handleCreateOffer} className="glass-panel animate-fade-in swap-form-container" style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    
                    {/* Destinatario */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)' }}>
                            <User size={16} style={{ verticalAlign: 'middle', marginRight: '5px' }} />
                            Alias del Coleccionista
                        </label>
                        <div style={{ display: 'flex', gap: '10px' }}>
                            <input 
                                type="text" 
                                placeholder="Ej: Naiara, Ale, etc..."
                                value={aliasB}
                                onChange={(e) => setAliasB(e.target.value)}
                                className="glass-input"
                                style={{ flex: 1, padding: '12px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'white' }}
                            />
                            <button 
                                type="button" 
                                onClick={fetchInventoryB} 
                                className="glass-button" 
                                disabled={loadingInventoryB || !aliasB}
                                style={{ padding: '0 20px', background: 'rgba(255,255,255,0.1)' }}
                            >
                                Buscar Repetidas
                            </button>
                        </div>
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
                                {repetidasA.map((fig, idx) => (
                                    <option key={idx} value={fig.fig_id}>{fig.jugador} ({fig.equipo})</option>
                                ))}
                            </select>
                            {repetidasA.length === 0 && (
                                <small style={{ color: '#fca5a5' }}>No tienes figuritas repetidas.</small>
                            )}
                        </div>

                        <ArrowRightLeft size={24} color="var(--primary)" style={{ marginTop: '25px' }} />

                        {/* Figurita a Recibir */}
                        <div style={{ flex: 1 }}>
                            <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-muted)' }}>Figurita que querés</label>
                            <select 
                                value={figReceive}
                                onChange={(e) => setFigReceive(e.target.value)}
                                className="glass-input"
                                disabled={inventoryB.length === 0}
                                style={{ width: '100%', padding: '12px', borderRadius: '8px', background: 'rgba(0,0,0,0.5)', border: '1px solid var(--glass-border)', color: 'white', opacity: inventoryB.length === 0 ? 0.5 : 1 }}
                            >
                                <option value="">Seleccioná una...</option>
                                {inventoryB.map((fig, idx) => (
                                    <option key={idx} value={fig.fig_id}>{fig.jugador} ({fig.equipo})</option>
                                ))}
                            </select>
                            {inventoryB.length === 0 && (
                                <small style={{ color: 'var(--text-muted)' }}>Busca al usuario primero.</small>
                            )}
                        </div>
                    </div>

                    <button 
                        type="submit" 
                        className="glass-button" 
                        disabled={loading || !figGive || !figReceive}
                        style={{ marginTop: '10px', padding: '15px', fontSize: '1.1rem', background: 'var(--primary)' }}
                    >
                        {loading ? 'Enviando Oferta...' : 'Enviar Oferta P2P'}
                    </button>
                </form>
            )}

            {activeTab === 'inbox' && (
                <div className="glass-panel animate-fade-in" style={{ padding: '20px', minHeight: '300px' }}>
                    <h3 style={{ marginTop: 0, color: 'var(--text)' }}>Ofertas Recibidas</h3>
                    
                    {loadingOffers ? (
                        <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>Cargando ofertas...</p>
                    ) : pendingOffers.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
                            <Inbox size={48} style={{ opacity: 0.5, marginBottom: '10px' }} />
                            <p>No tienes ofertas de intercambio pendientes.</p>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                            {pendingOffers.map((offer, idx) => (
                                <div key={idx} style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '12px', padding: '15px', border: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <div>
                                        <p style={{ margin: '0 0 10px 0', fontSize: '1.1rem' }}>
                                            <strong style={{ color: 'var(--primary)' }}>{offer.emisor_alias || 'Alguien'}</strong> te ofrece a:
                                        </p>
                                        <div style={{ display: 'flex', gap: '15px', alignItems: 'center', background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '8px' }}>
                                            <div style={{ textAlign: 'center' }}>
                                                <small style={{ color: 'var(--text-muted)' }}>Recibes</small>
                                                <div style={{ fontWeight: 'bold', color: '#6ee7b7' }}>{offer.fig_ofrecida.jugador}</div>
                                            </div>
                                            <ArrowRightLeft size={16} />
                                            <div style={{ textAlign: 'center' }}>
                                                <small style={{ color: 'var(--text-muted)' }}>Entregas</small>
                                                <div style={{ fontWeight: 'bold', color: '#fca5a5' }}>{offer.fig_solicitada.jugador}</div>
                                            </div>
                                        </div>
                                    </div>
                                    <button 
                                        className="glass-button" 
                                        onClick={() => handleAcceptOffer(offer.offer_id)}
                                        disabled={loading}
                                        style={{ background: '#10b981', padding: '10px 20px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '5px' }}
                                    >
                                        <Check size={18} />
                                        Aceptar
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
