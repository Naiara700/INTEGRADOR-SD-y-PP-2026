import React, { useState, useEffect } from 'react';
import { signTransaction } from '../utils/cryptoUtils';
import '../styles/pack.css';

const playerFolderMap = {
  "Japón": "Japon",
  "México": "Mexico",
  "Países Bajos": "Paises_Bajos",
  "Corea": "Korea",
  "Corea del Sur": "Korea",
  "Nueva Zelanda": "nueva zelanda",
  "Paraguay": "paraguay",
  "Suecia": "suecia",
  "Suiza": "suiza",
  "Sudáfrica": "Sudafrica",
  "Bélgica": "Bélgica",
  "Bosnia y Herzegovina": "Bosnia",
  "Canadá": "Canadá",
  "España": "España",
  "Haití": "Haití",
  "Irán": "Irán",
  "Panamá": "Panamá",
  "República Checa": "República Checa",
  "Turquía": "Turquía",
  "Túnez": "Túnez",
  "Uzbekistán": "Uzbekistán",
  "RD Congo": "República Democrática del Congo"
};

const getPlayerFolder = (equipo) => playerFolderMap[equipo] || equipo;

const PackOpener = ({ privateKey, publicKeyPem, onPackOpened, currentPts, figuritas }) => {
  const [isOpening, setIsOpening] = useState(false);
  const [revealedCards, setRevealedCards] = useState([]);
  const [error, setError] = useState(null);
  const [template, setTemplate] = useState(null);

  const baseUrl = import.meta.env.VITE_BACKEND_URL || '/proxy-api';

  // Cargar el template del álbum para poder buscar el índice de cada jugador
  useEffect(() => {
    const fetchTemplate = async () => {
      try {
        const res = await fetch(`${baseUrl}/album_template`);
        if (res.ok) {
          const data = await res.json();
          setTemplate(data);
        }
      } catch (err) {
        console.error("Error cargando template:", err);
      }
    };
    fetchTemplate();
  }, [baseUrl]);

  // Dado un jugador y equipo, buscar su índice (1-based) en la plantilla
  const getPlayerIndex = (jugador, equipo) => {
    if (!template || !template.equipos) return null;
    const jugadores = template.equipos[equipo];
    if (!jugadores) return null;
    const idx = jugadores.indexOf(jugador);
    return idx >= 0 ? idx + 1 : null;
  };

  const getPlayerImageUrl = (card) => {
    const folder = getPlayerFolder(card.equipo);
    const idx = getPlayerIndex(card.jugador, card.equipo);
    if (!idx) return null;
    return `/assets/players/${folder}/${idx}.png`;
  };

  const handleBuyPack = async () => {
    if (currentPts < 500) {
      setError("No tienes suficientes PTS. Necesitas 500 PTS para abrir un sobre.");
      return;
    }

    try {
      setIsOpening(true);
      setError(null);
      setRevealedCards([]);

      const payload = {
        action: "buy_pack",
        timestamp: Date.now()
      };

      const signature = await signTransaction(privateKey, payload);

      const requestBody = {
        public_key: publicKeyPem,
        payload: payload,
        signature: signature
      };

      const response = await fetch(`${baseUrl}/smart_contracts/buy_pack`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Error al comprar el sobre");
      }

      setTimeout(() => {
        const seen = new Set((figuritas || []).map(f => `${f.equipo}-${f.jugador}`));
        const cartasConRepetidas = (data.cartas || []).map(card => {
            const key = `${card.equipo}-${card.jugador}`;
            if (seen.has(key)) {
                return { ...card, is_repeated: true };
            }
            seen.add(key);
            return card;
        });
        setRevealedCards(cartasConRepetidas);
        if (onPackOpened) onPackOpened();
        setIsOpening(false);
      }, 1500);

    } catch (err) {
      console.error(err);
      setError(err.message);
      setIsOpening(false);
    }
  };

  const getRarityLabel = (rarity) => {
    switch (rarity) {
      case 'Legendaria': return '🌟 LEGENDARIA';
      case 'Épica': return '✨ ÉPICA';
      default: return '⚽ COMÚN';
    }
  };

  return (
    <div className="pack-store-container">
      <h2 className="pack-title">Gacha Store 2026</h2>
      <p className="pack-subtitle">Gastá 500 PTS para invocar 5 jugadores a tu álbum</p>

      {/* Sobre con imagen real */}
      {revealedCards.length === 0 && (
        <div className={`pack-wrapper ${isOpening ? 'opening' : ''}`} onClick={!isOpening ? handleBuyPack : undefined}>
          <div className="pack-front">
            <img
              src="/assets/ui/sobre_cerrado.png"
              alt="Sobre FIFA 2026"
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                borderRadius: '10px',
                position: 'absolute',
                top: 0,
                left: 0,
                zIndex: 1
              }}
            />
            <div className="pack-price" style={{ position: 'relative', zIndex: 2, marginTop: 'auto', marginBottom: '15px' }}>500 PTS</div>
          </div>
          <div className="pack-back">
            <h4 style={{ color: '#555' }}>StickerChain Holographic</h4>
          </div>
        </div>
      )}

      {/* Cartas reveladas con fotos de jugadores */}
      {revealedCards.length > 0 && (
        <div className="pack-results-container" style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '20px' }}>
          {revealedCards.map((card, index) => {
            const idx = getPlayerIndex(card.jugador, card.equipo);
            const imgUrl = getPlayerImageUrl(card);
            const isTeamPhoto = idx === 13;
            return (
              <div 
                key={card.fig_id || index} 
                className={`card-item rarity-${card.rareza.toLowerCase()}`}
                style={{
                  width: isTeamPhoto ? '340px' : '180px',
                  height: '260px'
                }}
              >
                {/* Foto del jugador */}
                <div className="card-photo-container" style={{
                  width: '100%',
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  overflow: 'hidden',
                  borderRadius: '8px',
                  background: 'rgba(0,0,0,0.3)',
                  marginBottom: '10px'
                }}>
                  {imgUrl ? (
                    <img
                      src={imgUrl}
                      alt={card.jugador}
                      style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '8px' }}
                      onError={(e) => {
                        if (e.target.src.endsWith('.png')) {
                          e.target.src = imgUrl.replace('.png', '.jpg');
                        } else {
                          e.target.style.display = 'none';
                          e.target.parentElement.innerHTML = `<span style="font-size:2.5rem">⚽</span>`;
                        }
                      }}
                    />
                  ) : (
                    <span style={{ fontSize: '2.5rem' }}>⚽</span>
                  )}
                </div>



                {/* Badge de rareza */}
                <div className="card-rarity">{getRarityLabel(card.rareza)}</div>
                
                {/* Badge de REPETIDA */}
                {card.is_repeated && (
                    <div style={{
                        position: 'absolute',
                        top: '-10px',
                        right: '-10px',
                        background: 'var(--danger)',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontWeight: 'bold',
                        fontSize: '0.8rem',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.5)',
                        zIndex: 10,
                        border: '2px solid white'
                    }}>
                        ¡REPETIDA!
                    </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Botón de compra */}
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

      {/* Botón para volver a comprar */}
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
