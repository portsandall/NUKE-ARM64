#pragma once

// Minimal non-Windows compatibility layer for KisakBlack physics atomics.
// Not a general-purpose replacement for Windows.h.
#if defined(_WIN32)
#error "Use native Windows primitives on Windows builds"
#endif

using LONG = __INT32_TYPE__;
using PVOID = void*;
static_assert(sizeof(LONG) == 4, "Windows LONG must be 32-bit");

using LONGLONG = long long;
inline LONGLONG _InterlockedCompareExchange64(volatile LONGLONG* p, LONGLONG exchange, LONGLONG comparand) noexcept {
    LONGLONG previous = comparand;
    __atomic_compare_exchange_n(p, &previous, exchange, false,
                                __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST);
    return previous;
}

inline LONG _InterlockedCompareExchange(volatile LONG* p, LONG next, LONG expected) noexcept {
    LONG previous = expected;
    __atomic_compare_exchange_n(p, &previous, next, false,
                                __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST);
    return previous;
}
inline LONG InterlockedIncrement(volatile LONG* p) noexcept {
    return __atomic_add_fetch(p, LONG{1}, __ATOMIC_SEQ_CST);
}
inline LONG _InterlockedExchangeAdd(volatile LONG* p, LONG value) noexcept {
    return __atomic_fetch_add(p, value, __ATOMIC_SEQ_CST);
}
inline PVOID InterlockedExchangePointer(PVOID* p, PVOID next) noexcept {
    return __atomic_exchange_n(p, next, __ATOMIC_SEQ_CST);
}
inline void _ReadWriteBarrier() noexcept {
    __atomic_signal_fence(__ATOMIC_SEQ_CST);
}
inline void MemoryBarrier() noexcept {
    __atomic_thread_fence(__ATOMIC_SEQ_CST);
}
