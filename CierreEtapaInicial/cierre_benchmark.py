import subprocess
import time
import re
import sys
from pathlib import Path


def ejecutar_comando(comando):
    """
    Ejecuta un comando externo y mide el tiempo real de ejecucion.
    """
    inicio = time.perf_counter()

    proceso = subprocess.run(
        comando,
        capture_output=True,
        text=True
    )

    fin = time.perf_counter()

    return {
        "returncode": proceso.returncode,
        "stdout": proceso.stdout,
        "stderr": proceso.stderr,
        "tiempo": fin - inicio
    }


def extraer_numero(salida):
    """
    Extrae una linea del tipo:
        Numero: 12345
    """
    match = re.search(r"Numero:\s*(\d+)", salida)

    if match:
        return int(match.group(1))

    return None


def extraer_hash(salida):
    """
    Extrae una linea del tipo:
        Hash:   0000abc...
    """
    match = re.search(r"Hash:\s*([0-9a-fA-F]{32})", salida)

    if match:
        return match.group(1).lower()

    return None


def se_encontro_solucion(salida):
    """
    Detecta si el programa encontro solucion.
    """
    return "Solucion encontrada" in salida


def no_se_encontro_solucion(salida):
    """
    Detecta si el programa informo que no encontro solucion.
    """
    return "No se encontro solucion" in salida


def ejecutar_test(nombre_test, tipo_hit, implementacion, comando):
    """
    Ejecuta un test individual y devuelve la informacion normalizada.
    """
    resultado = ejecutar_comando(comando)

    salida = resultado["stdout"]
    error = resultado["stderr"]
    tiempo = resultado["tiempo"]

    numero = extraer_numero(salida)
    hash_resultado = extraer_hash(salida)

    if resultado["returncode"] != 0:
        estado = "ERROR"
    elif se_encontro_solucion(salida):
        estado = "ENCONTRADO"
    elif no_se_encontro_solucion(salida):
        estado = "NO_ENCONTRADO"
    else:
        estado = "NO_PARSEADO"

    return {
        "test": nombre_test,
        "hit": tipo_hit,
        "implementacion": implementacion,
        "estado": estado,
        "numero": numero,
        "hash": hash_resultado,
        "tiempo": tiempo,
        "stdout": salida,
        "stderr": error
    }


def obtener_resultado(resultados, nombre_test, implementacion):
    """
    Busca un resultado puntual por nombre de test e implementacion.
    """
    for r in resultados:
        if r["test"] == nombre_test and r["implementacion"] == implementacion:
            return r

    return None


def calcular_speedup(cpu, gpu):
    """
    Calcula cuantas veces mas rapida fue la GPU respecto de CPU.
    """
    if cpu is None or gpu is None:
        return None

    if gpu["tiempo"] <= 0:
        return None

    return cpu["tiempo"] / gpu["tiempo"]


def hashes_coinciden(cpu, gpu):
    """
    Verifica si CPU y GPU devolvieron el mismo hash.
    """
    if cpu is None or gpu is None:
        return False

    if cpu["hash"] is None or gpu["hash"] is None:
        return cpu["estado"] == gpu["estado"]

    return cpu["hash"] == gpu["hash"]


def numeros_coinciden(cpu, gpu):
    """
    Verifica si CPU y GPU devolvieron el mismo nonce.

    Como nuestras implementaciones prueban en orden creciente,
    deberian encontrar el mismo numero.
    """
    if cpu is None or gpu is None:
        return False

    return cpu["numero"] == gpu["numero"]


