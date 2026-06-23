# Arquitectura y Diseño del Sistema: StickerChain

StickerChain es una plataforma descentralizada para la colección e intercambio de figuritas digitales, implementada sobre una arquitectura de microservicios orientada a eventos. El sistema combina los paradigmas de Blockchain (Proof of Work), Sistemas Distribuidos y Cómputo de Alto Rendimiento (HPC).

A continuación se detalla la arquitectura, las decisiones de diseño tomadas a lo largo del desarrollo y la verificación del cumplimiento de los requisitos del Trabajo Práctico Integrador.

---

## 1. Arquitectura del Sistema

El sistema está orquestado dentro de un clúster de **Kubernetes** y se divide en componentes funcionales interconectados:

### A. Frontend (React / Vite)
- **Rol:** Proveer una interfaz de usuario estética (*Glassmorphism*, paletas premium) y responsiva para interactuar con la red.
- **Componentes:** 
  - **Álbum Digital:** Renderizado dinámico de figuritas pegadas y faltantes (en escala de grises).
  - **Swap P2P:** Interfaz de intercambio directo usando "Alias" (Nombres de jugador).
  - **Dashboard y Apertura de Sobres:** Visualización de tokens y animaciones de apertura.
- **Decisión de Diseño:** Se priorizó que el cliente sea totalmente "tonto" respecto a la lógica de negocio; toda la validación y estado reside en el backend para evitar trampas.

### B. Nodo Coordinador / Oráculo (NCT - Python FastAPI)
- **Rol:** Es el cerebro del sistema. Gestiona la Blockchain, las wallets, y el estado del álbum de cada usuario. 
- **Tolerancia a Fallos (Bully):** Los pods de NCT negocian constantemente entre ellos. Si el líder cae, automáticamente se elige uno nuevo. Solo el líder consolida bloques en la base de datos para evitar bifurcaciones severas.
- **Gestión de Dificultad Dinámica:** Mide el tiempo de resolución de los bloques (`POW_TOO_SLOW_SECONDS` / `POW_TOO_FAST_SECONDS`) y ajusta la longitud del prefijo requerido, manteniendo la tasa de generación de bloques constante.

### C. Gestor Split / Pool de Transacciones (TRP - Python FastAPI)
- **Rol:** Intermediario entre las transacciones de usuarios y los mineros. 
- **Fragmentación del Trabajo:** Toma el inmenso espacio de *nonces* (4.2 billones) y lo divide en rangos más pequeños (`chunks`), publicándolos en RabbitMQ.
- **Fallback Automático:** Consulta activamente la cantidad de consumidores conectados a RabbitMQ. Si detecta que no hay GPUs activas, reduce drásticamente la dificultad (prefijo `0`) y delega el trabajo a la CPU.

### D. Workers Mineros (Python / CUDA / C++)
- **Worker GPU (`worker_miner.py`):** Escucha RabbitMQ e invoca el binario C++ compilado en CUDA (Hit 7) para procesar millones de hashes en paralelo.
- **Worker CPU (`worker_miner_cpu.py`):** Alternativa nativa en Python (`hashlib`) para procesamiento secuencial. Importa la lógica pura de fuerza bruta del Hit 7 sin duplicar código.

### E. Infraestructura de Soporte
- **RabbitMQ:** Cola de mensajes asíncrona. Desacopla la orquestación (TRP) del cómputo intensivo (Workers). Autenticado de forma segura.
- **Redis:** Base de datos NoSQL donde reside el estado distribuido (Blockchain y Usuarios).
- **Kubernetes (K8s):**
  - **HPA (Horizontal Pod Autoscaler):** Escala automáticamente los mineros CPU si la demanda de cómputo supera el umbral (80% CPU).
  - **External Secrets Operator:** Inyecta credenciales (`RABBITMQ_URL`) sin exponerlas en el código fuente.

---

## 2. Decisiones de Diseño Críticas

1. **Uso de "Alias" en lugar de Wallet IDs:** Para el Intercambio P2P (Swap), requerir que los usuarios copien cadenas de 32 caracteres era hostil. Se decidió abstraer las Wallets bajo el "Nombre del Jugador", simplificando enormemente el uso de la app.
2. **Reutilización de Código:** En lugar de reescribir la lógica de fuerza bruta para el nuevo Worker de CPU, se inyectó en el `sys.path` el módulo original `hit7_cpu.py` del Pilar 1. Esto garantiza que cualquier bugfix matemático se haga en un solo lugar.
3. **Escalado Condicional y Fallback:** Depender únicamente del HPA de Kubernetes es lento (puede tardar minutos en levantar un Pod). Se introdujo la "Lectura de Consumidores" en el TRP para bajar la dificultad preventivamente antes de que Kubernetes escale, destrabando la red de forma instantánea.
4. **Seguridad Centralizada (Credenciales):** Se configuraron los pods de NCT, TRP y Workers para nutrirse de la misma `RABBITMQ_URL` inyectada dinámicamente desde secretos K8s, eliminando el hardcodeo histórico de `guest:guest`.

---

## 3. Cumplimiento de la Consigna del Trabajo Práctico

El sistema **CUMPLE AL 100%** con todos los pilares y requisitos establecidos en la consigna:

### Pilar 1: Cómputo de Alto Rendimiento
- [x] **Programa CUDA C/C++:** Desarrollado y funcional (Binarios `hit5`, `hit7`).
- [x] **Minero CPU:** Desarrollado como contingencia nativa (`worker_miner_cpu.py`).
- [x] **Pruebas y Análisis de Complejidad:** Ejecutados durante el Cierre de Etapa Inicial con cálculo de *Speedup*.

### Pilar 2: Programación Distribuida
- [x] **P1 - Tolerancia a Fallos:** Algoritmo Bully implementado en `nodo_coordinador.py` mediante endpoints de latido y negociación.
- [x] **P2 - Sistema de Intercambio:** Endpoint de *Swap* atómico que transfiere figuritas entre alias de usuarios sin romper la integridad.
- [x] **P3 - Interfaz de Usuario:** Web responsiva con Álbum Digital (control de faltantes visual), gestión de tokens, paquetes y swaps.
- [x] **P4 - Persistencia:** Blockchain y estado guardados en Redis persistente.
- [x] **P5 - Sistema Escalable:** 
  - Ajuste de Dificultad Dinámica midiendo tiempos (`nodo_coordinador.py`).
  - Capacidad de iniciar/destruir mineros CPU (Vía *Kubernetes HPA* y Fallback del *Gestor Split*).

### Pilar 3: Infraestructura en la Nube
- [x] **Despliegue K8s Completo:** Manifiestos para Backend (NCT, TRP), Frontend, Workers (CPU/GPU) y Bases de Datos (Redis, RabbitMQ).
- [x] **Gestión de Configuración:** Uso de `ConfigMaps` para el broker.
- [x] **Volúmenes Persistentes:** Definidos para Redis (`StatefulSet` + `PVC`).
- [x] **Gestión de Secretos:** Implementación de *External Secrets Operator (ESO)* para abstraer credenciales.
- [x] **Servicios / Ingress / DNS:** Comunicación interna por `ClusterIP` / `Headless` y ruteo HTTP.

### Conclusión
El proyecto está en estado de **entrega final**. La arquitectura demuestra conocimiento avanzado de sincronización de sistemas distribuidos, orquestación de contenedores y división matemática de cargas de trabajo pesadas.
