import { useState, useEffect } from 'react';
import WalletAuth from './components/WalletAuth';
import Dashboard from './components/Dashboard';

export default function App() {
  const [wallet, setWallet] = useState(null);

  const handleLogin = (walletData) => {
    console.log("Logged in with alias:", walletData.alias);
    setWallet(walletData);
  };

  const handleLogout = () => {
    setWallet(null);
  };

  return (
    <div className="app-container">
      <nav className="top-nav glass-panel">
        <div className="nav-brand">🏆 StickerChain '26</div>
        {wallet && (
          <div className="flex items-center" style={{ display: 'flex', gap: '15px' }}>
            <span style={{ color: 'var(--text-muted)' }}>{wallet.alias}</span>
            <button onClick={handleLogout} className="glass-button" style={{ padding: '6px 12px', fontSize: '12px' }}>
              Salir
            </button>
          </div>
        )}
      </nav>

      {!wallet ? (
        <WalletAuth onLogin={handleLogin} />
      ) : (
        <Dashboard wallet={wallet} />
      )}
    </div>
  );
}
