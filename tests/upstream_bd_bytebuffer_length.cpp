#include <nuke/bd_byte_buffer_compat.h>

#include <cstdint>

int main()
{
    const char empty[] = {'\0', 'x'};
    if (nuke::boundedCStringLength(empty, static_cast<std::uint32_t>(sizeof(empty))) != 0)
        return 1;

    const char middle[] = {'a', 'b', '\0', 'c'};
    if (nuke::boundedCStringLength(middle, static_cast<std::uint32_t>(sizeof(middle))) != 2)
        return 2;

    if (nuke::boundedCStringLength(middle, 2) != 2)
        return 3;

    const char unterminated[] = {'a', 'b', 'c'};
    if (nuke::boundedCStringLength(unterminated, static_cast<std::uint32_t>(sizeof(unterminated))) != 3)
        return 4;

    if (nuke::boundedCStringLength(middle, 0) != 0)
        return 5;

    return 0;
}
