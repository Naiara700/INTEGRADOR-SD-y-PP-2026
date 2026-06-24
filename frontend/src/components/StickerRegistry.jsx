import React, { useState, useEffect } from 'react';
import { PackageOpen, Users, Star, Sparkles, Copy, BookOpen } from 'lucide-react';
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

const teamGroups = {
    "México": "A", "Sudáfrica": "A", "Corea del Sur": "A", "República Checa": "A",
    "Canadá": "B", "Bosnia y Herzegovina": "B", "Qatar": "B", "Suiza": "B",
    "Brasil": "C", "Marruecos": "C", "Haití": "C", "Escocia": "C",
    "Estados Unidos": "D", "Paraguay": "D", "Australia": "D", "Turquía": "D",
    "Alemania": "E", "Curazao": "E", "Costa de Marfil": "E", "Ecuador": "E",
    "Países Bajos": "F", "Japón": "F", "Suecia": "F", "Túnez": "F",
    "Bélgica": "G", "Egipto": "G", "Irán": "G", "Nueva Zelanda": "G",
    "España": "H", "Cabo Verde": "H", "Arabia Saudita": "H", "Uruguay": "H",
    "Portugal": "I", "Camerún": "I", "Corea": "I", "Uzbekistán": "I",
    "Inglaterra": "J", "Senegal": "J", "RD Congo": "J", "Panamá": "J"
};

const getPlayerFolder = (equipo) => playerFolderMap[equipo] || equipo;

export default function StickerRegistry({ figuritas }) {
    const [activeTab, setActiveTab] = useState('pegadas');
    const [template, setTemplate] = useState(null);
    const [filterEquipo, setFilterEquipo] = useState('');
    const [filterGrupo, setFilterGrupo] = useState('');
    const [filterRareza, setFilterRareza] = useState('');
    const baseUrl = import.meta.env.VITE_BACKEND_URL || '/proxy-api';

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

    // Procesar figuritas
    const pegadasMap = new Map();
    const repetidas = [];

    figuritas.forEach(fig => {
        const key = `${fig.equipo}-${fig.jugador}`;
        if (!pegadasMap.has(key)) {
            pegadasMap.set(key, fig);
        } else {
            // Si ya existe la "pegada", la actual es "repetida"
            repetidas.push(fig);
            // Optimizamos si la nueva es de mejor rareza, la ponemos como pegada y mandamos la vieja a repetidas
            const currentPegada = pegadasMap.get(key);
            const rank = { "Legendaria": 3, "Épica": 2, "Común": 1 };
            const currentRank = rank[currentPegada.rareza] || 1;
            const newRank = rank[fig.rareza] || 1;
            if (newRank > currentRank) {
                pegadasMap.set(key, fig); // La mejor va al álbum
                repetidas[repetidas.length - 1] = currentPegada; // La de menor rareza a repetidas
            }
        }
    });

    const pegadas = Array.from(pegadasMap.values());

    const getRarityLabel = (rarity) => {
        switch (rarity) {
            case 'Legendaria': return '🌟 LEGENDARIA';
            case 'Épica': return '✨ ÉPICA';
            default: return '⚽ COMÚN';
        }
    };

    const renderGrid = (cards) => {
        const filteredCards = cards.filter(c => {
            if (filterEquipo && c.equipo !== filterEquipo) return false;
            if (filterGrupo && teamGroups[c.equipo] !== filterGrupo) return false;
            if (filterRareza && c.rareza !== filterRareza) return false;
            return true;
        });

        if (filteredCards.length === 0) {
            return (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                    No hay figuritas en esta sección que coincidan con los filtros.
                </div>
            );
        }

        return (
            <div className="pack-results-container" style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '20px' }}>
                {filteredCards.map((card, index) => {
                    const idx = getPlayerIndex(card.jugador, card.equipo);
                    const imgUrl = getPlayerImageUrl(card);
                    const isTeamPhoto = idx === 13;

                    return (
                        <div 
                            key={card.fig_id || index} 
                            className={`card-item rarity-${card.rareza.toLowerCase()}`} 
                            style={{ 
                                position: 'relative',
                                width: isTeamPhoto ? '340px' : '180px',
                                height: '260px',
                                animation: 'none',
                                opacity: 1,
                                transform: 'none'
                            }}
                        >
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
                            <div className="card-rarity">{getRarityLabel(card.rareza)}</div>
                        </div>
                    );
                })}
            </div>
        );
    };

    return (
        <div className="glass-panel" style={{ padding: '30px' }}>
            <h2 style={{ fontSize: '2rem', marginBottom: '20px', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
                <Users color="var(--primary)" /> Registro de Colección
            </h2>

            <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', marginBottom: '30px' }}>
                <button 
                    onClick={() => setActiveTab('pegadas')}
                    className="glass-button"
                    style={{ 
                        padding: '12px 24px', 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '8px',
                        background: activeTab === 'pegadas' ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                        color: activeTab === 'pegadas' ? '#fff' : 'var(--text-muted)'
                    }}
                >
                    <BookOpen size={20} />
                    Pegadas ({pegadas.length})
                </button>
                <button 
                    onClick={() => setActiveTab('repetidas')}
                    className="glass-button"
                    style={{ 
                        padding: '12px 24px', 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '8px',
                        background: activeTab === 'repetidas' ? 'var(--danger)' : 'rgba(255,255,255,0.05)',
                        color: activeTab === 'repetidas' ? '#fff' : 'var(--text-muted)'
                    }}
                >
                    <Copy size={20} />
                    Repetidas ({repetidas.length})
                </button>
            </div>

            {/* Filtros */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '15px', marginBottom: '30px', flexWrap: 'wrap' }}>
                <select 
                    className="glass-panel" 
                    style={{ padding: '10px', background: 'rgba(0,0,0,0.3)', color: '#fff', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', cursor: 'pointer' }}
                    value={filterEquipo}
                    onChange={(e) => setFilterEquipo(e.target.value)}
                >
                    <option value="" style={{ color: '#000' }}>Todos los Equipos</option>
                    {Object.keys(teamGroups).sort().map(eq => <option key={eq} value={eq} style={{ color: '#000' }}>{eq}</option>)}
                </select>

                <select 
                    className="glass-panel" 
                    style={{ padding: '10px', background: 'rgba(0,0,0,0.3)', color: '#fff', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', cursor: 'pointer' }}
                    value={filterGrupo}
                    onChange={(e) => setFilterGrupo(e.target.value)}
                >
                    <option value="" style={{ color: '#000' }}>Todos los Grupos</option>
                    {['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'].map(g => <option key={g} value={g} style={{ color: '#000' }}>Grupo {g}</option>)}
                </select>

                <select 
                    className="glass-panel" 
                    style={{ padding: '10px', background: 'rgba(0,0,0,0.3)', color: '#fff', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', cursor: 'pointer' }}
                    value={filterRareza}
                    onChange={(e) => setFilterRareza(e.target.value)}
                >
                    <option value="" style={{ color: '#000' }}>Todas las Rarezas</option>
                    <option value="Común" style={{ color: '#000' }}>Común</option>
                    <option value="Épica" style={{ color: '#000' }}>Épica</option>
                    <option value="Legendaria" style={{ color: '#000' }}>Legendaria</option>
                </select>
            </div>

            {activeTab === 'pegadas' ? renderGrid(pegadas) : renderGrid(repetidas)}
        </div>
    );
}
