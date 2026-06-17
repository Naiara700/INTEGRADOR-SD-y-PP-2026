1. Compilar el Hit 5
2. Ejecutar el script del Benchmark --> python .\Hit6\hit6_benchmark.py "cadena" <Max_Prefijos>

Se le deben pasar 2 parametros: la cadena y la cantidad maxima de prefijos a testear.
El benchmark ira ejecutando las pruebas desde 1 hasta <Max_Prefijos> y comparando el rendimiento de la ejecucion con GPU vs CPU.

Finalmente genera el informe .md con los resultados obtenidos.

En principio, la CPU parece ser mas rapida que la GPU con una baja cantidad de prefijos. Esto se debe al costo de lanzar el kernel CUDA y copiar datos desde
la CPU a la GPU y viceversa, lo que se lleva la mayor carga de trabajo.