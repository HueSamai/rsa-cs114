#include "stdio.h"
#include "inttypes.h"
#include <stdlib.h>

typedef uint64_t u64;

FILE* out;

size_t prime_index = 1;
u64 primes[1024 * 1024] = {2};

int is_prime(u64 n) {
    for (size_t i = 0; i < prime_index; ++i)
        if (!(n % primes[i])) return 0;
    return 1;
}

u64 get_next_prime() {
    u64 p = primes[prime_index - 1];
    while (!is_prime(p)) ++p;
    primes[prime_index++] = p;
    return p;
}

void find_primes(u64 threshold, int count) {
    int primes_larger = 0;
    while (primes_larger < count) {
        u64 p = get_next_prime();
        if (p > threshold) {
            fprintf(out, "%llu\n", p);
            ++primes_larger;
        }
    }
}

int main(int argc, char** argv) {
    if (argc < 3) {
        fprintf(stderr, "ERROR: usage: find_primes <threshold> <count>\n");
        return 1;
    }

    u64 threshold = _atoi64(argv[1]);
    int count = atoi(argv[2]);

    out = fopen("primes.txt", "w");
    find_primes(threshold, count);
    return 0;
}