def guardar_informe(resultados, tests, ruta_informe):
    """
    Genera un informe Markdown listo para incorporar al trabajo.
    """
    with open(ruta_informe, "w", encoding="utf-8") as archivo:
        archivo.write("# Cierre etapa inicial - Comparativa CPU vs GPU\n\n")

        archivo.write("## Objetivo\n\n")
        archivo.write(
            "Se ejecuto una bateria de tests sobre las implementaciones CPU y GPU "
            "desarrolladas en los hits anteriores. El objetivo fue verificar que ambas "
            "implementaciones produzcan resultados equivalentes y comparar sus tiempos "
            "de ejecucion.\n\n"
        )

        archivo.write("## Implementaciones comparadas\n\n")
        archivo.write("- GPU CUDA Hit #5: `bin/hit5_cuda.exe`\n")
        archivo.write("- CPU Python Hit #5: `Hit5/hit5_cpu.py`\n")
        archivo.write("- GPU CUDA Hit #7: `bin/hit7_cuda.exe`\n")
        archivo.write("- CPU Python Hit #7: `Hit7/hit7_cpu.py`\n\n")

        archivo.write("## Bateria de tests utilizada\n\n")
        archivo.write("| Test | Hit | Parametros |\n")
        archivo.write("|---|---|---|\n")

        for test in tests:
            archivo.write(
                f"| {test['nombre']} "
                f"| {test['hit']} "
                f"| `{test['descripcion']}` |\n"
            )

        archivo.write("\n## Resultados comparativos\n\n")
        archivo.write(
            "| Test | Hit | Estado GPU | Tiempo GPU (s) | Nonce GPU | "
            "Estado CPU | Tiempo CPU (s) | Nonce CPU | Coinciden | Speedup GPU |\n"
        )
        archivo.write("|---|---|---|---:|---:|---|---:|---:|---|---:|\n")

        for test in tests:
            nombre = test["nombre"]

            gpu = obtener_resultado(resultados, nombre, "GPU")
            cpu = obtener_resultado(resultados, nombre, "CPU")

            if gpu is None or cpu is None:
                continue

            speedup = calcular_speedup(cpu, gpu)

            coinciden = (
                gpu["estado"] == cpu["estado"]
                and hashes_coinciden(cpu, gpu)
                and numeros_coinciden(cpu, gpu)
            )

            speedup_texto = f"{speedup:.2f}x" if speedup is not None else "-"

            archivo.write(
                f"| {nombre} "
                f"| {test['hit']} "
                f"| {gpu['estado']} "
                f"| {gpu['tiempo']:.6f} "
                f"| {gpu['numero'] if gpu['numero'] is not None else '-'} "
                f"| {cpu['estado']} "
                f"| {cpu['tiempo']:.6f} "
                f"| {cpu['numero'] if cpu['numero'] is not None else '-'} "
                f"| {'Si' if coinciden else 'No'} "
                f"| {speedup_texto} |\n"
            )

        archivo.write("\n## Detalle de hashes encontrados\n\n")
        archivo.write("| Test | Implementacion | Estado | Nonce | Hash |\n")
        archivo.write("|---|---|---|---:|---|\n")

        for r in resultados:
            archivo.write(
                f"| {r['test']} "
                f"| {r['implementacion']} "
                f"| {r['estado']} "
                f"| {r['numero'] if r['numero'] is not None else '-'} "
                f"| `{r['hash'] if r['hash'] is not None else '-'}` |\n"
            )

        archivo.write("\n## Analisis\n\n")
        archivo.write(
            "Los tests permiten observar que la implementacion GPU y la implementacion CPU "
            "resuelven el mismo problema: buscar un nonce tal que el hash MD5 de la cadena "
            "base concatenada con dicho nonce comience con un prefijo determinado.\n\n"
        )

        archivo.write(
            "Para prefijos cortos, la diferencia entre CPU y GPU puede ser pequena o incluso "
            "favorable a CPU, debido al costo fijo de lanzar kernels CUDA y transferir datos. "
            "A medida que aumenta la dificultad, la GPU tiende a mostrar mejores tiempos porque "
            "evalua muchos nonces en paralelo.\n\n"
        )

        archivo.write(
            "La dificultad crece exponencialmente con la longitud del prefijo. Como cada "
            "caracter hexadecimal tiene 16 posibilidades, agregar un caracter al prefijo "
            "multiplica el trabajo esperado aproximadamente por 16.\n\n"
        )

        archivo.write("```txt\n")
        archivo.write("intentos esperados = 16^longitud_prefijo\n")
        archivo.write("```\n\n")

        archivo.write(
            "En los tests con limites de rango, ademas de verificar tiempos, se comprueba "
            "que el programa informa correctamente cuando no existe una solucion dentro "
            "del intervalo indicado.\n"
        )


