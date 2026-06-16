#include <thrust/host_vector.h>
#include <thrust/device_vector.h>
#include <thrust/generate.h>
#include <thrust/sort.h>
#include <thrust/copy.h>
#include <thrust/random.h>
#include <stdio.h>

int main() {
  thrust::default_random_engine rng(1337);
  thrust::uniform_int_distribution<int> dist;
  thrust::host_vector<int> h_vec(1 << 20);
  thrust::generate(h_vec.begin(), h_vec.end(), [&] { return dist(rng); });

  // Verificar que NO está ordenado antes
  printf("Antes del sort - primeros 5: %d %d %d %d %d\n",
    h_vec[0], h_vec[1], h_vec[2], h_vec[3], h_vec[4]);

  thrust::device_vector<int> d_vec = h_vec;
  thrust::sort(d_vec.begin(), d_vec.end());
  thrust::copy(d_vec.begin(), d_vec.end(), h_vec.begin());

  // Verificar que SÍ está ordenado después
  printf("Despues del sort - primeros 5: %d %d %d %d %d\n",
    h_vec[0], h_vec[1], h_vec[2], h_vec[3], h_vec[4]);

  // Confirmar que está ordenado
  bool sorted = true;
  for (int i = 1; i < 100; i++) {
    if (h_vec[i] < h_vec[i-1]) { sorted = false; break; }
  }
  printf("¿Vector ordenado correctamente? %s\n", sorted ? "SI" : "NO");
}