#include <tl/base/tl_thread.h>
#include <cstdlib>
#include <cstdint>
#include <atomic>
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

    // KisakBlack call sites release ReadLock by atomically decrementing
    // ReadLockCount directly, so exercise that exact protocol under contention.
    std::atomic<std::uint64_t> shared_value{0};
    std::atomic<std::uint64_t> shared_inverse{~std::uint64_t{0}};
    std::atomic<int> active_readers{0};
    std::atomic<bool> writer_active{false};
    std::atomic<bool> failed{false};
    constexpr int reader_count = 4;
    constexpr int writer_count = 2;
    constexpr int read_iterations = 2500;
    constexpr int write_iterations = 1500;
    workers.clear();
    workers.reserve(reader_count + writer_count);

    for (int i = 0; i < writer_count; ++i) {
        workers.emplace_back([&] {
            for (int j = 0; j < write_iterations; ++j) {
                mutex.WriteLock();
                writer_active.store(true, std::memory_order_relaxed);
                if (active_readers.load(std::memory_order_relaxed) != 0)
                    failed.store(true, std::memory_order_relaxed);

                const auto next = shared_value.load(std::memory_order_relaxed) + 1;
                shared_value.store(next, std::memory_order_relaxed);
                // Widen the consistency window so a reader that slips past
                // the writer lock is more likely to be detected.
                std::this_thread::yield();
                shared_inverse.store(~next, std::memory_order_relaxed);
                writer_active.store(false, std::memory_order_relaxed);
                mutex.WriteUnlock();
            }
        });
    }

    for (int i = 0; i < reader_count; ++i) {
        workers.emplace_back([&] {
            for (int j = 0; j < read_iterations; ++j) {
                mutex.ReadLock();
                active_readers.fetch_add(1, std::memory_order_relaxed);
                if (writer_active.load(std::memory_order_relaxed))
                    failed.store(true, std::memory_order_relaxed);

                const auto value = shared_value.load(std::memory_order_relaxed);
                const auto inverse = shared_inverse.load(std::memory_order_relaxed);
                std::this_thread::yield();

                if (inverse != ~value)
                    failed.store(true, std::memory_order_relaxed);

                active_readers.fetch_sub(1, std::memory_order_relaxed);
                const auto prior_count = _InterlockedExchangeAdd(
                    &mutex.ThisPtr->ReadLockCount, 0xFFFFFFFFu);
                if (prior_count == 0)
                    failed.store(true, std::memory_order_relaxed);
            }
        });
    }

    for (auto &worker : workers) worker.join();
    check(!failed.load(std::memory_order_relaxed));
    check(shared_value.load(std::memory_order_relaxed) ==
          static_cast<std::uint64_t>(writer_count * write_iterations));
    check(shared_inverse.load(std::memory_order_relaxed) ==
          ~shared_value.load(std::memory_order_relaxed));
    check(mutex.WriteLockCount == 0);
    check(mutex.ReadLockCount == 0);
    check(mutex.WriteThreadId == 0);
    return 0;
}
