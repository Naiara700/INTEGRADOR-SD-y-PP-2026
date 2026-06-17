# Cierre etapa inicial - Comparativa CPU vs GPU

## Objetivo

Se ejecuto una bateria de tests sobre las implementaciones CPU y GPU desarrolladas en los hits anteriores. El objetivo fue verificar que ambas implementaciones produzcan resultados equivalentes y comparar sus tiempos de ejecucion.

## Implementaciones comparadas

- GPU CUDA Hit #5: `bin/hit5_cuda.exe`
- CPU Python Hit #5: `Hit5/hit5_cpu.py`
- GPU CUDA Hit #7: `bin/hit7_cuda.exe`
- CPU Python Hit #7: `Hit7/hit7_cpu.py`

## Bateria de tests utilizada

|       Test       |  Hit |                         Parametros                      |
|------------------|------|---------------------------------------------------------|
| H5_pref_0        | Hit5 | `cadena="abc", prefijo="0"`                             |
| H5_pref_00       | Hit5 | `cadena="abc", prefijo="00"`                            |
| H5_pref_000      | Hit5 | `cadena="abc", prefijo="000"`                           |
| H5_pref_0000     | Hit5 | `cadena="abc", prefijo="0000"`                          |
| H5_pref_00000    | Hit5 | `cadena="abc", prefijo="00000"`                         |
| H7_rango_chico   | Hit7 | `cadena="abc", prefijo="0000", rango=[0,1000]`          |
| H7_rango_medio   | Hit7 | `cadena="abc", prefijo="0000", rango=[0,100000]`        |
| H7_rango_partido | Hit7 | `cadena="abc", prefijo="0000", rango=[1001,100000]`     |
| H7_rango_grande  | Hit7 | `cadena="abc", prefijo="00000", rango=[0,2000000]`      |
| H7_rango_desplaz | Hit7 | `cadena="abc", prefijo="00000", rango=[500000,3000000]` |

## Resultados comparativos

|       Test       |  Hit |   Estado GPU  | Tiempo GPU (s) | Nonce GPU |   Estado CPU  | Tiempo CPU (s) | Nonce CPU | Coinciden | Speedup GPU |
|------------------|------|---------------|----------------|-----------|---------------|----------------|-----------|-----------|-------------|
| H5_pref_0        | Hit5 | ENCONTRADO    | 0.200409       | 6114      | ENCONTRADO    | 0.056656       | 5         | No        | 0.28x       |
| H5_pref_00       | Hit5 | ENCONTRADO    | 0.191513       | 7164      | ENCONTRADO    | 0.057415       | 18        | No        | 0.30x       |
| H5_pref_000      | Hit5 | ENCONTRADO    | 0.187718       | 3527      | ENCONTRADO    | 0.060061       | 2196      | No        | 0.32x       |
| H5_pref_0000     | Hit5 | ENCONTRADO    | 0.191360       | 34211     | ENCONTRADO    | 0.095170       | 34211     | Si        | 0.50x       |
| H5_pref_00000    | Hit5 | ENCONTRADO    | 0.194229       | 3231929   | ENCONTRADO    | 3.882560       | 3231929   | Si        | 19.99x      |
| H7_rango_chico   | Hit7 | NO_ENCONTRADO | 0.183449       | -         | NO_ENCONTRADO | 0.057836       | -         | Si        | 0.32x       |
| H7_rango_medio   | Hit7 | ENCONTRADO    | 0.180690       | 34211     | ENCONTRADO    | 0.118830       | 34211     | Si        | 0.66x       |
| H7_rango_partido | Hit7 | ENCONTRADO    | 0.198075       | 34211     | ENCONTRADO    | 0.114149       | 34211     | Si        | 0.58x       |
| H7_rango_grande  | Hit7 | NO_ENCONTRADO | 0.193468       | -         | NO_ENCONTRADO | 2.324114       | -         | Si        | 12.01x      |
| H7_rango_desplaz | Hit7 | NO_ENCONTRADO | 0.198874       | -         | NO_ENCONTRADO | 4.578380       | -         | Si        | 23.02x      |

## Detalle de hashes encontrados

