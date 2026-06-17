import hashlib
import sys
import time


def calcular_md5(texto):
    """
    Calcula el hash MD5 de un texto.

    hashlib.md5 necesita bytes, por eso convertimos el string
    usando encode("utf-8").
    """
    texto_bytes = texto.encode("utf-8")
    return hashlib.md5(texto_bytes).hexdigest()


def prefijo_es_valido(prefijo):
    """
    Valida que el prefijo ingresado sea hexadecimal.

    Un hash MD5 se muestra en hexadecimal, por eso solo tienen sentido
    caracteres entre:
    - 0 y 9
    - a y f
    - A y F
    """
    if len(prefijo) == 0 or len(prefijo) > 32:
        return False

    for caracter in prefijo:
        if caracter not in "0123456789abcdefABCDEF":
            return False

    return True


def buscar_numero(cadena_base, prefijo):
    """
    Busca por fuerza bruta un numero tal que:

        MD5(cadena_base + numero)

    empiece con el prefijo indicado.

    Esta es la version CPU/secuencial.
    Prueba los numeros de a uno: 0, 1, 2, 3, ...
    """
    numero = 0

    while True:
        texto = cadena_base + str(numero)
        hash_resultado = calcular_md5(texto)

        if hash_resultado.startswith(prefijo):
            return numero, texto, hash_resultado

        numero += 1


def main():
    """
    Programa principal.

    Uso:
        python Hit5/hit5_cpu.py "abc" "0000"
    """
    if len(sys.argv) != 3:
        print("Uso:")
        print('python Hit5/hit5_cpu.py "cadena_base" "prefijo_hash"')
        sys.exit(1)

    cadena_base = sys.argv[1]
    prefijo = sys.argv[2].lower()

    if not prefijo_es_valido(prefijo):
        print("Error: el prefijo debe ser hexadecimal y tener entre 1 y 32 caracteres.")
        print("Ejemplos validos: 0, 00, abc, 0000")
        sys.exit(1)

    print("Buscando nonce en CPU...")
    print("Cadena base:", cadena_base)
    print("Prefijo requerido:", prefijo)

    inicio = time.time()

    numero, texto_usado, hash_resultado = buscar_numero(cadena_base, prefijo)

    fin = time.time()
    tiempo_total = fin - inicio
    intentos = numero + 1

    print()
    print("Solucion encontrada")
    print("Numero:", numero)
    print("Texto usado:", texto_usado)
    print("Hash:  ", hash_resultado)
    print("Intentos:", intentos)
    print("Tiempo:", round(tiempo_total, 4), "segundos")

    if tiempo_total > 0:
        velocidad = intentos / tiempo_total
        print("Velocidad:", round(velocidad, 2), "hashes/segundo")


if __name__ == "__main__":
    main()