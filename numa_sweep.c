#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>

int main(int argc, char **argv)
{
    size_t mb = argc > 1 ? atol(argv[1]) : 128;
    size_t n = mb << 20;

    char *buf = malloc(n);

    if (buf == NULL) {
        printf("Memory allocation failed\n");
        return 1;
    }

    memset(buf, 1, n);

    long sum = 0;

    double t0 = omp_get_wtime();

    for (int pass = 0; pass < 4; pass++) {
        #pragma omp parallel for reduction(+:sum)
        for (size_t i = 0; i < n; i += 64) {
            sum += buf[i];
        }
    }

    printf("buffer=%zu MB | threads=%d | sum=%ld | time=%.4f s\n",
           mb, omp_get_max_threads(), sum, omp_get_wtime() - t0);

    free(buf);

    return 0;
}
