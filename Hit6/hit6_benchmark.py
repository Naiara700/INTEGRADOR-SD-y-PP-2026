import subprocess
import time
import csv
import re
import sys
from pathlib import Path


def extraer_numero(salida):
    """
    Extrae el numero encontrado desde la salida del programa.

    Busca una linea como:
        Numero: 34211
    """
    coincidencia = re.search(r"Numero:\s*(\d+)", salida)

    if coincidencia:
        return int(coincidencia.group(1))

    return None


def extraer_hash(salida):
    """
    Extrae el hash MD5 desde la salida del programa.

    Busca una linea como:
        Hash:   0000a3f5...
    """
    coincidencia = re.search(r"Hash:\s*([0-9a-fA-F]{32})", salida)

    if coincidencia:
        return coincidencia.group(1).lower()

    return None


def ejecutar_comando(comando):
    """
    Ejecuta un comando externo y mide cuanto tarda.

    Se usa tanto para:
    - GPU: .\\bin\\hit5_cuda.exe
    - CPU: python .\\Hit5\\hit5_cpu.py
    """
    inicio = time.perf_counter()

    proceso = subprocess.run(
        comando,
        capture_output=True,
        text=True
    )

    fin = time.perf_counter()

    tiempo = fin - inicio

    return proceso.returncode, proceso.stdout, proceso.stderr, tiempo


def ejecutar_prueba(nombre, comando, prefijo):
    """
    Ejecuta una prueba individual.

    nombre:
        CPU o GPU

    comando:
        lista con el comando completo a ejecutar

    prefijo:
        prefijo usado en esta prueba, por ejemplo "0000"
    """
    returncode, salida, error, tiempo = ejecutar_comando(comando)

    if returncode != 0:
        return {
            "implementacion": nombre,
            "longitud": len(prefijo),
            "prefijo": prefijo,
            "numero": None,
            "hash": None,
            "intentos": None,
            "tiempo": tiempo,
            "hashes_por_segundo": None,
            "estado": "ERROR",
            "salida": salida,
            "error": error
        }

    numero = extraer_numero(salida)
    hash_resultado = extraer_hash(salida)

    if numero is None or hash_resultado is None:
        return {
            "implementacion": nombre,
            "longitud": len(prefijo),
            "prefijo": prefijo,
            "numero": None,
            "hash": None,
            "intentos": None,
            "tiempo": tiempo,
            "hashes_por_segundo": None,
            "estado": "NO_PARSEADO",
            "salida": salida,
            "error": error
        }

    intentos = numero + 1

    if tiempo > 0:
        hashes_por_segundo = intentos / tiempo
    else:
        hashes_por_segundo = 0

    return {
        "implementacion": nombre,
        "longitud": len(prefijo),
        "prefijo": prefijo,
        "numero": numero,
        "hash": hash_resultado,
        "intentos": intentos,
        "tiempo": tiempo,
        "hashes_por_segundo": hashes_por_segundo,
        "estado": "OK",
        "salida": salida,
        "error": error
    }


