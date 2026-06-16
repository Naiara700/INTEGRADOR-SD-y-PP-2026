#include <thrust/host_vector.h>
#include <thrust/device_vector.h>
#include <thrust/generate.h>
#include <thrust/sort.h>
#include <thrust/copy.h>
#include <thrust/random.h>
#include <iostream>

int main() {
  // Generate 1M random numbers serially.
  thrust::default_random_engine rng(1337);
  thrust::uniform_int_distribution<int> dist;
  thrust::host_vector<int> h_vec(1 << 20);
  printf("Generando numeros...\n");
  thrust::generate(h_vec.begin(), h_vec.end(), [&] { return dist(rng); });

  // Transfer data to the device.
  printf("Copiando a GPU...\n");
  thrust::device_vector<int> d_vec = h_vec;

  // Sort data on the device.
  printf("Ordenando...\n");
  thrust::sort(d_vec.begin(), d_vec.end());

  // Transfer data back to host.
  printf("Copiando de vuelta a CPU...\n");
  thrust::copy(d_vec.begin(), d_vec.end(), h_vec.begin());

  printf("¡Proceso completado con exito!\n");
}