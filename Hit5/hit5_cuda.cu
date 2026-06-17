#include <iostream>
#include <iomanip>
#include <string>
#include <algorithm>

#include <thrust/host_vector.h>
#include <thrust/device_vector.h>

#include "md5.cuh"

using namespace std;

/*
    Convierte un valor entre 0 y 15 a su caracter hexadecimal.

    Ejemplos:
    0  -> '0'
    9  -> '9'
    10 -> 'a'
    15 -> 'f'
*/
__device__ char valorAHex(unsigned char valor) {
    if (valor < 10) {
        return '0' + valor;
    }

    return 'a' + (valor - 10);
}

/*
    Convierte un numero entero positivo a texto.

    Ejemplo:
    numero = 123
    salida = "123"

    Devuelve la cantidad de caracteres escritos.
*/
__device__ int numeroATexto(unsigned long long numero, char* salida) {
    char temporal[32];
    int cantidad = 0;

    if (numero == 0) {
        salida[0] = '0';
        return 1;
    }

    while (numero > 0) {
        temporal[cantidad] = '0' + (numero % 10);
        numero = numero / 10;
        cantidad++;
    }

    for (int i = 0; i < cantidad; i++) {
        salida[i] = temporal[cantidad - 1 - i];
    }

    return cantidad;
}

/*
    Verifica si el hash MD5 empieza con el prefijo pedido.

    El hash MD5 tiene 16 bytes.
    Al imprimirlo en hexadecimal se convierte en 32 caracteres.

    Ejemplo:
    hash bytes -> "900150983cd24fb0d6963f7d28e17f72"

    Si el prefijo es "9001", entonces coincide.
*/
__device__ bool hashEmpiezaCon(
    unsigned char* hash,
    const char* prefijo,
    int largoPrefijo
) {
    for (int i = 0; i < largoPrefijo; i++) {
        int indiceByte = i / 2;
        bool parteAlta = (i % 2 == 0);

        unsigned char byte = hash[indiceByte];
        unsigned char valorHex;

        if (parteAlta) {
            valorHex = (byte >> 4) & 0x0f;
        } else {
            valorHex = byte & 0x0f;
        }

        char caracterHex = valorAHex(valorHex);

        if (caracterHex != prefijo[i]) {
            return false;
        }
    }

    return true;
}

/*
    Kernel principal del Hit #5.

    Cada hilo prueba un numero distinto.

    Por ejemplo:
    - hilo 0 prueba cadena + 0
    - hilo 1 prueba cadena + 1
    - hilo 2 prueba cadena + 2
    - etc.

    Si encuentra un hash que empieza con el prefijo pedido,
    guarda:
    - el numero encontrado
    - el hash encontrado
    - una bandera indicando que ya se encontro solucion
*/
__global__ void buscarNonceMD5(
    const char* cadenaBase,
    int largoCadenaBase,
    const char* prefijo,
    int largoPrefijo,
    unsigned long long inicio,
    int* encontrado,
    unsigned long long* numeroEncontrado,
    unsigned char* hashEncontrado
) {
    /*
        Si otro hilo ya encontro una solucion, este hilo no hace nada.
    */
    if (*encontrado == 1) {
        return;
    }

    /*
        Calculamos el numero que le corresponde probar a este hilo.
    */
    unsigned long long idGlobal = blockIdx.x * blockDim.x + threadIdx.x;
    unsigned long long numero = inicio + idGlobal;

    /*
        Armamos el texto a hashear:
            cadenaBase + numero

        Ejemplo:
            cadenaBase = "abc"
            numero = 123

            texto = "abc123"
    */
    char texto[256];

    for (int i = 0; i < largoCadenaBase; i++) {
        texto[i] = cadenaBase[i];
    }

    int largoNumero = numeroATexto(numero, texto + largoCadenaBase);

    int largoTexto = largoCadenaBase + largoNumero;

    /*
        Calculamos MD5 usando la libreria crypto-c.

        Esta funcion se ejecuta dentro de la GPU.
    */
    unsigned char hash[16];

    cu_md5(texto, largoTexto, hash);

    /*
        Verificamos si el hash empieza con el prefijo pedido.
    */
    if (hashEmpiezaCon(hash, prefijo, largoPrefijo)) {

        /*
            atomicCAS evita que varios hilos escriban la solucion al mismo tiempo.

            Solo el primer hilo que cambia la variable "encontrado" de 0 a 1
            guarda el resultado final.
        */
        if (atomicCAS(encontrado, 0, 1) == 0) {
            *numeroEncontrado = numero;

            for (int i = 0; i < 16; i++) {
                hashEncontrado[i] = hash[i];
            }
        }
    }
}

/*
    Imprime un hash MD5 de 16 bytes en hexadecimal.
*/
void imprimirHash(const thrust::host_vector<unsigned char>& hash) {
    for (int i = 0; i < 16; i++) {
        cout << hex << setw(2) << setfill('0') << (int)hash[i];
    }

    cout << dec << endl;
}

