#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>

namespace nuke_port {

// Reserve an aligned region from a shared linear buffer without truncating its
// address to 32 bits. Compare/exchange prevents concurrent allocators from
// returning overlapping ranges.
inline char *allocate_aligned_buffer(
    char **cursor,
    char *end,
    std::size_t size,
    std::size_t alignment) noexcept
{
    if (!cursor || !end || size == 0 || alignment == 0 ||
        (alignment & (alignment - 1)) != 0 ||
        alignment > std::numeric_limits<std::uintptr_t>::max())
        return nullptr;

    char *observed = __atomic_load_n(cursor, __ATOMIC_ACQUIRE);
    if (!observed)
        return nullptr;

    const std::uintptr_t end_address = reinterpret_cast<std::uintptr_t>(end);
    const std::uintptr_t max_address =
        std::numeric_limits<std::uintptr_t>::max();
    const std::uintptr_t mask = static_cast<std::uintptr_t>(alignment - 1);

    for (;;)
    {
        const std::uintptr_t current_address =
            reinterpret_cast<std::uintptr_t>(observed);

        if (current_address > end_address ||
            current_address > max_address - mask)
            return nullptr;

        const std::uintptr_t aligned_address =
            (current_address + mask) & ~mask;

        if (aligned_address > end_address ||
            size > end_address - aligned_address ||
            size > max_address - aligned_address)
            return nullptr;

        char *next = reinterpret_cast<char *>(aligned_address + size);
        char *expected = observed;
        if (__atomic_compare_exchange_n(
                cursor,
                &expected,
                next,
                false,
                __ATOMIC_ACQ_REL,
                __ATOMIC_ACQUIRE))
            return reinterpret_cast<char *>(aligned_address);

        observed = expected;
        if (!observed)
            return nullptr;
    }
}

} // namespace nuke_port