def guardar_csv(resultados, ruta_csv):
    """
    Guarda todos los resultados en CSV.
    """
    campos = [
        "implementacion",
        "longitud",
        "prefijo",
        "numero",
        "hash",
        "intentos",
        "tiempo_segundos",
        "hashes_por_segundo",
        "estado"
    ]

    with open(ruta_csv, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()

        for r in resultados:
            escritor.writerow({
                "implementacion": r["implementacion"],
                "longitud": r["longitud"],
                "prefijo": r["prefijo"],
                "numero": r["numero"],
                "hash": r["hash"],
                "intentos": r["intentos"],
                "tiempo_segundos": round(r["tiempo"], 6),
                "hashes_por_segundo": round(r["hashes_por_segundo"], 2) if r["hashes_por_segundo"] else None,
                "estado": r["estado"]
            })


def obtener_resultado(resultados, implementacion, longitud):
    """
    Busca un resultado especifico por implementacion y longitud de prefijo.
    """
    for r in resultados:
        if r["implementacion"] == implementacion and r["longitud"] == longitud:
            return r

    return None


def guardar_informe(resultados, ruta_informe, cadena_base, longitud_maxima):
    """
    Genera un informe Markdown comparando CPU y GPU.
    """
    with open(ruta_informe, "w", encoding="utf-8") as archivo:
        archivo.write("# Hit #6 - Longitudes de prefijo en CUDA HASH\n\n")

        archivo.write("## Objetivo\n\n")
        archivo.write(
            "Medir el tiempo requerido para encontrar un nonce valido usando "
            "diferentes longitudes de prefijo, comparando la implementacion GPU CUDA "
            "contra la implementacion CPU en Python.\n\n"
        )

        archivo.write("## Configuracion de la prueba\n\n")
        archivo.write(f"- Cadena base utilizada: `{cadena_base}`\n")
        archivo.write("- Implementacion GPU: `bin/hit5_cuda.exe`\n")
        archivo.write("- Implementacion CPU: `Hit5/hit5_cpu.py`\n")
        archivo.write("- Hash utilizado: MD5\n")
        archivo.write("- Metodo de medicion: script Python con `subprocess` y `time.perf_counter()`\n")
        archivo.write(f"- Longitud maxima probada: {longitud_maxima}\n\n")

        archivo.write("## Resultados comparativos\n\n")
        archivo.write(
            "| Longitud | Prefijo | Numero GPU | Tiempo GPU (s) | Hashes/s GPU | "
            "Numero CPU | Tiempo CPU (s) | Hashes/s CPU | Aceleracion GPU vs CPU |\n"
        )
        archivo.write("|---:|---|---:|---:|---:|---:|---:|---:|---:|\n")

        for longitud in range(1, longitud_maxima + 1):
            gpu = obtener_resultado(resultados, "GPU", longitud)
            cpu = obtener_resultado(resultados, "CPU", longitud)

            prefijo = "0" * longitud

            if gpu and cpu and gpu["estado"] == "OK" and cpu["estado"] == "OK":
                if gpu["tiempo"] > 0:
                    aceleracion = cpu["tiempo"] / gpu["tiempo"]
                else:
                    aceleracion = 0

                archivo.write(
                    f"| {longitud} "
                    f"| `{prefijo}` "
                    f"| {gpu['numero']} "
                    f"| {gpu['tiempo']:.6f} "
                    f"| {gpu['hashes_por_segundo']:.2f} "
                    f"| {cpu['numero']} "
                    f"| {cpu['tiempo']:.6f} "
                    f"| {cpu['hashes_por_segundo']:.2f} "
                    f"| {aceleracion:.2f}x |\n"
                )
            else:
                gpu_estado = gpu["estado"] if gpu else "SIN_DATO"
                cpu_estado = cpu["estado"] if cpu else "SIN_DATO"

                archivo.write(
                    f"| {longitud} "
                    f"| `{prefijo}` "
                    f"| {gpu_estado} "
                    f"| - "
                    f"| - "
                    f"| {cpu_estado} "
                    f"| - "
                    f"| - "
                    f"| - |\n"
                )

        archivo.write("\n## Detalle de hashes encontrados\n\n")
        archivo.write("| Implementacion | Longitud | Prefijo | Numero | Texto usado | Hash |\n")
        archivo.write("|---|---:|---|---:|---|---|\n")

        for r in resultados:
            if r["estado"] == "OK":
                archivo.write(
                    f"| {r['implementacion']} "
                    f"| {r['longitud']} "
                    f"| `{r['prefijo']}` "
                    f"| {r['numero']} "
                    f"| `{cadena_base}{r['numero']}` "
                    f"| `{r['hash']}` |\n"
                )

        archivo.write("\n## Analisis\n\n")
        archivo.write(
            "La dificultad aumenta exponencialmente con la longitud del prefijo. "
            "Como el hash MD5 se representa en hexadecimal, cada caracter del prefijo "
            "puede tomar 16 valores posibles. Por eso, la probabilidad aproximada de "
            "que un hash cumpla un prefijo de longitud `n` es:\n\n"
        )

        archivo.write("```txt\n")
        archivo.write("1 / 16^n\n")
        archivo.write("```\n\n")

        archivo.write(
            "Por lo tanto, el numero esperado de intentos para encontrar una solucion es:\n\n"
        )

        archivo.write("```txt\n")
        archivo.write("16^n\n")
        archivo.write("```\n\n")

        archivo.write(
            "Esto implica que cada caracter hexadecimal adicional en el prefijo multiplica "
            "el trabajo esperado aproximadamente por 16. En la practica, los tiempos no "
            "crecen de forma perfectamente regular porque la busqueda depende de la posicion "
            "en la que aparece el primer hash valido.\n\n"
        )

        resultados_gpu_ok = [
            r for r in resultados
            if r["implementacion"] == "GPU" and r["estado"] == "OK"
        ]

        resultados_cpu_ok = [
            r for r in resultados
            if r["implementacion"] == "CPU" and r["estado"] == "OK"
        ]

        if resultados_gpu_ok:
            mayor_gpu = resultados_gpu_ok[-1]
            archivo.write("## Prefijo mas largo encontrado en GPU\n\n")
            archivo.write(f"- Prefijo: `{mayor_gpu['prefijo']}`\n")
            archivo.write(f"- Longitud: {mayor_gpu['longitud']}\n")
            archivo.write(f"- Numero: {mayor_gpu['numero']}\n")
            archivo.write(f"- Texto usado: `{cadena_base}{mayor_gpu['numero']}`\n")
            archivo.write(f"- Hash: `{mayor_gpu['hash']}`\n")
            archivo.write(f"- Tiempo: {mayor_gpu['tiempo']:.6f} segundos\n\n")

        if resultados_cpu_ok:
            mayor_cpu = resultados_cpu_ok[-1]
            archivo.write("## Prefijo mas largo encontrado en CPU\n\n")
            archivo.write(f"- Prefijo: `{mayor_cpu['prefijo']}`\n")
            archivo.write(f"- Longitud: {mayor_cpu['longitud']}\n")
            archivo.write(f"- Numero: {mayor_cpu['numero']}\n")
            archivo.write(f"- Texto usado: `{cadena_base}{mayor_cpu['numero']}`\n")
            archivo.write(f"- Hash: `{mayor_cpu['hash']}`\n")
            archivo.write(f"- Tiempo: {mayor_cpu['tiempo']:.6f} segundos\n")


def imprimir_tabla_comparativa(resultados, longitud_maxima):
    """
    Imprime una tabla comparativa en consola.
    """
    print()
    print("Resultados comparativos Hit #6")
    print("-" * 125)
    print(
        f"{'Long.':<8} "
        f"{'Prefijo':<10} "
        f"{'GPU tiempo':<14} "
        f"{'CPU tiempo':<14} "
        f"{'Speedup':<10} "
        f"{'GPU nonce':<14} "
        f"{'CPU nonce':<14} "
        f"{'Hash GPU'}"
    )
    print("-" * 125)

    for longitud in range(1, longitud_maxima + 1):
        gpu = obtener_resultado(resultados, "GPU", longitud)
        cpu = obtener_resultado(resultados, "CPU", longitud)

        prefijo = "0" * longitud

        if gpu and cpu and gpu["estado"] == "OK" and cpu["estado"] == "OK":
            speedup = cpu["tiempo"] / gpu["tiempo"] if gpu["tiempo"] > 0 else 0

            print(
                f"{longitud:<8} "
                f"{prefijo:<10} "
                f"{gpu['tiempo']:<14.6f} "
                f"{cpu['tiempo']:<14.6f} "
                f"{speedup:<10.2f} "
                f"{gpu['numero']:<14} "
                f"{cpu['numero']:<14} "
                f"{gpu['hash']}"
            )
        else:
            gpu_estado = gpu["estado"] if gpu else "SIN_DATO"
            cpu_estado = cpu["estado"] if cpu else "SIN_DATO"

            print(
                f"{longitud:<8} "
                f"{prefijo:<10} "
                f"{gpu_estado:<14} "
                f"{cpu_estado:<14}"
            )

    print("-" * 125)


def main():
    """
    Uso:

        python .\\Hit6\\hit6_benchmark.py "abc" 5

    Ejecuta GPU y CPU para:
        0
        00
        000
        0000
        00000
    """
    if len(sys.argv) != 3:
        print("Uso:")
        print('python .\\Hit6\\hit6_benchmark.py "cadena_base" longitud_maxima')
        print()
        print("Ejemplo:")
        print('python .\\Hit6\\hit6_benchmark.py "abc" 5')
        sys.exit(1)

    cadena_base = sys.argv[1]
    longitud_maxima = int(sys.argv[2])

    if longitud_maxima < 1 or longitud_maxima > 32:
        print("Error: la longitud maxima debe estar entre 1 y 32.")
        sys.exit(1)

    raiz_proyecto = Path(__file__).resolve().parent.parent

    ejecutable_gpu = raiz_proyecto / "bin" / "hit5_cuda.exe"
    script_cpu = raiz_proyecto / "Hit5" / "hit5_cpu.py"

    if not ejecutable_gpu.exists():
        print("Error: no se encontro el ejecutable GPU:")
        print(ejecutable_gpu)
        print()
        print("Primero compila el Hit #5 para generar bin\\hit5_cuda.exe")
        sys.exit(1)

    if not script_cpu.exists():
        print("Error: no se encontro el script CPU:")
        print(script_cpu)
        print()
        print("Primero crea Hit5\\hit5_cpu.py")
        sys.exit(1)

    carpeta_hit6 = raiz_proyecto / "Hit6"
    ruta_csv = carpeta_hit6 / "resultados_hit6_cpu_gpu.csv"
    ruta_informe = carpeta_hit6 / "informe_hit6_cpu_gpu.md"

    resultados = []

    print("Benchmark Hit #6 CPU vs GPU")
    print("Cadena base:", cadena_base)
    print("Longitud maxima:", longitud_maxima)
    print("GPU:", ejecutable_gpu)
    print("CPU:", script_cpu)
    print()

    for longitud in range(1, longitud_maxima + 1):
        prefijo = "0" * longitud

        print(f"Ejecutando GPU con prefijo '{prefijo}'...")

        comando_gpu = [
            str(ejecutable_gpu),
            cadena_base,
            prefijo
        ]

        resultado_gpu = ejecutar_prueba(
            nombre="GPU",
            comando=comando_gpu,
            prefijo=prefijo
        )

        resultados.append(resultado_gpu)

        if resultado_gpu["estado"] != "OK":
            print("Fallo la prueba GPU.")
            print("Estado:", resultado_gpu["estado"])
            print("Salida:")
            print(resultado_gpu["salida"])
            print("Error:")
            print(resultado_gpu["error"])
            break

        print(f"Ejecutando CPU con prefijo '{prefijo}'...")

        comando_cpu = [
            sys.executable,
            str(script_cpu),
            cadena_base,
            prefijo
        ]

        resultado_cpu = ejecutar_prueba(
            nombre="CPU",
            comando=comando_cpu,
            prefijo=prefijo
        )

        resultados.append(resultado_cpu)

        if resultado_cpu["estado"] != "OK":
            print("Fallo la prueba CPU.")
            print("Estado:", resultado_cpu["estado"])
            print("Salida:")
            print(resultado_cpu["salida"])
            print("Error:")
            print(resultado_cpu["error"])
            break

    imprimir_tabla_comparativa(resultados, longitud_maxima)

    guardar_csv(resultados, ruta_csv)
    guardar_informe(resultados, ruta_informe, cadena_base, longitud_maxima)

    print()
    print("Archivos generados:")
    print(ruta_csv)
    print(ruta_informe)


if __name__ == "__main__":
    main()