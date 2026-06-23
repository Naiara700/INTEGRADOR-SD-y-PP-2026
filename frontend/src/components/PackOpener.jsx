import React, { useState } from 'react';
import { signTransaction } from '../utils/cryptoUtils';
import '../styles/pack.css';

const PackOpener = ({ privateKeyHex, publicKeyPem, onPackOpened, currentPts }) => {
  const [isOpening, setIsOpening] = useState(false);
  const [revealedCards, setRevealedCards] = useState([]);
  const [error, setError] = useState(null);

  const baseUrl = import.meta.env.VITE_BACKEND_URL || '/proxy-api';

  const handleBuyPack = async () => {
    if (currentPts < 500) {
      setError("No tienes suficientes PTS. Necesitas 500 PTS para abrir un sobre.");
      return;
    }

    try {
      setIsOpening(true);
      setError(null);
      setRevealedCards([]);

      // 1. Armamos el payload para la transacción
      const payload = {
        action: "buy_pack",
        timestamp: Date.now()
      };

      // 2. Firmamos la transacción con Web Crypto API
      const signature = await signTransaction(privateKeyHex, payload);

      const requestBody = {
        public_key: publicKeyPem,
        payload: payload,
        signature: signature
      };

      // 3. Enviamos al Nodo Coordinador (vía Proxy Vite)
      const response = await fetch(`${baseUrl}/smart_contracts/buy_pack`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Error al comprar el sobre");
      }

      // 4. Si fue exitoso, la animación CSS 'packBurst' durará 1.5s
      // Esperamos que termine la animación del sobre para revelar las cartas
      setTimeout(() => {
        setRevealedCards(data.cartas || []);
        if (onPackOpened) {
          onPackOpened(); // Llamamos al padre para que actualice el saldo
        }
        setIsOpening(false);
      }, 1500);

    } catch (err) {
      console.error(err);
      setError(err.message);
      setIsOpening(false);
    }
  };

  const renderRarityEmoji = (rarity) => {
    switch (rarity) {
      case 'Legendaria': return '🌟';
      case 'Épica': return '✨';
      default: return '⚽';
    }
  };

  return (
    <div className="pack-store-container">
      <h2 className="pack-title">Gacha Store 2026</h2>
      <p className="pack-subtitle">Gasta 500 PTS para invocar 5 jugadores a tu álbum</p>

      {/* Sobre 3D */}
      {revealedCards.length === 0 && (
        <div className={`pack-wrapper ${isOpening ? 'opening' : ''}`} onClick={!isOpening ? handleBuyPack : undefined}>
          <div className="pack-front">
            {/* Placeholder logo, asumiendo que no hay assets de imagen por ahora */}
            <div style={{ fontSize: '4rem', marginBottom: '20px' }}>🌍</div>
            <h3 style={{ color: 'white', letterSpacing: '2px' }}>FIFA 2026</h3>
            <div className="pack-price">500 PTS</div>
          </div>
          <div className="pack-back">
            <h4 style={{ color: '#555' }}>StickerChain Holographic</h4>
          </div>
        </div>
      )}

      {/* Resultados: Cartas reveladas */}
      {revealedCards.length > 0 && (
        <div className="pack-results-container" style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '20px' }}>
          {revealedCards.map((card, index) => (
            <div key={card.fig_id || index} className={`card-item rarity-${card.rareza.toLowerCase()}`}>
              <div className="card-image-placeholder">
                {renderRarityEmoji(card.rareza)}
              </div>
              <div>
                <div className="card-name">{card.jugador}</div>
                <div className="card-team">{card.equipo}</div>
              </div>
              <div className="card-rarity">{card.rareza}</div>
            </div>
          ))}
        </div>
      )}

      {/* Botón explícito por si no quieren clickear el sobre */}
      {revealedCards.length === 0 && (
        <button 
          className="buy-button" 
          onClick={handleBuyPack} 
          disabled={isOpening || currentPts < 500}
        >
          {isOpening ? (
            <><span className="loading-spinner"></span> Invocando...</>
          ) : (
            `Abrir Sobre (500 PTS)`
          )}
        </button>
      )}

      {/* Botón para volver a comprar tras revelar */}
      {revealedCards.length > 0 && (
        <button 
          className="buy-button" 
          onClick={() => setRevealedCards([])} 
          style={{ marginTop: '40px' }}
        >
          Comprar Otro Sobre
        </button>
      )}

      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

export default PackOpener;
