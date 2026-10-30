#include "upstream_phys_buffer_allocator.h"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <thread>
#include <vector>

int main()
{
    alignas(64) std::array<unsigned char, 1024> small{};
    char *cursor = reinterpret_cast<char *>(small.data()) + 1;
    char *const end = reinterpret_cast<char *>(small.data() + small.size());

    char *first = nuke_port::allocate_aligned_buffer(&cursor, end, 7, 8);
    assert(first != nullptr);
    assert((reinterpret_cast<std::uintptr_t>(first) & 7u) == 0);
    assert(cursor == first + 7);

    char *second = nuke_port::allocate_aligned_buffer(&cursor, end, 8, 16);
    assert(second != nullptr);
    assert((reinterpret_cast<std::uintptr_t>(second) & 15u) == 0);
    assert(first + 7 <= second);
    assert(cursor == second + 8);

    char *before_failure = cursor;
    assert(nuke_port::allocate_aligned_buffer(&cursor, end, 1, 0) == nullptr);
    assert(nuke_port::allocate_aligned_buffer(&cursor, end, 1, 3) == nullptr);
    assert(nuke_port::allocate_aligned_buffer(&cursor, end, 0, 8) == nullptr);
    assert(nuke_port::allocate_aligned_buffer(&cursor, end, 1024, 8) == nullptr);
    assert(cursor == before_failure);

    alignas(64) std::array<unsigned char, 65536> concurrent{};
    char *shared_cursor = reinterpret_cast<char *>(concurrent.data()) + 1;
    char *const shared_end =
        reinterpret_cast<char *>(concurrent.data() + concurrent.size());

    constexpr std::size_t thread_count = 8;
    constexpr std::size_t allocations_per_thread = 64;
    constexpr std::size_t allocation_size = 13;
    constexpr std::size_t allocation_alignment = 16;
    std::vector<char *> allocations(thread_count * allocations_per_thread);
    std::vector<std::thread> workers;
    workers.reserve(thread_count);

    for (std::size_t thread_index = 0; thread_index < thread_count; ++thread_index)
    {
        workers.emplace_back([&, thread_index]() {
            for (std::size_t i = 0; i < allocations_per_thread; ++i)
            {
                char *p = nuke_port::allocate_aligned_buffer(
                    &shared_cursor,
                    shared_end,
                    allocation_size,
                    allocation_alignment);
                assert(p != nullptr);
                allocations[thread_index * allocations_per_thread + i] = p;
            }
        });
    }

    for (auto &worker : workers)
        worker.join();

    std::sort(allocations.begin(), allocations.end(),
              [](const char *a, const char *b) {
                  return reinterpret_cast<std::uintptr_t>(a) <
                         reinterpret_cast<std::uintptr_t>(b);
              });

    for (std::size_t i = 0; i < allocations.size(); ++i)
    {
        const auto address = reinterpret_cast<std::uintptr_t>(allocations[i]);
        assert((address & (allocation_alignment - 1)) == 0);
        assert(allocations[i] >= reinterpret_cast<char *>(concurrent.data()));
        assert(allocations[i] + allocation_size <= shared_end);
        if (i != 0)
            assert(allocations[i - 1] + allocation_size <= allocations[i]);
    }

    return 0;
}
