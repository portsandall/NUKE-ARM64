#include <tl/base/tl_thread.h>
#include <cstdlib>
#include <cstdint>
#include <thread>
#include <vector>
#include <type_traits>

static void check(bool condition) {
    if (!condition) std::abort();
}

int main() {
    static_assert(sizeof(tlAtomicReadWriteMutex) == 0x18,
                  "thread mutex layout must remain 24 bytes");
    static_assert(alignof(tlAtomicReadWriteMutex) >= 8,
                  "thread mutex must retain 8-byte alignment");
    static_assert(std::is_same_v<decltype(tlAtomicReadWriteMutex::WriteThreadId), volatile LONGLONG>,
                  "atomic field type must match compare-exchange primitive");

    tlAtomicReadWriteMutex mutex;
    constexpr int thread_count = 8;
    constexpr int iterations = 2000;
    std::int64_t protected_total = 0;
    std::vector<std::thread> workers;
    workers.reserve(thread_count);

    for (int i = 0; i < thread_count; ++i) {
        workers.emplace_back([&] {
            for (int j = 0; j < iterations; ++j) {
                mutex.WriteLock();
                ++protected_total;
                mutex.WriteUnlock();
            }
        });
    }
    for (auto &worker : workers) worker.join();

    check(protected_total == thread_count * iterations);
    check(mutex.WriteLockCount == 0);
    check(mutex.ReadLockCount == 0);
    check(mutex.WriteThreadId == 0);
    return 0;
}
