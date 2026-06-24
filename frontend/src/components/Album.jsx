import React, { useState, useEffect } from 'react';
import { signTransaction, deriveAddress } from '../utils/cryptoUtils';
import { Gift, Star, Award, CheckCircle, BookOpen, ArrowLeft, ArrowRight, Search } from 'lucide-react';

export default function Album({ figuritas, privateKey, publicKeyPem, onRewardClaimed }) {
    const [claiming, setClaiming] = useState(false);
    const [claimMessage, setClaimMessage] = useState('');
    const [template, setTemplate] = useState(null);
    const [currentPage, setCurrentPage] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');
    const [dailyChallenges, setDailyChallenges] = useState([]);
    const [loadingChallenges, setLoadingChallenges] = useState(true);
    const TEAMS_PER_PAGE = 1; // Cantidad de equipos por página del álbum
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

        const fetchDailyChallenges = async () => {
            if (!publicKeyPem) return;
            setLoadingChallenges(true);
            try {
                const derivedAddr = await deriveAddress(publicKeyPem);
                const response = await fetch(`${baseUrl}/smart_contracts/daily_challenges?wallet_id=${derivedAddr}`);
                const data = await response.json();
                if (response.ok && data.challenges) {
                    setDailyChallenges(data.challenges);
                }
            } catch (error) {
                console.error('Error al cargar retos diarios:', error);
            } finally {
                setLoadingChallenges(false);
            }
        };

        fetchTemplate();
        fetchDailyChallenges();
    }, [baseUrl, publicKeyPem]);

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

    const teamGroups = {
        "México": "A", "Sudáfrica": "A", "Corea del Sur": "A", "República Checa": "A",
        "Canadá": "B", "Bosnia y Herzegovina": "B", "Qatar": "B", "Suiza": "B",
        "Brasil": "C", "Marruecos": "C", "Haití": "C", "Escocia": "C",
        "Estados Unidos": "D", "Paraguay": "D", "Australia": "D", "Turquía": "D",
        "Alemania": "E", "Curazao": "E", "Costa de Marfil": "E", "Ecuador": "E",
        "Países Bajos": "F", "Japón": "F", "Suecia": "F", "Túnez": "F",
        "Bélgica": "G", "Egipto": "G", "Irán": "G", "Nueva Zelanda": "G",
        "España": "H", "Cabo Verde": "H", "Arabia Saudita": "H", "Uruguay": "H",
        "Francia": "I", "Senegal": "I", "Irak": "I", "Noruega": "I",
        "Argentina": "J", "Argelia": "J", "Austria": "J", "Jordania": "J",
        "Portugal": "K", "RD Congo": "K", "Uzbekistán": "K", "Colombia": "K",
        "Inglaterra": "L", "Croacia": "L", "Ghana": "L", "Panamá": "L"
    };

    // Obtener y ordenar equipos por grupo
    const rawEquipos = template ? Object.keys(template.equipos) : Object.keys(albumAgrupado);
    const equiposOrdenados = rawEquipos.sort((a, b) => {
        const groupA = teamGroups[a] || 'Z';
        const groupB = teamGroups[b] || 'Z';
        if (groupA === groupB) return a.localeCompare(b);
        return groupA.localeCompare(groupB);
    });

    const equipos = equiposOrdenados.filter(equipo => {
        if (!searchTerm) return true;
        const group = teamGroups[equipo] || '';
        const s = searchTerm.toLowerCase();
        return equipo.toLowerCase().includes(s) ||
            `grupo ${group.toLowerCase()}`.includes(s) ||
            group.toLowerCase() === s;
    });

    // Mapeo manual de banderas por la mezcla de extensiones y nombres
    const flagMap = {
        "Alemania": "alemania.png",
        "Arabia Saudita": "arabiaSaudita.png",
        "Argelia": "argelia.png",
        "Argentina": "argentina.png",
        "Australia": "australia.png",
        "Austria": "austria.png",
        "Bélgica": "belgica.png",
        "Bosnia": "bosnia.png",
        "Brasil": "brasil.png",
        "Cabo Verde": "caboVerde.png",
        "Canadá": "canada.png",
        "Colombia": "colombia.png",
        "Costa de Marfil": "costaDeMarfil.png",
        "Croacia": "croacia.png",
        "Curazao": "curazao.png",
        "Ecuador": "ecuador.png",
        "Egipto": "egipto.png",
        "Escocia": "escocia.png",
        "España": "españa.png",
        "Estados Unidos": "estadosUnidos.png",
        "Francia": "francia.png",
        "Ghana": "ghana.png",
        "Haití": "haiti.png",
        "Inglaterra": "inglaterra.png",
        "Irak": "irak.png",
        "Irán": "iran.png",
        "Japón": "japon.png",
        "Jordania": "jordania.png",
        "Corea": "korea.png",
        "Marruecos": "marruecos.png",
        "México": "mexico.png",
        "Noruega": "noruega.png",
        "Nueva Zelanda": "nuevaZelanda.png",
        "Países Bajos": "paisesBajos.png",
        "Panamá": "panama.png",
        "Portugal": "portugal.png",
        "Qatar": "qatar.png",
        "República Checa": "republicaCheca.png",
        "Senegal": "senegal.png",
        "Sudáfrica": "sudafrica.png",
        "Suecia": "suecia.png",
        "Suiza": "suiza.png",
        "Túnez": "tunez.png",
        "Turquía": "turquia.png",
        "Uzbekistán": "uzbekiztan.png",
        "Uruguay": "uruguay.png" // Fallbacks follow standard if missing
    };

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
        "Uzbekistán": "Uzbekistán"
    };

    const getPlayerFolder = (equipo) => {
        return playerFolderMap[equipo] || equipo;
    };

    const getFlagUrl = (equipo) => {
        if (!equipo) return '';
        if (flagMap[equipo]) {
            return `/assets/flags/${flagMap[equipo]}`;
        }

        // Fallback genérico a camelCase + .png
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
            const payload = { tipo_desafio: desafio_id };
            const signature = await signTransaction(privateKey, payload);

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

            setClaimMessage(data.message || '¡Recompensa Reclamada (Pendiente de confirmación en bloque)!');
            
            // Actualización optimista: marcamos completado inmediatamente en la UI
            setDailyChallenges(prev => prev.map(reto => 
                reto.id === desafio_id ? { ...reto, completado: true } : reto
            ));

            if (onRewardClaimed) onRewardClaimed();

            // Sigue intentando obtener el estado real en background, 
            // aunque puede tardar hasta que el bloque se mine.
            try {
                const res = await fetch(`${baseUrl}/smart_contracts/daily_challenges?wallet_id=${encodeURIComponent(publicKeyPem)}`);
                const d = await res.json();
                if (res.ok && d.challenges) {
                    // Solo actualizamos si nos devuelve algo nuevo o válido
                    setDailyChallenges(d.challenges);
                }
            } catch (e) { }

            setTimeout(() => setClaimMessage(''), 5000);
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
            <div className="glass-panel" style={{ padding: '20px', marginBottom: '30px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <h3 style={{ marginBottom: '15px', fontSize: '1.2rem', color: 'var(--text-muted)' }}>
                    Retos Diarios
                </h3>

                {loadingChallenges ? (
                    <p style={{ color: 'var(--text-muted)' }}>Cargando retos...</p>
                ) : (
                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'nowrap', width: '100%', justifyContent: 'space-between' }}>
                        {dailyChallenges.map((reto) => {
                            // Validar localmente si cumple para habilitar botón
                            let cumple = false;
                            let reqStr = "";
                            if (reto.id === 'LOGIN_DIARIO' || reto.id === 'HOJA_COMPLETA') {
                                cumple = true; // El server validará
                            } else if (reto.condicion) {
                                if (reto.condicion.tipo === 'total') {
                                    const unicas = new Set(figuritas.map(f => f.jugador)).size;
                                    cumple = unicas >= reto.condicion.cantidad;
                                    reqStr = `Tenes ${unicas}/${reto.condicion.cantidad}`;
                                } else if (reto.condicion.tipo === 'dorada') {
                                    const doradas = figuritas.filter(f => f.es_dorada).length;
                                    cumple = doradas >= reto.condicion.cantidad;
                                    reqStr = `Tenes ${doradas}/${reto.condicion.cantidad}`;
                                } else if (reto.condicion.tipo === 'equipo') {
                                    const equipo = figuritas.filter(f => f.equipo === reto.condicion.equipo).length;
                                    cumple = equipo >= reto.condicion.cantidad;
                                    reqStr = `Tenes ${equipo}/${reto.condicion.cantidad}`;
                                }
                            }

                            const isCompleted = reto.completado;
                            const isDisabled = claiming || isCompleted || (!cumple && reto.id !== 'LOGIN_DIARIO' && reto.id !== 'HOJA_COMPLETA');

                            return (
                                <button
                                    key={reto.id}
                                    className="glass-button"
                                    onClick={() => claimReward(reto.id)}
                                    disabled={isDisabled}
                                    style={{
                                        flex: 1,
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: '5px',
                                        whiteSpace: 'normal',
                                        textAlign: 'center',
                                        padding: '10px 5px',
                                        fontSize: '0.80rem',
                                        opacity: isDisabled ? 0.5 : 1,
                                        borderColor: isCompleted ? '#10b981' : (reto.id === 'LOGIN_DIARIO' ? '' : (cumple ? 'gold' : '')),
                                        color: isCompleted ? '#10b981' : ''
                                    }}
                                    title={isCompleted ? "Ya completado hoy" : (!cumple && reqStr ? reqStr : "")}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                                        {reto.id.includes('DORADA') ? <Star size={16} /> : <Award size={16} />}
                                        {reto.desc}
                                    </div>
                                    {isCompleted && <span style={{ fontSize: '0.65rem' }}>COMPLETADO</span>}
                                    {!isCompleted && !cumple && reqStr && <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{reqStr}</span>}
                                </button>
                            );
                        })}
                    </div>
                )}

                {claimMessage && (
                    <p style={{ width: '100%', textAlign: 'center', marginTop: '10px', color: 'var(--accent)', fontWeight: 'bold' }} className="animate-fade-in">
                        {claimMessage}
                    </p>
                )}
            </div>

            {/* Grilla de Equipos con Paginación */}
            {!template ? (
                <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>Cargando plantilla del álbum...</p>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%' }}>
                    {/* Barra de Búsqueda */}
                    <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--glass-border)', padding: '10px 15px', borderRadius: '8px', marginBottom: '10px' }}>
                        <Search size={20} color="var(--text-muted)" style={{ marginRight: '10px' }} />
                        <input
                            type="text"
                            placeholder="Buscar selección o grupo (ej: Grupo A, Argentina...)"
                            value={searchTerm}
                            onChange={(e) => {
                                setSearchTerm(e.target.value);
                                setCurrentPage(0); // Resetear a página 1 al buscar
                            }}
                            style={{ background: 'transparent', border: 'none', color: 'white', width: '100%', outline: 'none', fontSize: '1rem', fontFamily: 'Inter' }}
                        />
                    </div>

                    {/* Controles de Paginación Superior */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0' }}>
                        <button
                            onClick={() => setCurrentPage(prev => Math.max(0, prev - 1))}
                            disabled={currentPage === 0}
                            className="glass-button"
                            style={{ opacity: currentPage === 0 ? 0.5 : 1, width: '140px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                        >
                            <ArrowLeft size={18} /> Anterior
                        </button>
                        <span style={{ fontWeight: 'bold', color: 'var(--text-muted)' }}>
                            Página {equipos.length === 0 ? 0 : currentPage + 1} de {Math.ceil(equipos.length / TEAMS_PER_PAGE)}
                        </span>
                        <button
                            onClick={() => setCurrentPage(prev => Math.min(Math.ceil(equipos.length / TEAMS_PER_PAGE) - 1, prev + 1))}
                            disabled={currentPage >= Math.ceil(equipos.length / TEAMS_PER_PAGE) - 1 || equipos.length === 0}
                            className="glass-button"
                            style={{ opacity: (currentPage >= Math.ceil(equipos.length / TEAMS_PER_PAGE) - 1 || equipos.length === 0) ? 0.5 : 1, width: '140px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                        >
                            Siguiente <ArrowRight size={18} />
                        </button>
                    </div>

                    {equipos.length === 0 && (
                        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                            No se encontraron selecciones.
                        </div>
                    )}

                    {equipos.slice(currentPage * TEAMS_PER_PAGE, (currentPage + 1) * TEAMS_PER_PAGE).map(equipo => {
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
                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px', marginRight: '10px' }}>
                                            Grupo {teamGroups[equipo] || '?'}
                                        </span>
                                        {equipo}
                                    </h3>
                                    <span style={{ marginLeft: 'auto', background: cantidadPoseidas === jugadoresEquipo.length ? 'rgba(16, 185, 129, 0.2)' : 'var(--glass-border)', color: cantidadPoseidas === jugadoresEquipo.length ? '#10b981' : 'white', padding: '5px 10px', borderRadius: '20px', fontSize: '0.9rem', fontWeight: cantidadPoseidas === jugadoresEquipo.length ? 'bold' : 'normal' }}>
                                        {cantidadPoseidas} / {jugadoresEquipo.length}
                                    </span>
                                </div>

                                <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '15px' }}>
                                    {jugadoresEquipo.map((jugador, idx) => {
                                        const fig = figuritasPoseidas[jugador]; // Check si la tiene
                                        const isOwned = !!fig;
                                        const isDorada = fig?.es_dorada;

                                        return (
                                            <div
                                                key={idx}
                                                className={`glass-panel ${isDorada ? 'holographic' : ''}`}
                                                style={{
                                                    width: idx === 12 ? 'calc(66.666% - 5px)' : 'calc(33.333% - 10px)',
                                                    flexShrink: 0,
                                                    padding: isOwned ? '0' : '15px 10px',
                                                    textAlign: 'center',
                                                    position: 'relative',
                                                    display: 'flex',
                                                    flexDirection: 'column',
                                                    justifyContent: 'center',
                                                    minHeight: idx === 12 ? '180px' : '350px',
                                                    borderColor: isDorada ? 'gold' : isOwned ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                                                    background: isDorada ? 'linear-gradient(135deg, rgba(255,215,0,0.1), rgba(218,165,32,0.3))' : isOwned ? 'rgba(59, 130, 246, 0.1)' : 'rgba(0,0,0,0.3)',
                                                    filter: !isOwned ? 'grayscale(100%) opacity(0.5)' : 'none',
                                                    transition: 'all 0.3s ease',
                                                    overflow: 'hidden'
                                                }}
                                            >
                                                {isDorada && (
                                                    <Star size={24} color="gold" fill="gold" style={{ position: 'absolute', top: '-10px', right: '-10px', filter: 'drop-shadow(0 0 10px gold)', zIndex: 10 }} />
                                                )}

                                                {!isOwned && (
                                                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '5px' }}>#{idx + 1}</p>
                                                )}

                                                {!isOwned && (
                                                    <h4 style={{ fontSize: '1.1rem', margin: '0 0 10px 0', fontWeight: 'bold', color: isDorada ? 'gold' : 'var(--text-muted)', zIndex: 2 }}>
                                                        ???
                                                    </h4>
                                                )}

                                                {isOwned && (
                                                    <img
                                                        src={`/assets/players/${getPlayerFolder(equipo)}/${idx + 1}.png`}
                                                        alt={fig.jugador}
                                                        style={{ width: '100%', height: '100%', objectFit: 'cover', margin: '0', borderRadius: '4px', zIndex: 1 }}
                                                        onError={(e) => {
                                                            if (e.target.src.endsWith('.png')) {
                                                                e.target.src = `/assets/players/${getPlayerFolder(equipo)}/${idx + 1}.jpg`;
                                                            } else {
                                                                e.target.style.display = 'none';
                                                            }
                                                        }}
                                                    />
                                                )}

                                                {!isOwned && (
                                                    <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '-5px', marginBottom: '10px', zIndex: 2 }}>
                                                        {jugador}
                                                    </p>
                                                )}

                                                {!isOwned && (
                                                    <img
                                                        src={getFlagUrl(equipo)}
                                                        alt="Bandera miniatura"
                                                        style={{ width: '30px', margin: '0 auto', opacity: 0.3, borderRadius: '2px' }}
                                                        onError={(e) => { e.target.style.display = 'none'; }}
                                                    />
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        );
                    })}

                    {/* Controles de Paginación Inferior */}
                    {equipos.length > 0 && (
                        <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', padding: '20px 0', borderTop: '1px solid var(--glass-border)', marginTop: '20px' }}>
                            <button
                                onClick={() => {
                                    setCurrentPage(prev => Math.max(0, prev - 1));
                                    window.scrollTo({ top: 0, behavior: 'smooth' });
                                }}
                                disabled={currentPage === 0}
                                className="glass-button"
                                style={{ opacity: currentPage === 0 ? 0.5 : 1, width: '140px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                            >
                                <ArrowLeft size={18} /> Anterior
                            </button>
                            <button
                                onClick={() => {
                                    setCurrentPage(prev => Math.min(Math.ceil(equipos.length / TEAMS_PER_PAGE) - 1, prev + 1));
                                    window.scrollTo({ top: 0, behavior: 'smooth' });
                                }}
                                disabled={currentPage >= Math.ceil(equipos.length / TEAMS_PER_PAGE) - 1}
                                className="glass-button"
                                style={{ opacity: currentPage >= Math.ceil(equipos.length / TEAMS_PER_PAGE) - 1 ? 0.5 : 1, width: '140px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                            >
                                Siguiente <ArrowRight size={18} />
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
