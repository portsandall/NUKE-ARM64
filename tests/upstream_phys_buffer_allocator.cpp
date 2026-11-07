#include "upstream_phys_buffer_allocator.h"
#include "upstream_phys_free_list_compat.h"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdlib>
#include <thread>
#include <vector>

struct FreeListNode
{
    FreeListNode *next = nullptr;
    std::uint32_t id = 0;
};

static void check(bool condition)
{
    if (!condition)
        std::abort();
}

static void test_native_pointer_free_list()
{
    void *head = nullptr;
    unsigned int tag = 0;
    std::array<FreeListNode, 3> small{};

    for (std::size_t i = 0; i < small.size(); ++i)
    {
        small[i].id = static_cast<std::uint32_t>(i);
        nuke_port::phys_free_list_push(&head, &tag, &small[i]);
    }
    check(tag == 3);
    check(nuke_port::phys_free_list_pop(&head, &tag) == &small[2]);
    check(nuke_port::phys_free_list_pop(&head, &tag) == &small[1]);
    check(nuke_port::phys_free_list_pop(&head, &tag) == &small[0]);
    check(nuke_port::phys_free_list_pop(&head, &tag) == nullptr);
    check(head == nullptr);
    check(tag == 6);

    constexpr std::size_t thread_count = 8;
    constexpr std::size_t nodes_per_thread = 128;
    constexpr std::size_t node_count = thread_count * nodes_per_thread;
    std::vector<FreeListNode> nodes(node_count);
    for (std::size_t i = 0; i < nodes.size(); ++i)
        nodes[i].id = static_cast<std::uint32_t>(i);

    head = nullptr;
    tag = 0;
    std::vector<std::thread> workers;
    for (std::size_t thread = 0; thread < thread_count; ++thread)
    {
        workers.emplace_back([&, thread] {
            for (std::size_t i = 0; i < nodes_per_thread; ++i)
                nuke_port::phys_free_list_push(
                    &head, &tag, &nodes[thread * nodes_per_thread + i]);
        });
    }
    for (auto &worker : workers)
        worker.join();

    check(tag == node_count);
    std::vector<unsigned char> seen(node_count, 0);
    std::size_t popped = 0;
    while (void *raw = nuke_port::phys_free_list_pop(&head, &tag))
    {
        auto *node = static_cast<FreeListNode *>(raw);
        check(node->id < node_count);
        check(seen[node->id] == 0);
        seen[node->id] = 1;
        ++popped;
    }
    check(popped == node_count);
    check(tag == node_count * 2);
    for (unsigned char value : seen)
        check(value == 1);
}

int main()
{
    test_native_pointer_free_list();
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
