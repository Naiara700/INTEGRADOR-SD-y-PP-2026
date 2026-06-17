1. Compilar el hit7_cuda.cu --> Ctrl + Shift + P > buscar Task: Run Task > Seleccionar la task "CUDA: compilar Hit7 MD5 rango"
2. Ejecutarlo en GPU--> .\bin\hit7_cuda.exe "cadena_base" "prefijo_hash" <min_rango> <max_rango>
3. Ejecutarlo en CPU (Pyhton) --> python .\Hit7\hit7_cpu.py "cadena_base" "prefijo_hash" <min_rango> <max_rango>

Agregar estos parametros de inicio y fin permite dividir el espacio de busqueda, lo cual es importante para poder *Distribuir*
el trabajo entre varios procesos o nodos.

## === Ejecucion en GPU ===

### - Caso donde se encontro solucion:

.\bin\hit7_cuda.exe "abc" "0000" 0 100000   --> busca el nonce en el rango [0-100000]

#### Salida obtenida:
Buscando nonce en rango...
Cadena base: abc
Prefijo requerido: 0000
Rango: [0, 100000]

Solucion encontrada
Numero: 34211
Texto usado: abc34211
Hash:   00002f1daee5ee909f41a692ca31423f

### - Caso donde NO se encontro solucion:

.\bin\hit7_cuda.exe "abc" "0000" 0 1000   --> busca el nonce en el rango [0-1000]

#### Salida obtenida:
Buscando nonce en rango...
Cadena base: abc
Prefijo requerido: 0000
Rango: [0, 1000]

No se encontro solucion en el rango indicado.

## === Ejecucion en CPU ===

### - Caso donde se encontro solucion:

python .\Hit7\hit7_cpu.py "abc" "0000" 0 100000   --> busca el nonce en el rango [0-100000]

#### Salida obtenida:
Buscando nonce en rango usando CPU...
Cadena base: abc
Prefijo requerido: 0000
Rango: [0, 100000]

Solucion encontrada
Numero: 34211
Texto usado: abc34211
Hash:   00002f1daee5ee909f41a692ca31423f
Intentos realizados: 34212
Tiempo: 0.062612 segundos
Velocidad: 546416.32 hashes/segundo

### - Caso donde NO se encontro solucion:

python .\Hit7\hit7_cpu.py "abc" "0000" 0 1000   --> busca el nonce en el rango [0-1000]

#### Salida obtenida:
Buscando nonce en rango usando CPU...
Cadena base: abc
Prefijo requerido: 0000
Rango: [0, 1000]

No se encontro solucion en el rango indicado.
Intentos realizados: 1001
Tiempo: 0.001259 segundos
Velocidad: 795075.46 hashes/segundo