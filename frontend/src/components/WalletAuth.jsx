import React, { useState } from 'react';
import { generateWalletKeys, encryptPrivateKey, decryptPrivateKey } from '../utils/cryptoUtils';
import { Wallet, Key, ShieldCheck, ArrowRight } from 'lucide-react';

export default function WalletAuth({ onLogin }) {
    const [isCreating, setIsCreating] = useState(false);
    const [alias, setAlias] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleCreateWallet = async (e) => {
        e.preventDefault();
        if (!alias || !password) return setError("Por favor completa todos los campos.");
        if (password.length < 6) return setError("La contraseña debe tener al menos 6 caracteres.");
        
        setLoading(true);
        setError('');
        
        try {
            // 1. Generar par de claves RSA nativas
            const { privateKey, publicKeyPem } = await generateWalletKeys();
            
            // 2. Encriptar la clave privada con la contraseña usando AES-GCM
            const encryptedPrivKey = await encryptPrivateKey(privateKey, password);
            
            // 3. Guardar todo en localStorage
            localStorage.setItem('wallet_alias', alias);
            localStorage.setItem('wallet_public_key', publicKeyPem);
            localStorage.setItem('wallet_private_key_enc', encryptedPrivKey);
            
            // Iniciar sesión en memoria
            onLogin({ alias, publicKeyPem, privateKey });
        } catch (err) {
            setError("Error al crear la billetera: " + err.message);
        }
        setLoading(false);
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        if (!alias || !password) return setError("Ingresa tu alias y contraseña.");
        
        setLoading(true);
        setError('');
        
        try {
            const savedAlias = localStorage.getItem('wallet_alias');
            const savedPublicKey = localStorage.getItem('wallet_public_key');
            const savedEncryptedPriv = localStorage.getItem('wallet_private_key_enc');
            
            if (!savedAlias || !savedPublicKey || !savedEncryptedPriv) {
                throw new Error("No se encontró una billetera en este navegador.");
            }

            if (savedAlias !== alias) {
                throw new Error("El alias no coincide con la billetera guardada.");
            }
            
            // Desencriptar la clave privada
            const privateKey = await decryptPrivateKey(savedEncryptedPriv, password);
            
            // Iniciar sesión
            onLogin({ alias: savedAlias, publicKeyPem: savedPublicKey, privateKey });
        } catch (err) {
            setError("Credenciales incorrectas o billetera no encontrada.");
        }
        setLoading(false);
    };

    const hasWallet = !!localStorage.getItem('wallet_alias');

    return (
        <div className="auth-container animate-fade-in">
            <div className="glass-panel auth-card">
                <div className="auth-icon-wrapper">
                    <div className="auth-icon">
                        {isCreating ? <Key size={48} color="#60a5fa" /> : <Wallet size={48} color="#60a5fa" />}
                    </div>
                </div>
                
                <h1 className="auth-title">
                    {isCreating ? 'Crear Billetera' : 'Desbloquear Billetera'}
                </h1>
                <p className="auth-subtitle">
                    {isCreating ? 'Generando identidad criptográfica RSA en tu dispositivo.' : 'Accede a tus fondos y figuritas del Mundial 2026.'}
                </p>

                <form onSubmit={isCreating ? handleCreateWallet : handleLogin} className="auth-form">
                    <input
                        type="text"
                        placeholder={isCreating ? "Elige un Alias (Ej: CryptoFan99)" : "Ingresa tu Alias"}
                        className="glass-input"
                        value={alias}
                        onChange={(e) => setAlias(e.target.value)}
                        disabled={loading}
                    />
                    
                    <input
                        type="password"
                        placeholder="Contraseña de Desbloqueo"
                        className="glass-input"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        disabled={loading}
                    />

                    {error && (
                        <div className="auth-error">
                            <ShieldCheck size={16} /> {error}
                        </div>
                    )}

                    <button 
                        type="submit" 
                        className="glass-button auth-submit"
                        disabled={loading}
                    >
                        {loading ? 'Procesando...' : (isCreating ? 'Generar Llaves' : 'Desbloquear')}
                        {!loading && <ArrowRight size={18} />}
                    </button>
                </form>

                <div className="auth-footer">
                    <button 
                        onClick={() => {
                            setIsCreating(!isCreating);
                            setError('');
                        }}
                        className="auth-switch-btn"
                    >
                        {isCreating ? 'Ya tengo una billetera, quiero desbloquearla' : 'Crear una billetera nueva'}
                    </button>
                </div>
            </div>
        </div>
    );
}
