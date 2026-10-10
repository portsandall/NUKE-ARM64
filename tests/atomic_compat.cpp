#include <nuke/win_atomic_compat.h>
#include <cassert>
#include <cstdint>
#include <thread>
#include <vector>

int main() {
    volatile LONG value = 1;
    assert(_InterlockedCompareExchange(&value, 4, 0) == 1);
    assert(value == 1);
    assert(_InterlockedCompareExchange(&value, 4, 1) == 1);
    assert(value == 4);
    assert(InterlockedIncrement(&value) == 5);

    int a = 1, b = 2;
    PVOID pointer = &a;
    assert(InterlockedExchangePointer(&pointer, &b) == &a);
    assert(pointer == &b);
    _ReadWriteBarrier();
    MemoryBarrier();

    volatile LONG counter = 0;
    constexpr int threads = 8, iterations = 10000;
    std::vector<std::thread> workers;
    for (int i = 0; i < threads; ++i) {
        workers.emplace_back([&] {
            for (int j = 0; j < iterations; ++j)
                InterlockedIncrement(&counter);
        });
    }
    for (auto &worker : workers) worker.join();
    assert(counter == threads * iterations);

    volatile LONG spin = 0;
    std::int64_t protected_total = 0;
    workers.clear();
    for (int i = 0; i < threads; ++i) {
        workers.emplace_back([&] {
            for (int j = 0; j < iterations; ++j) {
                while (_InterlockedCompareExchange(&spin, 1, 0) != 0) {}
                ++protected_total;
                assert(_InterlockedCompareExchange(&spin, 0, 1) == 1);
            }
        });
    }
    for (auto &worker : workers) worker.join();
    assert(protected_total == threads * iterations);
}
