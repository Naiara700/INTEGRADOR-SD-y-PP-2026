# INTEGRADOR-SD-y-PP-2026 - PROPUESTA-1
## SmartCampus: Sistema Integral de Identidad y Valor Estudiantil
### Descripción de la Propuesta
SmartCampus es una plataforma descentralizada diseñada para asegurar la gestión de la vida universitaria. A través de una Billetera de Identidad Estudiantil, el sistema unifica la trayectoria académica (analítico) y la gestión económica del alumno en el campus.  
Para cumplir estrictamente con la estructura transaccional requerida de (Usuario A; Usuario B; Monto), la red procesa operaciones utilizando dos tipos de activos digitales que circulan sobre la misma infraestructura de bloques: los Tokens Académicos y los Tokens de Beneficio.

### Profundización del Ecosistema de Tokens
A nivel de protocolo, la red maneja estrictamente valores numéricos en el campo Monto, acompañando cada transacción con metadatos en formato JSON para otorgar el contexto institucional.

**Tokens Académicos:** Representan el progreso académico del estudiante, como materias aprobadas o seminarios completados. No tienen un valor económico, sino curricular, funcionando como un certificado único digital (tipo NFT).
*Dinámica Transaccional:*
- Usuario A (Emisor): La Cátedra (ej: Sistemas Distribuidos) o el Departamento de Ciencias Básicas.
- Usuario B (Receptor): La billetera digital del alumno.
- Monto: 1 ACAD (Representando la certificación única de una materia). Metadata adjunta: { "materia": "Sistemas Distribuidos", "nota": 8, "horas": 90 }.
*Caso de uso:* Cuando el profesor cierra las actas, el sistema emite una transacción transfiriendo el token con la nota a la billetera del alumno. Una vez que el bloque se valida, esa nota queda sellada criptográficamente para siempre.

**Tokens de Beneficio** Representan recursos tangibles destinados a la vida diaria en la universidad. Funcionan como dinero transaccional líquido.
*Dinámica Transaccional:*
- Usuario A (Emisor): La Secretaría de Asuntos Estudiantiles o el ente gubernamental correspondiente.
- Usuario B (Receptor): La billetera digital del alumno.
- Monto: Saldo en créditos líquidos. (Ejemplo: 81000 BENF para gastos mensuales de programas de ayuda financiera como las Becas, cupos para la fotocopiadora, o 1500 BENF para un menú del comedor). Metadata adjunta: { "concepto": "Beca Manuel Belgrano - Mayo" } o { "concepto": "Menú Estudiantil Diario" }.
*Caso de uso:* El alumno recibe su asignación mensual en tokens. Al momento de almorzar o sacar apuntes, realiza una nueva transacción transfiriendo 1500 Tokens de Beneficio de su billetera a la billetera del Comedor Universitario, o a la de la fotocopiadora.

### Automatización mediante Contratos Inteligentes (Recompensas por Rendimiento)
El sistema enlaza ambos tokens de forma directa: el rendimiento académico funciona como disparador automático para la asignación de beneficios, digitalizando las reglas de los programas de becas.

Dinámica Transaccional Automatizada: El minero resuelve el bloque confirmando un Token Académico con una calificación sobresaliente (ej: nota >= 8). El Nodo Coordinador de Tareas lee esta condición en la metadata, aplica la regla de negocio institucional de la beca y encola una nueva transacción de recompensa económica hacia la billetera del alumno.

Usuario A (Emisor): Fondo de Becas de la Universidad.

Usuario B (Receptor): La billetera digital del alumno.

Monto: 5000 BENF.

Metadata adjunta: { "concepto": "Incentivo Económico a la Excelencia Académica" }.

### Ejemplo Práctico: El Ciclo de Vida de los Tokens y el Dinero
El flujo funciona de la siguiente manera:

1. Respaldo Real: El Estado o la Universidad deposita el presupuesto de becas en pesos (ej: $1.000.000) en una cuenta institucional tradicional. El sistema acuña el equivalente exacto en tokens (1.000.000 BENF) y los almacena en la billetera central del "Fondo de Becas".
2. El Disparador: El alumno aprueba la materia, el minero valida el bloque y se le transfiere 1 ACAD.
3. El Premio Automático: El Coordinador detecta la buena calificación y transfiere automáticamente BENF desde el "Fondo de Becas" hacia la billetera del alumno.
4. El Consumo: El alumno utiliza BENF para pagar sus gastos en el campus (almuerzo, fotocopias), transfiriéndolos a la billetera del concesionario del comedor.
5. La Liquidación: A fin de mes, el comedor envía los tokens acumulados a la Universidad. La red destruye esos tokens digitales y la administración transfiere el dinero equivalente en pesos reales desde su cuenta institucional a la cuenta del proveedor, cerrando el ciclo económico.

### Justificación del Uso de Blockchain
La implementación de una base de datos distribuida resuelve vulnerabilidades criticas de los sistemas centralizados universitarios:   
- Resiliencia Operativa: Si los servidores de administración se caen durante un pico de demanda, los alumnos igual pueden seguir utilizando su credencial y sus tokens, ya que el estado del sistema y los bloques se mantienen replicados en múltiples nodos.
- Auditoría y Transparencia: Permite trazar perfectamente el flujo de los fondos públicos o becas. El Estado o la Universidad pueden auditar en el registro público de la blockchain que los recursos llegaron exactamente a los alumnos correspondientes y se utilizaron para los fines previstos.

### Objetivo de la Prueba de Trabajo (PoW) en SmartCampus
Su objetivo se divide en dos funciones vitales para el producto:   
1. Blindaje del Historial Académico contra Alteraciones: Para que un alumno o un atacante externo pueda "hackear" el sistema y subirse la nota de un 4 a un 9 retroactivamente, tendría que modificar un bloque pasado. El algoritmo de Prueba de Trabajo hace que esto sea computacionalmente inviable. Para que la red acepte ese bloque adulterado, el atacante necesitaría recalcular el nonce de ese bloque y de todos los siguientes más rápido que toda la red legitima combinada (un ataque del 51%). El PoW asegura que el analítico del alumno sea absoluta y matemáticamente inmutable.
2. Prevención del Fraude y Doble Gasto de Beneficios: Un estudiante podría intentar enviar los mismos 1500 Tokens de Beneficio simultáneamente al sistema de la fotocopiadora y al del comedor para duplicar su saldo de forma fraudulenta. El PoW crea una dificultad criptográfica intencional que toma tiempo resolver.  Mientras las GPUs compiten para calcular el hash correcto del bloque, el sistema tiene el tiempo necesario para validar el historial en Redis, determinar qué transacción entró primero al pool de transacciones y rechazar el intento de doble gasto, protegiendo los recursos de la universidad.  
