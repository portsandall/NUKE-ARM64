#include <nuke/win_atomic_compat.h>
#include <cstdlib>
#include <cstdint>
#include <thread>
#include <vector>

// Never hide atomic operations inside assert(): NDEBUG removes their side effects.
static void check(bool ok) { if (!ok) std::abort(); }

int main() {
    volatile LONG value = 1;
    check(_InterlockedCompareExchange(&value, 4, 0) == 1);
    check(value == 1);
    check(_InterlockedCompareExchange(&value, 4, 1) == 1);
    check(value == 4);

    volatile long long wide = 0x100000002LL;
    check(_InterlockedCompareExchange64(&wide, 0x300000004LL, 0x100000001LL) == 0x100000002LL);
    check(wide == 0x100000002LL);
    check(_InterlockedCompareExchange64(&wide, 0x300000004LL, 0x100000002LL) == 0x100000002LL);
    check(wide == 0x300000004LL);
    check(InterlockedIncrement(&value) == 5);
    check(_InterlockedDecrement(&value) == 4);
    check(value == 4);
    check(_InterlockedDecrement(&value) == 3);
    check(value == 3);

    volatile LONG exchanged = 11;
    check(InterlockedExchange(&exchanged, -7) == 11);
    check(exchanged == -7);
    check(InterlockedExchange(&exchanged, 0) == -7);
    check(exchanged == 0);


    volatile std::uint32_t unsigned_value = 1;
    check(_InterlockedCompareExchange(&unsigned_value, 4u, 0u) == 1u);
    check(unsigned_value == 1u);
    check(_InterlockedCompareExchange(&unsigned_value, 4u, 1u) == 1u);
    check(unsigned_value == 4u);
    check(_InterlockedExchangeAdd(&unsigned_value, 3u) == 4u);
    check(unsigned_value == 7u);
    check(_InterlockedDecrement(&unsigned_value) == 6u);
    check(InterlockedIncrement(&unsigned_value) == 7u);
    check(InterlockedExchange(&unsigned_value, 9u) == 7u);
    check(unsigned_value == 9u);

    volatile LONG exchange_add = 7;
    check(_InterlockedExchangeAdd(&exchange_add, 3) == 7);
    check(exchange_add == 10);
    check(_InterlockedExchangeAdd(&exchange_add, -2) == 10);
    check(exchange_add == 8);

    int a = 1, b = 2;
    PVOID pointer = &a;
    check(InterlockedExchangePointer(&pointer, &b) == &a);
    check(pointer == &b);

    const PVOID sentinel =
        reinterpret_cast<PVOID>(std::uintptr_t{0xFEDCBA98u});
    PVOID owner = &a;
    check(InterlockedCompareExchangePointer(
              reinterpret_cast<PVOID volatile *>(&owner), sentinel, &a) == &a);
    check(owner == sentinel);
    check(InterlockedCompareExchangePointer(
              reinterpret_cast<PVOID volatile *>(&owner), &b, sentinel) == sentinel);
    check(owner == &b);
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
    check(counter == threads * iterations);

    volatile LONG spin = 0;
    std::int64_t protected_total = 0;
    workers.clear();
    for (int i = 0; i < threads; ++i) {
        workers.emplace_back([&] {
            for (int j = 0; j < iterations; ++j) {
                while (_InterlockedCompareExchange(&spin, 1, 0) != 0) {}
                ++protected_total;
                check(_InterlockedCompareExchange(&spin, 0, 1) == 1);
            }
        });
    }
    for (auto &worker : workers) worker.join();
    check(protected_total == threads * iterations);
}
