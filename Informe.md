# Informe TP Integrador
## Pilar 1
### Entorno utilizado
- Lenguajes de programación: C/C++ para el desarrollo del minero GPU (CUDA) y  Python para el desarrollo del minero compatible con CPU.
- Editor de Código / IDE: Visual Studio Code.
### Problemas

### Setup.
Al disponer de hardware nativo con una tarjeta NVIDIA local (GTX 1650 Super), el desarrollo y las pruebas se realizan directamente en el equipo. El proceso se maneja directamente desde la terminal de Windows. El código fuente en CUDA (.cu) se compila utilizando el comando nvcc del Toolkit para generar el ejecutable binario.  

### Características del hardware nativo
**GPU:** NVIDIA GeForce GTX 1650 Super
**CUDA:** 12.6
**Compilador:** nvcc incluido en el CUDA Toolkit
**Sistema operativo:** Windows 10

### NVIDIA CCCL
El repositorio NVIDIA/cccl (CUDA Core Compute Libraries) es un proyecto oficial que unifica tres bibliotecas fundamentales de C++ para el desarrollo de software acelerado por GPU: Thrust: biblioteca de alto nivel, su mayor ventaja es que te permite programar operaciones complejas en paralelo de forma muy sencilla, y el mismo código puede ejecutarse tanto en tu procesador (CPU) como en la tarjeta gráfica (GPU). ; CUB: Es una biblioteca de bajo nivel, diseñada para exprimir al máximo la velocidad de las tarjetas NVIDIA. Proporciona las primitivas matemáticas y lógicas más rápidas posibles para que armar algoritmos propios dentro de la GPU. y libcudacxx: Es la versión oficial de la Biblioteca Estándar de C++ pero adaptada para el mundo CUDA. Su función es garantizar que las herramientas y estructuras clásicas de C++ funcionen tanto del lado del Host como del lado del Device. 

Su propósito principal es brindar a los desarrolladores un conjunto de algoritmos paralelos y primitivas de alto rendimiento que sean portables y eficientes, actuando en conjunto como una biblioteca estándar optimizada específicamente para el ecosistema CUDA. Al estar compuesto únicamente por archivos de encabezado, facilita su integración directa en el código fuente de cualquier proyecto sin requerir procesos de compilación o instalación adicionales. 

*Cuando fue la última vez que se actualizó?* 
A la fecha del día la ultima actualización es del 17/6/26 19:19

*Compilen y ejecuten el primer ejemplo de la sección Vectors de Thrust. ¿Hace falta instalar algo adicional o ya viene con CUDA?*
Una vez que instalás el CUDA Toolkit, no tenés que descargar ni instalar Thrust, CUB ni libcudacxx por separado. Todas esas herramientas ya vienen empaquetadas e incluidas directamente adentro del Toolkit.

### Diferencias entre programar CUDA puro vs usar Thrust/CCCL.
- Nivel de abstracción y estilo de código: Mientras que CUDA nativo es una extensión de C que requiere escribir kernels detallados y manejar la jerarquía de hilos, Thrust es una biblioteca de plantillas de C++ basada en la Standard Template Library (STL). Thrust proporciona una interfaz de alto nivel que permite implementar aplicaciones paralelas con un esfuerzo de programación mínimo y con un código fuente mucho más conciso y legible.
- Manejo de la memoria: En CUDA tradicional, se debe reservar memoria manualmente y usar funciones como cudaMemcpy para mover datos entre la CPU y la GPU. Thrust simplifica esto enormemente introduciendo contenedores dinámicos como host_vector (memoria de la CPU) y device_vector (memoria de la GPU). Por ejemplo, copiar datos de la RAM a la tarjeta de video se logra con una simple asignación usando el operador =.
- Algoritmos predefinidos vs. Reinventar la rueda: Si se programa "nativamente", se debe diseñar algoritmos propios de ordenamiento o reducción. Thrust, en cambio, provee una colección de algoritmos paralelos listos para usar (como scan, sort, reduce y transform). Todos estos algoritmos tienen implementaciones tanto para el host (CPU) como para el device (GPU).
- Optimización automática: Al describir los cálculos utilizando las abstracciones de alto nivel de Thrust, le damos a la biblioteca la libertad de seleccionar automáticamente la implementación más eficiente para el hardware subyacente.
- Enfoque en la productividad: Debido a su simplicidad, Thrust es ideal para el prototipado rápido de aplicaciones CUDA, priorizando la productividad del programador sin sacrificar la robustez y el rendimiento absoluto necesarios para entornos de producción.
