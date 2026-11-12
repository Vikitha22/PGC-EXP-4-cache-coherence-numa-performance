#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

#define N 100000000L
#define MB 128UL

int main()
{
    int threads[] = {1, 2, 4};

    printf("CACHE FALSE SHARING COMPARISON\n");

    for (int k = 0; k < 3; k++)
    {
        int nt = threads[k];

        for (int stride_index = 0; stride_index < 2; stride_index++)
        {
            int stride = stride_index == 0 ? 1 : 8;

            size_t bytes = (size_t)nt * stride * sizeof(long);
            bytes = ((bytes + 63) / 64) * 64;

            volatile long *cnt = aligned_alloc(64, bytes);

            if (cnt == NULL)
            {
                printf("Memory allocation failed\n");
                return 1;
            }

            for (int i = 0; i < nt * stride; i++)
            {
                cnt[i] = 0;
            }

            omp_set_num_threads(nt);

            double t0 = omp_get_wtime();

            #pragma omp parallel
            {
                int id = omp_get_thread_num();

                for (long i = 0; i < N / nt; i++)
                {
                    cnt[id * stride]++;
                }
            }

            double elapsed = omp_get_wtime() - t0;

            long total = 0;

            for (int i = 0; i < nt; i++)
            {
                total += cnt[i * stride];
            }

            printf("threads=%d | layout=%s | total=%ld | time=%.4f s\n",
                   nt,
                   stride == 1 ? "adjacent" : "padded",
                   total,
                   elapsed);

            free((void *)cnt);
        }
    }

    printf("\nNUMA MEMORY ACCESS TEST\n");

    size_t n = MB * 1024UL * 1024UL;

    char *buf = malloc(n);

    if (buf == NULL)
    {
        printf("Memory allocation failed\n");
        return 1;
    }

    for (size_t i = 0; i < n; i++)
    {
        buf[i] = 1;
    }

    for (int nt = 1; nt <= 2; nt++)
    {
        long sum = 0;

        omp_set_num_threads(nt);

        double t0 = omp_get_wtime();

        #pragma omp parallel for reduction(+:sum)
        for (size_t i = 0; i < n; i += 64)
        {
            sum += buf[i];
        }

        printf("threads=%d | buffer=%lu MB | sum=%ld | time=%.4f s\n",
               nt, MB, sum, omp_get_wtime() - t0);
    }

    free(buf);

    return 0;
}
