# Hit #6 - Longitudes de prefijo en CUDA HASH

## Objetivo

Medir el tiempo requerido para encontrar un nonce valido usando diferentes longitudes de prefijo, comparando la implementacion GPU CUDA contra la implementacion CPU en Python.

## Configuracion de la prueba

- Cadena base utilizada: `abc`
- Implementacion GPU: `bin/hit5_cuda.exe`
- Implementacion CPU: `Hit5/hit5_cpu.py`
- Hash utilizado: MD5
- Metodo de medicion: script Python con `subprocess` y `time.perf_counter()`
- Longitud maxima probada: 6

## Resultados comparativos

| Longitud | Prefijo | Numero GPU | Tiempo GPU (s) | Hashes/s GPU | Numero CPU | Tiempo CPU (s) | Hashes/s CPU | Aceleracion GPU vs CPU |
|----------|---------|------------|----------------|--------------|------------|----------------|--------------|------------------------|
| 1        | `0`     | 4072       | 0.195935       | 20787.51     | 5          | 0.055900       | 107.33       | 0.29x                  |
| 2        | `00`    | 6107       | 0.192304       | 31762.21     | 18         | 0.055568       | 341.92       | 0.29x                  |
| 3        | `000`   | 3527       | 0.190876       | 18483.25     | 2196       | 0.058223       | 37733.97     | 0.31x                  |
| 4        | `0000`  | 34211      | 0.181875       | 188107.11    | 34211      | 0.096509       | 354495.44    | 0.53x                  |
| 5        | `00000` | 3231929    | 0.193911       | 16667044.85  | 3231929    | 3.947384       | 818752.33    | 20.36x                 |
| 6        | `000000`| 8605828    | 0.213376       | 40331662.58  | 8605828    | 10.192493      | 844330.13    | 47.77x                 |

## Detalle de hashes encontrados

| Implementacion | Longitud | Prefijo |  Numero |  Texto usado |                Hash                |
|================|==========|=========|=========|==============|====================================|
| GPU            | 1        | `0`     | 4072    | `abc4072`    | `06e591087aeec0f6e753b7ab59bf388b` |
| CPU            | 1        | `0`     | 5       | `abc5`       | `08b23036b726919c08cfe8703a339035` |
|----------------|----------|---------|---------|--------------|------------------------------------|
| GPU            | 2        | `00`    | 6107    | `abc6107`    | `00fdd4df62d3c1f0a2853a7fe300c6c5` |
| CPU            | 2        | `00`    | 18      | `abc18`      | `0034e0923cc38887a57bd7b1d4f953df` |
|----------------|----------|---------|---------|--------------|------------------------------------|
| GPU            | 3        | `000`   | 3527    | `abc3527`    | `0008a94875cd7adc8f2592a44226f29c` |
| CPU            | 3        | `000`   | 2196    | `abc2196`    | `000d69e0505d8d009ab51658079af109` |
|----------------|----------|---------|---------|--------------|------------------------------------|
| GPU            | 4        | `0000`  | 34211   | `abc34211`   | `00002f1daee5ee909f41a692ca31423f` |
| CPU            | 4        | `0000`  | 34211   | `abc34211`   | `00002f1daee5ee909f41a692ca31423f` |
|----------------|----------|---------|---------|--------------|------------------------------------|
| GPU            | 5        | `00000` | 3231929 | `abc3231929` | `00000155f8105dff7f56ee10fa9b9abd` |
| CPU            | 5        | `00000` | 3231929 | `abc3231929` | `00000155f8105dff7f56ee10fa9b9abd` |
|----------------|----------|---------|---------|--------------|------------------------------------|
| GPU            | 6        | `000000`| 8605828 | `abc8605828` | `0000000ea49fd3fc1b2f10e02d98ee96` |
| CPU            | 6        | `000000`| 8605828 | `abc8605828` | `0000000ea49fd3fc1b2f10e02d98ee96` |

## Analisis

La dificultad aumenta exponencialmente con la longitud del prefijo. Como el hash MD5 se representa en hexadecimal, cada caracter del prefijo puede tomar 16 valores posibles. Por eso, la probabilidad aproximada de que un hash cumpla un prefijo de longitud `n` es:

```txt
1 / 16^n
```

Por lo tanto, el numero esperado de intentos para encontrar una solucion es:

```txt
16^n
```

Esto implica que cada caracter hexadecimal adicional en el prefijo multiplica el trabajo esperado aproximadamente por 16. En la practica, los tiempos no crecen de forma perfectamente regular porque la busqueda depende de la posicion en la que aparece el primer hash valido.

## Prefijo mas largo encontrado en GPU

- Prefijo: `000000`
- Longitud: 6
- Numero: 8605828
- Texto usado: `abc8605828`
- Hash: `0000000ea49fd3fc1b2f10e02d98ee96`
- Tiempo: 0.213376 segundos

## Prefijo mas largo encontrado en CPU

- Prefijo: `000000`
- Longitud: 6
- Numero: 8605828
- Texto usado: `abc8605828`
- Hash: `0000000ea49fd3fc1b2f10e02d98ee96`
- Tiempo: 10.192493 segundos