def imprimir_tabla(resultados, tests):
    """
    Imprime una tabla comparativa resumida por consola.
    """
    print()
    print("Comparativa CPU vs GPU")
    print("-" * 130)
    print(
        f"{'Test':<16} "
        f"{'Hit':<8} "
        f"{'GPU estado':<14} "
        f"{'GPU tiempo':<14} "
        f"{'CPU estado':<14} "
        f"{'CPU tiempo':<14} "
        f"{'Coinciden':<12} "
        f"{'Speedup':<10}"
    )
    print("-" * 130)

    for test in tests:
        nombre = test["nombre"]

        gpu = obtener_resultado(resultados, nombre, "GPU")
        cpu = obtener_resultado(resultados, nombre, "CPU")

        if gpu is None or cpu is None:
            continue

        speedup = calcular_speedup(cpu, gpu)

        coinciden = (
            gpu["estado"] == cpu["estado"]
            and hashes_coinciden(cpu, gpu)
            and numeros_coinciden(cpu, gpu)
        )

        print(
            f"{nombre:<16} "
            f"{test['hit']:<8} "
            f"{gpu['estado']:<14} "
            f"{gpu['tiempo']:<14.6f} "
            f"{cpu['estado']:<14} "
            f"{cpu['tiempo']:<14.6f} "
            f"{'SI' if coinciden else 'NO':<12} "
            f"{f'{speedup:.2f}x' if speedup is not None else '-':<10}"
        )

    print("-" * 130)


