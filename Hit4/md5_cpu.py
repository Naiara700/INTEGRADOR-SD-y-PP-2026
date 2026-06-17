import hashlib
import sys

# Validamos que el usuario haya pasado un texto por parametro.
#
# Ejemplo:
# python Hit4/md5_cpu.py "abc"

if len(sys.argv) != 2:
    print("Uso:")
    print('python Hit4/md5_cpu.py "texto"')
    sys.exit(1)

# Tomamos el texto recibido por consola.
texto = sys.argv[1]

# Convertimos el texto a bytes.
# MD5 trabaja sobre bytes, no directamente sobre strings.
texto_bytes = texto.encode("utf-8")

# Calculamos el MD5 usando hashlib, que es una libreria estandar de Python.
hash_md5 = hashlib.md5(texto_bytes).hexdigest()

# Mostramos el resultado.
print("Texto:", texto)
print("MD5:  ", hash_md5)