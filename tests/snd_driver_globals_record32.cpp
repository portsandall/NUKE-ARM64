#include "nuke/snd_driver_globals_record32.h"

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>

int main()
{
    constexpr nuke::db::SndDriverGlobalsRecord32 record{
        0x01020304u, 3u,
        0x11121314u, 4u,
        0x21222324u, 5u,
        0x31323334u, 6u,
        0x41424344u, 7u,
        0x51525354u, 8u,
        0x61626364u
    };
    constexpr std::array<std::uint32_t, 13> expected{
        0x01020304u, 3u,
        0x11121314u, 4u,
        0x21222324u, 5u,
        0x31323334u, 6u,
        0x41424344u, 7u,
        0x51525354u, 8u,
        0x61626364u
    };

    std::array<std::uint32_t, 13> words{};
    std::memcpy(words.data(), &record, sizeof(record));
    if (words != expected) {
        std::fprintf(stderr, "SndDriverGlobals record field-order regression\n");
        return 1;
    }

    std::puts("SndDriverGlobals fixed-width record: 52 bytes, 13 ordered 32-bit words");
    return 0;
}