/*
    Valida que el prefijo ingresado tenga solo caracteres hexadecimales.

    Caracteres validos:
    0-9
    a-f
    A-F
*/
bool esPrefijoHexadecimal(const string& prefijo) {
    if (prefijo.empty() || prefijo.size() > 32) {
        return false;
    }

    for (char c : prefijo) {
        bool esNumero = c >= '0' && c <= '9';
        bool esMinuscula = c >= 'a' && c <= 'f';
        bool esMayuscula = c >= 'A' && c <= 'F';

        if (!esNumero && !esMinuscula && !esMayuscula) {
            return false;
        }
    }

    return true;
}

int main(int argc, char* argv[]) {
    /*
        El programa recibe dos parametros:

        1. cadena base
        2. prefijo que debe tener el hash

        Ejemplo:
        .\bin\hit5_cuda.exe "abc" "0000"
    */
    if (argc != 3) {
        cout << "Uso:" << endl;
        cout << ".\\bin\\hit5_cuda.exe \"cadena_base\" \"prefijo_hash\"" << endl;
        return 1;
    }

    string cadenaBase = argv[1];
    string prefijo = argv[2];

    /*
        Pasamos el prefijo a minusculas porque el hash lo comparamos
        en hexadecimal minuscula.
    */
    transform(prefijo.begin(), prefijo.end(), prefijo.begin(), ::tolower);

    if (!esPrefijoHexadecimal(prefijo)) {
        cout << "Error: el prefijo debe ser hexadecimal y tener entre 1 y 32 caracteres." << endl;
        cout << "Ejemplos validos: 0, 00, abc, 0000, fffff" << endl;
        return 1;
    }

    if (cadenaBase.size() > 200) {
        cout << "Error: la cadena base no debe superar 200 caracteres en esta version." << endl;
        return 1;
    }

    /*
        Copiamos cadena base y prefijo desde CPU a GPU usando Thrust.
    */
    thrust::host_vector<char> cadenaCPU(cadenaBase.begin(), cadenaBase.end());
    thrust::host_vector<char> prefijoCPU(prefijo.begin(), prefijo.end());

    thrust::device_vector<char> cadenaGPU = cadenaCPU;
    thrust::device_vector<char> prefijoGPU = prefijoCPU;

    /*
        Variables de resultado.

        encontradoGPU:
        - 0 significa que todavia no se encontro solucion.
        - 1 significa que ya se encontro solucion.

        numeroGPU:
        - guarda el numero que genero el hash valido.

        hashGPU:
        - guarda el MD5 encontrado.
    */
    thrust::device_vector<int> encontradoGPU(1, 0);
    thrust::device_vector<unsigned long long> numeroGPU(1, 0);
    thrust::device_vector<unsigned char> hashGPU(16, 0);

    /*
        Configuracion CUDA.

        Cada tanda prueba:

            bloques * hilosPorBloque

        combinaciones.

        Con 256 bloques y 256 hilos, cada tanda prueba 65536 numeros.
    */
    int hilosPorBloque = 256;
    int bloques = 256;

    unsigned long long intentosPorTanda = hilosPorBloque * bloques;
    unsigned long long inicio = 0;

    cout << "Buscando nonce..." << endl;
    cout << "Cadena base: " << cadenaBase << endl;
    cout << "Prefijo requerido: " << prefijo << endl;

    /*
        Lanzamos tandas hasta encontrar una solucion.
    */
    while (true) {
        buscarNonceMD5<<<bloques, hilosPorBloque>>>(
            thrust::raw_pointer_cast(cadenaGPU.data()),
            cadenaBase.size(),
            thrust::raw_pointer_cast(prefijoGPU.data()),
            prefijo.size(),
            inicio,
            thrust::raw_pointer_cast(encontradoGPU.data()),
            thrust::raw_pointer_cast(numeroGPU.data()),
            thrust::raw_pointer_cast(hashGPU.data())
        );

        cudaDeviceSynchronize();

        /*
            Copiamos solo la bandera encontrado para saber si paramos.
        */
        thrust::host_vector<int> encontradoCPU = encontradoGPU;

        if (encontradoCPU[0] == 1) {
            break;
        }

        inicio += intentosPorTanda;

        /*
            Mensaje de avance cada varias tandas.
        */
        if (inicio % (intentosPorTanda * 100) == 0) {
            cout << "Intentos realizados: " << inicio << endl;
        }
    }

    /*
        Copiamos el resultado final desde GPU hacia CPU.
    */
    thrust::host_vector<unsigned long long> numeroCPU = numeroGPU;
    thrust::host_vector<unsigned char> hashCPU = hashGPU;

    cout << endl;
    cout << "Solucion encontrada" << endl;
    cout << "Numero: " << numeroCPU[0] << endl;
    cout << "Texto usado: " << cadenaBase << numeroCPU[0] << endl;
    cout << "Hash:   ";
    imprimirHash(hashCPU);

    return 0;
}