def main():
    """
    Ejecuta una bateria de tests sobre CPU y GPU.

    Uso:
        python .\\CierreEtapaInicial\\cierre_benchmark.py
    """
    raiz = Path(__file__).resolve().parent.parent

    gpu_hit5 = raiz / "bin" / "hit5_cuda.exe"
    gpu_hit7 = raiz / "bin" / "hit7_cuda.exe"

    cpu_hit5 = raiz / "Hit5" / "hit5_cpu.py"
    cpu_hit7 = raiz / "Hit7" / "hit7_cpu.py"

    faltantes = []

    for archivo in [gpu_hit5, gpu_hit7, cpu_hit5, cpu_hit7]:
        if not archivo.exists():
            faltantes.append(archivo)

    if faltantes:
        print("Faltan archivos necesarios:")
        for archivo in faltantes:
            print("-", archivo)

        print()
        print("Antes de ejecutar este benchmark, compila Hit5 e Hit7 CUDA")
        print("y verifica que existan los scripts CPU.")
        sys.exit(1)

    tests = [
        {
            "nombre": "H5_pref_0",
            "hit": "Hit5",
            "descripcion": 'cadena="abc", prefijo="0"',
            "gpu": [str(gpu_hit5), "abc", "0"],
            "cpu": [sys.executable, str(cpu_hit5), "abc", "0"]
        },
        {
            "nombre": "H5_pref_00",
            "hit": "Hit5",
            "descripcion": 'cadena="abc", prefijo="00"',
            "gpu": [str(gpu_hit5), "abc", "00"],
            "cpu": [sys.executable, str(cpu_hit5), "abc", "00"]
        },
        {
            "nombre": "H5_pref_000",
            "hit": "Hit5",
            "descripcion": 'cadena="abc", prefijo="000"',
            "gpu": [str(gpu_hit5), "abc", "000"],
            "cpu": [sys.executable, str(cpu_hit5), "abc", "000"]
        },
        {
            "nombre": "H5_pref_0000",
            "hit": "Hit5",
            "descripcion": 'cadena="abc", prefijo="0000"',
            "gpu": [str(gpu_hit5), "abc", "0000"],
            "cpu": [sys.executable, str(cpu_hit5), "abc", "0000"]
        },

        # Test mas pesado.
        # Con 5 ceros, el numero esperado de intentos ronda 16^5 = 1.048.576.
        # Este caso deberia mostrar mejor la ventaja de GPU.
        {
            "nombre": "H5_pref_00000",
            "hit": "Hit5",
            "descripcion": 'cadena="abc", prefijo="00000"',
            "gpu": [str(gpu_hit5), "abc", "00000"],
            "cpu": [sys.executable, str(cpu_hit5), "abc", "00000"]
        },

        {
            "nombre": "H7_rango_chico",
            "hit": "Hit7",
            "descripcion": 'cadena="abc", prefijo="0000", rango=[0,1000]',
            "gpu": [str(gpu_hit7), "abc", "0000", "0", "1000"],
            "cpu": [sys.executable, str(cpu_hit7), "abc", "0000", "0", "1000"]
        },
        {
            "nombre": "H7_rango_medio",
            "hit": "Hit7",
            "descripcion": 'cadena="abc", prefijo="0000", rango=[0,100000]',
            "gpu": [str(gpu_hit7), "abc", "0000", "0", "100000"],
            "cpu": [sys.executable, str(cpu_hit7), "abc", "0000", "0", "100000"]
        },
        {
            "nombre": "H7_rango_partido",
            "hit": "Hit7",
            "descripcion": 'cadena="abc", prefijo="0000", rango=[1001,100000]',
            "gpu": [str(gpu_hit7), "abc", "0000", "1001", "100000"],
            "cpu": [sys.executable, str(cpu_hit7), "abc", "0000", "1001", "100000"]
        },

        # Test pesado con rango.
        # Busca dentro de un rango mucho mas grande.
        # Sirve para observar mejor el comportamiento cuando hay mas nonces para evaluar.
        {
            "nombre": "H7_rango_grande",
            "hit": "Hit7",
            "descripcion": 'cadena="abc", prefijo="00000", rango=[0,2000000]',
            "gpu": [str(gpu_hit7), "abc", "00000", "0", "2000000"],
            "cpu": [sys.executable, str(cpu_hit7), "abc", "00000", "0", "2000000"]
        },

        # Test con rango desplazado.
        # Evita comenzar desde cero y obliga a buscar dentro de una zona mas avanzada.
        {
            "nombre": "H7_rango_desplaz",
            "hit": "Hit7",
            "descripcion": 'cadena="abc", prefijo="00000", rango=[500000,3000000]',
            "gpu": [str(gpu_hit7), "abc", "00000", "500000", "3000000"],
            "cpu": [sys.executable, str(cpu_hit7), "abc", "00000", "500000", "3000000"]
        }
    ]

    resultados = []

    print("Ejecutando cierre de etapa inicial...")
    print()

    for test in tests:
        print(f"Ejecutando {test['nombre']} en GPU...")
        resultado_gpu = ejecutar_test(
            nombre_test=test["nombre"],
            tipo_hit=test["hit"],
            implementacion="GPU",
            comando=test["gpu"]
        )
        resultados.append(resultado_gpu)

        print(f"Ejecutando {test['nombre']} en CPU...")
        resultado_cpu = ejecutar_test(
            nombre_test=test["nombre"],
            tipo_hit=test["hit"],
            implementacion="CPU",
            comando=test["cpu"]
        )
        resultados.append(resultado_cpu)

    imprimir_tabla(resultados, tests)

    carpeta_salida = raiz / "CierreEtapaInicial"
    ruta_informe = carpeta_salida / "informe_cierre_etapa_inicial.md"

    guardar_informe(resultados, tests, ruta_informe)

    print()
    print("Archivo generado:")
    print(ruta_informe)


if __name__ == "__main__":
    main()