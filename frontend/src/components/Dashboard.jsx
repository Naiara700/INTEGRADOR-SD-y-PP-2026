import React, { useState, useEffect } from 'react';
import { deriveAddress } from '../utils/cryptoUtils';
import { Coins, BookOpen, PackageOpen, QrCode, RefreshCcw, ArrowRightLeft, ArrowLeft } from 'lucide-react';
import PackOpener from './PackOpener';
import QRScanner from './QRScanner';
import Album from './Album';
import SwapP2P from './SwapP2P';

export default function Dashboard({ wallet }) {
    const [balanceData, setBalanceData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [address, setAddress] = useState('');
    const [activeView, setActiveView] = useState('home'); // 'home', 'pack_opener'

    const fetchBalance = async () => {
        setLoading(true);
        setError('');
        try {
            const derivedAddr = await deriveAddress(wallet.publicKeyPem);
            setAddress(derivedAddr);

            const baseUrl = import.meta.env.VITE_BACKEND_URL || '/proxy-api';
            const response = await fetch(`${baseUrl}/wallet/balance?address=${derivedAddr}`);
            
            if (!response.ok) {
                throw new Error("No se pudo conectar con el Nodo Coordinador.");
            }
            
            const data = await response.json();
            setBalanceData(data.estado);
        } catch (err) {
            setError(err.message);
        }
        setLoading(false);
    };

    const registerAlias = async () => {
        try {
            const baseUrl = import.meta.env.VITE_BACKEND_URL || '/proxy-api';
            const { signTransaction } = await import('../utils/cryptoUtils');
            
            const payload = { alias: wallet.alias };
            const signature = await signTransaction(wallet.privateKey, payload);
            
            await fetch(`${baseUrl}/wallet/register_alias`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    public_key: wallet.publicKeyPem,
                    payload: payload,
                    signature: signature
                })
            });
        } catch (err) {
            console.error("Error registrando alias:", err);
        }
    };

    useEffect(() => {
        fetchBalance();
        registerAlias();
    }, [wallet]);

    return (
        <div className="animate-fade-in" style={{ padding: '20px', maxWidth: '900px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '40px', position: 'relative' }}>
                {activeView !== 'home' && (
                    <button 
                        onClick={() => setActiveView('home')}
                        className="glass-button"
                        style={{ position: 'absolute', left: 0, top: '50%', transform: 'translateY(-50%)', padding: '10px 15px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                    >
                        <ArrowLeft size={24} /> Volver
                    </button>
                )}
                <h1 style={{ fontSize: '2.5rem', marginBottom: '10px' }}>
                    Bienvenido, <span style={{ color: 'var(--primary)' }}>{wallet.alias}</span>
                </h1>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', wordBreak: 'break-all' }}>
                    <strong>Wallet ID:</strong> {address || 'Derivando...'}
                </p>
            </div>

            {/* Tarjeta de Saldo Principal */}
            <div className="glass-panel" style={{ padding: '30px', textAlign: 'center', marginBottom: '40px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <h2 style={{ fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Coins color="var(--accent)" /> Mis Fondos
                    </h2>
                    <button onClick={fetchBalance} className="glass-button" style={{ padding: '8px', background: 'transparent' }} title="Actualizar Saldo">
                        <RefreshCcw size={20} className={loading ? 'animate-spin' : ''} />
                    </button>
                </div>
                
                {loading && !balanceData ? (
                    <p style={{ color: 'var(--text-muted)' }}>Consultando la Blockchain...</p>
                ) : error ? (
                    <p style={{ color: 'var(--danger)' }}>{error}</p>
                ) : (
                    <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center' }}>
                        <div>
                            <p style={{ fontSize: '1rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Saldo Total</p>
                            <p style={{ fontSize: '3rem', fontWeight: '900', color: 'var(--accent)', textShadow: '0 0 15px rgba(245, 158, 11, 0.4)' }}>
                                {balanceData.puntos_disponibles} PTS
                            </p>
                        </div>
                        <div style={{ borderLeft: '1px solid var(--glass-border)', paddingLeft: '30px' }}>
                            <p style={{ fontSize: '1rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Figuritas Coleccionadas</p>
                            <p style={{ fontSize: '2.5rem', fontWeight: '700' }}>
                                {balanceData.figuritas_poseidas.length}
                            </p>
                        </div>
                    </div>
                )}


            </div>

            {/* Vista Dinámica */}
            {activeView === 'home' ? (
                <>
                    <h3 style={{ marginBottom: '20px', fontSize: '1.2rem', color: 'var(--text-muted)' }} className="dashboard-action-title">Acciones Disponibles</h3>
                    <div className="dashboard-action-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '20px' }}>
                        <button className="glass-panel action-card" onClick={() => setActiveView('album')}>
                            <BookOpen size={40} color="#3b82f6" />
                            <h4>Mi Álbum</h4>
                            <p>Pega tus figuritas y completa selecciones.</p>
                        </button>

                        <button className="glass-panel action-card" onClick={() => setActiveView('pack_opener')}>
                            <PackageOpen size={40} color="#a855f7" />
                            <h4>Abrir Sobres</h4>
                            <p>Compra sobres holográficos por 500 PTS.</p>
                        </button>

                        <button className="glass-panel action-card" onClick={() => setActiveView('qr_scanner')}>
                            <QrCode size={40} color="#10b981" />
                            <h4>Escanear Código</h4>
                            <p>Reclama puntos de productos físicos.</p>
                        </button>

                        <button className="glass-panel action-card" onClick={() => setActiveView('swap')}>
                            <ArrowRightLeft size={40} color="#f59e0b" />
                            <h4>Intercambio</h4>
                            <p>Swap P2P con otros coleccionistas.</p>
                        </button>
                    </div>
                </>
            ) : activeView === 'pack_opener' ? (
                <PackOpener 
                    privateKey={wallet.privateKey} 
                    publicKeyPem={wallet.publicKeyPem} 
                    currentPts={balanceData?.puntos_disponibles || 0}
                    onPackOpened={fetchBalance}
                />
            ) : activeView === 'qr_scanner' ? (
                <QRScanner 
                    privateKey={wallet.privateKey} 
                    publicKeyPem={wallet.publicKeyPem}
                    onSuccess={() => {
                        fetchBalance();
                    }}
                />
            ) : activeView === 'album' ? (
                <Album 
                    figuritas={balanceData?.figuritas_poseidas || []}
                    privateKey={wallet.privateKey}
                    publicKeyPem={wallet.publicKeyPem}
                    onRewardClaimed={fetchBalance}
                />
            ) : activeView === 'swap' ? (
                <SwapP2P 
                    figuritas={balanceData?.figuritas_poseidas || []}
                    privateKey={wallet.privateKey}
                    publicKeyPem={wallet.publicKeyPem}
                    onSuccess={() => {
                        setActiveView('home');
                        fetchBalance();
                    }}
                />
            ) : null}
        </div>
    );
}
