# INTEGRADOR-SD-y-PP-2026 - PROPUESTA-1
## StickerChain: Álbum de Figuritas Digital Descentralizado
### Descripción de la Propuesta
StickerChain es una plataforma descentralizada diseñada para coleccionar e intercambiar figuritas digitales de eventos masivos (como un Mundial). El sistema reemplaza los servidores centrales tradicionales por una red blockchain, garantizando a los usuarios la propiedad absoluta de sus coleccionables y asegurando matemáticamente la escasez o "rareza" de las figuritas.

Para cumplir estrictamente con la estructura transaccional requerida de (Usuario A; Usuario B; Monto), la red procesa operaciones utilizando dos tipos de activos digitales que interactúan sobre la misma infraestructura de bloques: los Tokens Coleccionables (figuritas) y los Tokens de Recompensa (monedas/puntos).

### Profundización del Ecosistema de Tokens
A nivel de protocolo, la red maneja estrictamente valores numéricos en el campo Monto, acompañando cada transacción con metadatos en formato JSON para otorgar el contexto del juego.

1. Tokens Coleccionables (La Figurita)
Funcionan como un comprobante digital único (tipo NFT) que representa una figurita específica. Su origen en la billetera del usuario puede darse por dos vías distintas:

- *Vía A:* Acuñación por Apertura de Sobre (Minting): El sistema crea la figurita por primera vez.

  - Usuario A (Emisor): Tesorería Central (El Kiosco).

  - Usuario B (Receptor): Billetera del Coleccionista.

  - Monto: 1 FIG

  - Metadata adjunta: { "jugador": "Lionel Messi", "rareza": "Legendaria"}.

- *Vía B:* Mercado P2P (Intercambio): El usuario recibe una figurita que ya existía en la red, transferida por otro jugador.

  - Usuario A (Emisor): Billetera del Coleccionista 1.

  - Usuario B (Receptor): Billetera del Coleccionista 2.

  - Monto: 1 FIG.

  - Metadata adjunta: Conserva la metadata original de creación.

*Gestión de Figuritas Repetidas:*
A nivel técnico, una figurita "repetida" es simplemente un token 1 FIG que el sistema acuña con atributos idénticos en su metadata (ej: otro "De Paul" común) pero con un hash único. El sistema permite acumular repetidas. Estas repetidas son el motor de la economía secundaria: el usuario puede ofrecerlas en el Mercado P2P para realizar intercambios seguros por figuritas que le falten.

2. Tokens de Recompensa (Monedas / Consumible)
Es el saldo virtual (PTS) que los usuarios utilizan para comprar paquetes de figuritas en la tienda oficial del álbum.

*Dinámica Transaccional:*

- Usuario A (Emisor): Billetera del Coleccionista.

- Usuario B (Receptor): Tesorería del Álbum.

- Monto: 500 PTS (El costo de un paquete virtual).

- Metadata adjunta: { "concepto": "Compra de 1 Paquete Estándar" }.

3. Automatización mediante Contratos Inteligentes (Desafíos y QRs)
El Nodo Coordinador de Tareas (NCT) enlaza ambos tokens, digitalizando las reglas del juego.

**Códigos QR Físicos:** Al escanear el QR de un producto sponsor físico, el sistema emite una transacción desde la Tesorería hacia el usuario por 100 PTS, otorgando saldo para sobres.

**Desafíos (Logros):** El Coordinador monitorea el estado. Por ej: Si detecta que un usuario logró juntar los 11 Tokens FIG de una selección (llenó la hoja), el contrato inteligente se activa y encola automáticamente una transacción de premio.

- Usuario A (Emisor): Tesorería de Recompensas.

- Usuario B (Receptor): Billetera del Coleccionista.

- Monto: 2000 PTS (o 1 FIG de una figurita Dorada Especial).

- Metadata adjunta: { "concepto": "Premio por Desafío: Hoja Completada" }.

### Ejemplo Práctico: El Ciclo de Vida del Coleccionista
Para visualizar cómo el Nodo Coordinador de Tareas (NCT) gestiona los flujos, aquí se detalla el ciclo completo de un usuario:

**Escenario 1: Ingreso de Fondos (El Código QR)**
El usuario compra una botella de gaseosa sponsor, escanea el código QR físico y la Tesorería de Recompensas le transfiere 500 PTS de regalo.

**Escenario 2: Compra y Apertura del Sobre**
El usuario decide usar sus puntos para abrir un sobre.

*El Pago:* Transfiere 500 PTS a la Tesorería. El minero valida el pago.

*La Apertura:* El Nodo Coordinador detecta el pago, ejecuta un algoritmo de probabilidad (RNG) y emite automáticamente 5 transacciones nuevas desde la Tesorería hacia el usuario. Cada transacción transfiere 1 FIG.

**Escenario 3: Intercambio de Repetidas**
Al usuario le tocó un "Dibu Martínez" repetido. Entra al Mercado P2P y acuerda cambiar su token repetido con un amigo por un "Cuti Romero".

*Transacción:* El sistema encola ambas transferencias de 1 FIG de manera cruzada. El bloque solo se valida si ambos usuarios tienen la figurita en su inventario. El minero resuelve el bloque y ambas figuritas cambian de dueño en el mismo instante, evitando estafas.

**Escenario 4: El Desafío Completado**
El usuario pega su nuevo "Cuti Romero" y llena la hoja. El Coordinador detecta esto y dispara un contrato inteligente que premia al usuario transfiriendo una figurita exclusiva o 2000 PTS desde la Tesorería hacia su billetera.

### Justificación del Uso de Blockchain
**Resiliencia y Escalabilidad ante Picos de Demanda:** Durante un Mundial, el tráfico masivo colapsa los servidores. Aquí, las peticiones para abrir sobres se encolan asincrónicamente en RabbitMQ. Los nodos workers validan estas operaciones de forma paralela, garantizando que el sistema no se caiga.

**Transparencia de la "Rareza":** Al ser una blockchain, cualquiera puede auditar el registro y verificar matemáticamente cuántas figuritas "Legendarias" fueron emitidas realmente, garantizando un juego justo.

**Objetivo de la Prueba de Trabajo (PoW) en StickerChain**
La minería mediante fuerza bruta (algoritmos de hash en CUDA) protege la economía del álbum:

**1. Prevención de Duplicación (Doble Gasto):** Si un usuario intenta clonar su figurita más rara enviándola a dos amigos simultáneamente, el tiempo criptográfico que exige el PoW le permite al sistema validar el historial y rechazar la segunda transacción, protegiendo el valor de la colección.

**2. Intercambios Seguros sin Confianza Central:** El esfuerzo computacional consolida las transacciones P2P en el mercado. Asegura que nadie pueda alterar el bloque una vez minado para revertir un cambio legítimo luego de haber recibido la figurita del otro jugador.