|       Test       | Implementacion |     Estado    |  Nonce  |               Hash                 |
|==================|================|===============|=========|====================================|
| H5_pref_0        |       GPU      | ENCONTRADO    | 6114    | `04eb468aa23e35c9de835786fed19b67` |
| H5_pref_0        |       CPU      | ENCONTRADO    | 5       | `08b23036b726919c08cfe8703a339035` |
|------------------|----------------|---------------|---------|------------------------------------|
| H5_pref_00       |       GPU      | ENCONTRADO    | 7164    | `006486359674bc7963a290f4cca5ed4c` |
| H5_pref_00       |       CPU      | ENCONTRADO    | 18      | `0034e0923cc38887a57bd7b1d4f953df` |
|------------------|----------------|---------------|---------|------------------------------------|
| H5_pref_000      |       GPU      | ENCONTRADO    | 3527    | `0008a94875cd7adc8f2592a44226f29c` |
| H5_pref_000      |       CPU      | ENCONTRADO    | 2196    | `000d69e0505d8d009ab51658079af109` |
|------------------|----------------|---------------|---------|------------------------------------|
| H5_pref_0000     |       GPU      | ENCONTRADO    | 34211   | `00002f1daee5ee909f41a692ca31423f` |
| H5_pref_0000     |       CPU      | ENCONTRADO    | 34211   | `00002f1daee5ee909f41a692ca31423f` |
|------------------|----------------|---------------|---------|------------------------------------|
| H5_pref_00000    |       GPU      | ENCONTRADO    | 3231929 | `00000155f8105dff7f56ee10fa9b9abd` |
| H5_pref_00000    |       CPU      | ENCONTRADO    | 3231929 | `00000155f8105dff7f56ee10fa9b9abd` |
|------------------|----------------|---------------|---------|------------------------------------|
| H7_rango_chico   |       GPU      | NO_ENCONTRADO | -       | `-`                                |
| H7_rango_chico   |       CPU      | NO_ENCONTRADO | -       | `-`                                |
|------------------|----------------|---------------|---------|------------------------------------|
| H7_rango_medio   |       GPU      | ENCONTRADO    | 34211   | `00002f1daee5ee909f41a692ca31423f` |
| H7_rango_medio   |       CPU      | ENCONTRADO    | 34211   | `00002f1daee5ee909f41a692ca31423f` |
|------------------|----------------|---------------|---------|------------------------------------|
| H7_rango_partido |       GPU      | ENCONTRADO    | 34211   | `00002f1daee5ee909f41a692ca31423f` |
| H7_rango_partido |       CPU      | ENCONTRADO    | 34211   | `00002f1daee5ee909f41a692ca31423f` |
|------------------|----------------|---------------|---------|------------------------------------|
| H7_rango_grande  |       GPU      | NO_ENCONTRADO | -       | `-`                                |
| H7_rango_grande  |       CPU      | NO_ENCONTRADO | -       | `-`                                |
|------------------|----------------|---------------|---------|------------------------------------|
| H7_rango_desplaz |       GPU      | NO_ENCONTRADO | -       | `-`                                |
| H7_rango_desplaz |       CPU      | NO_ENCONTRADO | -       | `-`                                |


## Análisis y conclusión

A partir de la batería de tests ejecutada, se pudo verificar que las implementaciones CPU y GPU resuelven correctamente el problema de búsqueda de nonces. En los casos donde existe una única solución relevante dentro del rango evaluado, ambas implementaciones coinciden en el nonce y en el hash resultante. Por ejemplo, para el prefijo `0000`, tanto CPU como GPU encontraron el nonce `34211`, generando el hash `00002f1daee5ee909f41a692ca31423f`. Lo mismo ocurrió para el prefijo `00000`, donde ambas implementaciones encontraron el nonce `3231929` y el hash `00000155f8105dff7f56ee10fa9b9abd`.

En los tests con prefijos cortos (`0`, `00` y `000`) CPU y GPU encontraron nonces distintos. Esto no representa un error, ya que para prefijos de baja dificultad existen muchas soluciones válidas. La CPU recorre los valores de forma secuencial y por eso encuentra el primer nonce válido en orden creciente. La GPU, en cambio, evalúa muchos candidatos en paralelo, por lo que puede registrar como solución un nonce distinto dependiendo de qué hilo finalice primero.

En cuanto al rendimiento, los resultados muestran dos comportamientos diferenciados. Para problemas pequeños, la CPU fue más rápida que la GPU. Por ejemplo, con prefijo `0000`, la GPU tardó `0.191360 s`, mientras que la CPU tardó `0.095170 s`, dando un speedup GPU de `0.50x`. Esto ocurre porque, en cargas pequeñas, el costo fijo de usar CUDA —lanzamiento del kernel, sincronización y transferencia de datos— pesa más que el beneficio del paralelismo.

Sin embargo, al aumentar la dificultad o el tamaño del rango, la ventaja de la GPU se vuelve evidente. En el test `H5_pref_00000`, la GPU resolvió la búsqueda en `0.194229 s`, mientras que la CPU tardó `3.882560 s`, logrando una aceleración de `19.99x`. En los tests con rango grande, aunque no se encontró solución, también se observa la diferencia de rendimiento: para `H7_rango_grande`, la GPU tardó `0.193468 s` contra `2.324114 s` de CPU, con una aceleración de `12.01x`; y para `H7_rango_desplaz`, la GPU tardó `0.198874 s` contra `4.578380 s`, alcanzando `23.02x`.

Estos resultados confirman que la dificultad del problema crece exponencialmente con la longitud del prefijo. Como cada carácter hexadecimal tiene 16 posibilidades, agregar un carácter al prefijo multiplica el trabajo esperado aproximadamente por 16:


```txt
intentos esperados = 16^longitud_prefijo
```
