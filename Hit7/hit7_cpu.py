import hashlib
import sys
import time


def calcular_md5(texto):
    """
    Calcula el hash MD5 de un texto.

    hashlib.md5 recibe bytes, por eso convertimos el string
    usando encode("utf-8").
    """
    texto_bytes = texto.encode("utf-8")
    return hashlib.md5(texto_bytes).hexdigest()


def prefijo_es_valido(prefijo):
    """
    Valida que el prefijo sea hexadecimal.

    Un hash MD5 se representa con 32 caracteres hexadecimales.
    Por eso el prefijo solo puede contener:
    - numeros del 0 al 9
    - letras de la a a la f
    """
    if len(prefijo) == 0 or len(prefijo) > 32:
        return False

    for caracter in prefijo:
        if caracter not in "0123456789abcdefABCDEF":
            return False

    return True


def buscar_en_rango(cadena_base, prefijo, inicio, fin):
    """
    Busca un nonce dentro del rango [inicio, fin].

    Para cada numero calcula:

        MD5(cadena_base + numero)

    Si el hash empieza con el prefijo pedido, devuelve:
    - numero encontrado
    - texto usado
    - hash resultante

    Si no encuentra nada, devuelve None.
    """
    for numero in range(inicio, fin + 1):
        texto = cadena_base + str(numero)
        hash_resultado = calcular_md5(texto)

        if hash_resultado.startswith(prefijo):
            return numero, texto, hash_resultado

    return None


def main():
    """
    Uso:

        python .\\Hit7\\hit7_cpu.py "abc" "0000" 0 100000
    """
    if len(sys.argv) != 5:
        print("Uso:")
        print('python .\\Hit7\\hit7_cpu.py "cadena_base" "prefijo_hash" inicio fin')
        print()
        print("Ejemplo:")
        print('python .\\Hit7\\hit7_cpu.py "abc" "0000" 0 100000')
        sys.exit(1)

    cadena_base = sys.argv[1]
    prefijo = sys.argv[2].lower()

    if not prefijo_es_valido(prefijo):
        print("Error: el prefijo debe ser hexadecimal y tener entre 1 y 32 caracteres.")
        print("Ejemplos validos: 0, 00, abc, 0000")
        sys.exit(1)

    try:
        inicio = int(sys.argv[3])
        fin = int(sys.argv[4])
    except ValueError:
        print("Error: inicio y fin deben ser numeros enteros.")
        sys.exit(1)

    if inicio < 0 or fin < 0:
        print("Error: inicio y fin deben ser numeros positivos.")
        sys.exit(1)

    if inicio > fin:
        print("Error: el inicio del rango no puede ser mayor que el fin.")
        sys.exit(1)

    print("Buscando nonce en rango usando CPU...")
    print("Cadena base:", cadena_base)
    print("Prefijo requerido:", prefijo)
    print(f"Rango: [{inicio}, {fin}]")

    tiempo_inicio = time.perf_counter()

    resultado = buscar_en_rango(
        cadena_base=cadena_base,
        prefijo=prefijo,
        inicio=inicio,
        fin=fin
    )

    tiempo_fin = time.perf_counter()
    tiempo_total = tiempo_fin - tiempo_inicio

    print()

    if resultado is None:
        intentos = fin - inicio + 1

        print("No se encontro solucion en el rango indicado.")
        print("Intentos realizados:", intentos)
        print("Tiempo:", round(tiempo_total, 6), "segundos")

        if tiempo_total > 0:
            velocidad = intentos / tiempo_total
            print("Velocidad:", round(velocidad, 2), "hashes/segundo")

        sys.exit(0)

    numero, texto_usado, hash_resultado = resultado

    intentos = numero - inicio + 1

    print("Solucion encontrada")
    print("Numero:", numero)
    print("Texto usado:", texto_usado)
    print("Hash:  ", hash_resultado)
    print("Intentos realizados:", intentos)
    print("Tiempo:", round(tiempo_total, 6), "segundos")

    if tiempo_total > 0:
        velocidad = intentos / tiempo_total
        print("Velocidad:", round(velocidad, 2), "hashes/segundo")


if __name__ == "__main__":
    main()