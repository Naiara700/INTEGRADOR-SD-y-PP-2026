# Guía y Justificación de Manifiestos de Kubernetes

Este documento detalla cada archivo `.yaml` dentro de la carpeta `Pilar3/k8s`, explicando qué tipo de objeto de Kubernetes (`kind`) utiliza y cuál es su función específica dentro de la arquitectura de StickerChain.

---

## 1. Nodos Principales (Backend y Base de Datos)

### `nct/deployment.yaml` (Nodo Coordinador de Tareas)
- **Kind principal**: `StatefulSet` y `Service` (Headless)
- **Qué hace**: Despliega el backend principal (Oráculo y Validador de Smart Contracts).
- **Justificación del Kind**: El backend utiliza el **Algoritmo de Bully** para elegir un líder P2P. El algoritmo requiere que cada nodo tenga un nombre predecible y numerado (`nct-0`, `nct-1`). Un `StatefulSet` garantiza estos nombres exactos, mientras que un `Deployment` generaría nombres aleatorios que romperían el consenso.

### `redis/statefulset.yaml` (Almacenamiento del Estado)
- **Kind principal**: `StatefulSet` y `Service`
- **Qué hace**: Despliega la base de datos Redis, que actúa como el "Libro Mayor" (Ledger) de la blockchain guardando los bloques, billeteras y figuritas.
- **Justificación del Kind**: Requiere persistencia en disco. El `StatefulSet` asegura que cada pod mantenga su identidad y se conecte siempre a su mismo disco (PersistentVolumeClaim) incluso si se reinicia, evitando perder la blockchain.

---

## 2. Cola de Mensajes (RabbitMQ y Secretos)

### `rabbit/statefulset.yaml`
- **Kind principal**: `StatefulSet` y `Service`
- **Qué hace**: Despliega RabbitMQ, el broker de mensajería asíncrona encargado de distribuir las tareas de minería y recibir las soluciones.
- **Justificación del Kind**: Las colas requieren persistencia en disco para no perder transacciones si el broker se cae. Además, RabbitMQ necesita identidades estables para sincronizar la base de datos interna de su clúster (Mnesia DB).

### `rabbit/configmap.yaml`
- **Kind principal**: `ConfigMap`
- **Qué hace**: Guarda configuraciones estáticas de RabbitMQ (como habilitar plugins o definir límites de memoria) sin exponer contraseñas.
- **Justificación del Kind**: El `ConfigMap` es el estándar de Kubernetes para inyectar configuraciones limpias en formato texto plano a los contenedores.

### `rabbit/secret-store.yaml` y `rabbit/external-secret.yaml`
- **Kind principal**: `ClusterSecretStore` y `ExternalSecret`
- **Qué hace**: Permiten que el clúster se conecte directamente con **GCP Secret Manager** para descargar la contraseña de RabbitMQ y la inyecten de forma segura en los pods.
- **Justificación del Kind**: Son recursos personalizados del operador *External Secrets Operator (ESO)*. Evitan que las contraseñas queden hardcodeadas en texto plano en Git.

---

## 3. Servicios Stateless (Sin Estado) y Minería

### `trp/deployment.yaml` (Pool de Transacciones)
- **Kind principal**: `Deployment` y `Service`
- **Qué hace**: Recibe bloques, los fragmenta matemáticamente (Split) y despacha los rangos de Nonces a RabbitMQ.
- **Justificación del Kind**: Es una API intermedia que no guarda nada en memoria ni en disco. Al ser 100% efímera, el `Deployment` es perfecto porque permite matar o replicar el servicio instantáneamente sin preocuparse por los datos.

### `worker/deployment-cpu.yaml` y `worker/deployment-gpu-external.yaml`
- **Kind principal**: `Deployment`
- **Qué hace**: Despliegan los mineros (CPU para el clúster local de GKE, GPU para el clúster remoto de k3s de Ale). Toman tareas de RabbitMQ, resuelven los algoritmos Proof-of-Work (hit7) y devuelven el hash.
- **Justificación del Kind**: Son "daemon workers" descartables. No tienen almacenamiento propio ni reciben tráfico HTTP. Si el `Deployment` detecta que un worker muere en pleno cálculo, RabbitMQ reasigna la tarea automáticamente a otro pod.

### `worker/hpa-cpu.yaml` y `worker/hpa-gpu-external.yaml`
- **Kind principal**: `HorizontalPodAutoscaler` (HPA)
- **Qué hace**: Monitorean el consumo de CPU de los workers. Si detectan que hay mucha demanda de cálculo, ordenan al clúster levantar más réplicas de los mineros automáticamente.
- **Justificación del Kind**: Es el controlador nativo de K8s para auto-escalado horizontal basado en métricas.

---

## 4. Frontend y Red

### `frontend/deployment.yaml`
- **Kind principal**: `Deployment` y `Service`
- **Qué hace**: Despliega el servidor web (Vite/Nginx) que hospeda la interfaz de usuario en React.
- **Justificación del Kind**: Son archivos estáticos HTML/JS. El `Deployment` permite escalar réplicas web para soportar muchos usuarios simultáneos sin ningún riesgo de pérdida de datos.

### `ingress.yaml`
- **Kind principal**: `Ingress`
- **Qué hace**: Es el "guardia de la puerta" del clúster. Recibe todo el tráfico de internet (`stickerchain.lat`), analiza la URL (`/api`, `/smart_contracts`, `/`) y enruta la petición al microservicio correcto.
- **Justificación del Kind**: Reemplaza la necesidad de tener múltiples IPs públicas (LoadBalancers). Permite centralizar el enrutamiento y manejar certificados SSL en un solo lugar.

### `cluster-issuer.yaml`
- **Kind principal**: `ClusterIssuer`
- **Qué hace**: Habla de forma automatizada con *Let's Encrypt* para pedir certificados SSL y habilitar HTTPS gratis.
- **Justificación del Kind**: Es un recurso del operador *Cert-Manager*, esencial para mantener la seguridad web sin intervención manual.
