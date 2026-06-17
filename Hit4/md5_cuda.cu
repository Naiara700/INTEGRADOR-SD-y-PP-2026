#include <iostream>
#include <iomanip>
#include <string>

#include <thrust/host_vector.h>
#include <thrust/device_vector.h>

#include "md5.cuh"

using namespace std;

/*
    Kernel CUDA.

    esta es la funcion que se ejecuta en la GPU.

    Este kernel recibe:
    - texto: el mensaje que queremos hashear.
    - largo: la cantidad de caracteres del mensaje.
    - hash: arreglo donde se guarda el resultado MD5.

    La funcion cu_md5 pertenece a la libreria crypto-c.
    Esa funcion calcula el MD5 completo usando codigo CUDA.
*/
__global__ void calcularMD5(const char* texto, size_t largo, unsigned char* hash) {
    cu_md5(texto, largo, hash);
}

/*
    Imprime el MD5 en formato hexadecimal.

    MD5 siempre devuelve 16 bytes.
    Cada byte se muestra como 2 digitos hexadecimales.
*/
void imprimirMD5(const thrust::host_vector<unsigned char>& hash) {
    for (int i = 0; i < 16; i++) {
        cout << hex << setw(2) << setfill('0') << (int)hash[i];
    }

    cout << endl;
}

int main(int argc, char* argv[]) {
    /*
        Validamos que el usuario haya pasado un texto por parametro.

        Ejemplo:
        .\bin\md5_cuda.exe "hola"
    */
    if (argc != 2) {
        cout << "Uso:" << endl;
        cout << ".\\bin\\md5_cuda.exe \"texto\"" << endl;
        return 1;
    }

    /*
        Tomamos el texto recibido desde la consola.
    */
    string texto = argv[1];

    /*
        Copiamos el string a un vector de CPU usando Thrust.

        thrust::host_vector vive en memoria RAM normal.
    */
    thrust::host_vector<char> textoCPU(texto.begin(), texto.end());

    /*
        Copiamos el texto desde CPU a GPU.

        Esta linea reemplaza manualmente:
        - cudaMalloc
        - cudaMemcpy de CPU a GPU
    */
    thrust::device_vector<char> textoGPU = textoCPU;

    /*
        Reservamos 16 bytes en GPU para guardar el resultado MD5.

        MD5 = 128 bits = 16 bytes.
    */
    thrust::device_vector<unsigned char> hashGPU(16);

    /*
        Ejecutamos el kernel en la GPU.

        Usamos <<<1, 1>>> porque para este hit calculamos
        un solo MD5 de un solo texto.
    */
    calcularMD5<<<1, 1>>>(
        thrust::raw_pointer_cast(textoGPU.data()),
        texto.size(),
        thrust::raw_pointer_cast(hashGPU.data())
    );

    /*
        Esperamos a que la GPU termine antes de leer el resultado.
    */
    cudaDeviceSynchronize();

    /*
        Copiamos el hash desde GPU hacia CPU.

        Esta linea reemplaza cudaMemcpy de GPU a CPU.
    */
    thrust::host_vector<unsigned char> hashCPU = hashGPU;

    /*
        Mostramos el resultado por consola.
    */
    cout << "Texto: " << texto << endl;
    cout << "MD5:   ";
    imprimirMD5(hashCPU);

    return 0;
}