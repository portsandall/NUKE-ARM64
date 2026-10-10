#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(__aarch64__)
#define NUKE_ARCH "aarch64"
#elif defined(__x86_64__)
#define NUKE_ARCH "x86_64"
#else
#define NUKE_ARCH "other"
#endif

static uint32_t checksum(const unsigned char *data, size_t len) {
    uint32_t state = UINT32_C(2166136261);
    for (size_t i = 0; i < len; ++i) {
        state = (state ^ data[i]) * UINT32_C(16777619);
    }
    return state;
}

int main(int argc, char **argv) {
    const char *name = argc > 1 ? argv[1] : "mp_nuked";
    if (strcmp(name, "mp_nuked") != 0) {
        fprintf(stderr, "Only mp_nuked is within project scope.\n");
        return EXIT_FAILURE;
    }
    if (sizeof(void *) != 8) {
        fprintf(stderr, "A 64-bit target is required.\n");
        return EXIT_FAILURE;
    }
    printf("NUKE-ARM64 platform bootstrap | arch=%s | pointer_bits=%zu | map=%s | probe=%08" PRIx32 "\n",
           NUKE_ARCH, sizeof(void *) * 8, name,
           checksum((const unsigned char *)name, strlen(name)));
    return EXIT_SUCCESS;
}
