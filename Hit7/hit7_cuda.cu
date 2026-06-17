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
*/
__device__ char valorAHex(unsigned char valor) {
    if (valor < 10) {
        return '0' + valor;
    }

    return 'a' + (valor - 10);
}

/*
    Convierte un numero entero positivo a texto dentro de la GPU.

    Ejemplo:
        123 -> "123"

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
    Verifica si un hash MD5 comienza con el prefijo hexadecimal pedido.

    El hash MD5 tiene 16 bytes.
    Al imprimirse en hexadecimal se representa con 32 caracteres.
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
    Kernel CUDA del Hit #7.

    Cada hilo prueba un numero distinto dentro del rango indicado.

    Si un hilo calcula un nonce mayor al limite superior, termina sin hacer nada.
*/
__global__ void buscarNonceMD5EnRango(
    const char* cadenaBase,
    int largoCadenaBase,
    const char* prefijo,
    int largoPrefijo,
    unsigned long long inicioRango,
    unsigned long long finRango,
    int* encontrado,
    unsigned long long* numeroEncontrado,
    unsigned char* hashEncontrado
) {
    /*
        Si otro hilo ya encontro una solucion, este hilo no trabaja.
    */
    if (*encontrado == 1) {
        return;
    }

    /*
        Cada hilo calcula un numero diferente a probar.
    */
    unsigned long long idGlobal = blockIdx.x * blockDim.x + threadIdx.x;
    unsigned long long numero = inicioRango + idGlobal;

    /*
        Si el numero cae fuera del rango pedido, no se prueba.
    */
    if (numero > finRango) {
        return;
    }

    /*
        Armamos el texto:
            cadenaBase + numero

        Ejemplo:
            "abc" + 123 -> "abc123"
    */
    char texto[256];

    for (int i = 0; i < largoCadenaBase; i++) {
        texto[i] = cadenaBase[i];
    }

    int largoNumero = numeroATexto(numero, texto + largoCadenaBase);
    int largoTexto = largoCadenaBase + largoNumero;

    /*
        Calculamos el MD5 en GPU usando crypto-c.
    */
    unsigned char hash[16];

    cu_md5(texto, largoTexto, hash);

    /*
        Si cumple el prefijo, intentamos guardar la solucion.
    */
    if (hashEmpiezaCon(hash, prefijo, largoPrefijo)) {
        /*
            atomicCAS evita que varios hilos escriban al mismo tiempo.

            Solo el primer hilo que cambia encontrado de 0 a 1
            guarda el numero y el hash.
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
    Imprime los 16 bytes del MD5 en hexadecimal.
*/
void imprimirHash(const thrust::host_vector<unsigned char>& hash) {
    for (int i = 0; i < 16; i++) {
        cout << hex << setw(2) << setfill('0') << (int)hash[i];
    }

    cout << dec << endl;
}

/*
    Valida que el prefijo sea hexadecimal.

    Validos:
    - 0 a 9
    - a a f
    - A a F
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
        Parametros esperados:

        1. cadena base
        2. prefijo hexadecimal
        3. inicio del rango
        4. fin del rango

        Ejemplo:
        .\bin\hit7_cuda.exe "abc" "0000" 0 100000
    */
    if (argc != 5) {
        cout << "Uso:" << endl;
        cout << ".\\bin\\hit7_cuda.exe \"cadena_base\" \"prefijo_hash\" inicio fin" << endl;
        cout << endl;
        cout << "Ejemplo:" << endl;
        cout << ".\\bin\\hit7_cuda.exe \"abc\" \"0000\" 0 100000" << endl;
        return 1;
    }

    string cadenaBase = argv[1];
    string prefijo = argv[2];

    /*
        Convertimos el prefijo a minusculas para comparar contra el hash,
        que se trabaja en hexadecimal minuscula.
    */
    transform(prefijo.begin(), prefijo.end(), prefijo.begin(), ::tolower);

    if (!esPrefijoHexadecimal(prefijo)) {
        cout << "Error: el prefijo debe ser hexadecimal y tener entre 1 y 32 caracteres." << endl;
        cout << "Ejemplos validos: 0, 00, abc, 0000" << endl;
        return 1;
    }

    if (cadenaBase.size() > 200) {
        cout << "Error: la cadena base no debe superar 200 caracteres en esta version." << endl;
        return 1;
    }

    unsigned long long inicioRango;
    unsigned long long finRango;

    try {
        inicioRango = stoull(argv[3]);
        finRango = stoull(argv[4]);
    } catch (...) {
        cout << "Error: inicio y fin deben ser numeros enteros positivos." << endl;
        return 1;
    }

    if (inicioRango > finRango) {
        cout << "Error: el inicio del rango no puede ser mayor que el fin." << endl;
        return 1;
    }

    /*
        Copiamos cadena base y prefijo a GPU usando Thrust.
    */
    thrust::host_vector<char> cadenaCPU(cadenaBase.begin(), cadenaBase.end());
    thrust::host_vector<char> prefijoCPU(prefijo.begin(), prefijo.end());

    thrust::device_vector<char> cadenaGPU = cadenaCPU;
    thrust::device_vector<char> prefijoGPU = prefijoCPU;

    /*
        Variables de salida en GPU.
    */
    thrust::device_vector<int> encontradoGPU(1, 0);
    thrust::device_vector<unsigned long long> numeroGPU(1, 0);
    thrust::device_vector<unsigned char> hashGPU(16, 0);

    /*
        Configuracion CUDA.

        El rango se recorre en tandas.
        Cada tanda prueba bloques * hilosPorBloque numeros.
    */
    int hilosPorBloque = 256;
    int bloques = 256;

    unsigned long long intentosPorTanda =
        (unsigned long long)bloques * (unsigned long long)hilosPorBloque;

    unsigned long long inicioActual = inicioRango;

    cout << "Buscando nonce en rango..." << endl;
    cout << "Cadena base: " << cadenaBase << endl;
    cout << "Prefijo requerido: " << prefijo << endl;
    cout << "Rango: [" << inicioRango << ", " << finRango << "]" << endl;

    /*
        Recorremos el rango hasta:
        - encontrar una solucion
        - o superar finRango
    */
    while (inicioActual <= finRango) {
        buscarNonceMD5EnRango<<<bloques, hilosPorBloque>>>(
            thrust::raw_pointer_cast(cadenaGPU.data()),
            cadenaBase.size(),
            thrust::raw_pointer_cast(prefijoGPU.data()),
            prefijo.size(),
            inicioActual,
            finRango,
            thrust::raw_pointer_cast(encontradoGPU.data()),
            thrust::raw_pointer_cast(numeroGPU.data()),
            thrust::raw_pointer_cast(hashGPU.data())
        );

        cudaDeviceSynchronize();

        thrust::host_vector<int> encontradoCPU = encontradoGPU;

        if (encontradoCPU[0] == 1) {
            break;
        }

        /*
            Evitamos overflow y avanzamos a la siguiente tanda.
        */
        if (finRango - inicioActual < intentosPorTanda) {
            break;
        }

        inicioActual += intentosPorTanda;
    }

    /*
        Copiamos la bandera final para saber si encontro algo.
    */
    thrust::host_vector<int> encontradoCPU = encontradoGPU;

    if (encontradoCPU[0] == 0) {
        cout << endl;
        cout << "No se encontro solucion en el rango indicado." << endl;
        return 0;
    }

    /*
        Si encontro, copiamos numero y hash a CPU.
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