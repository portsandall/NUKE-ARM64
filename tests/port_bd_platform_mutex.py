#!/usr/bin/env python3
"""Select a recursive pthread implementation for KisakBlack's platform mutex.

The upstream file is a small four-method Win32 adapter. Check all four method
anchors before replacing the disposable CI checkout. The public MutexHandle
remains void*; Windows retains the original implementation.
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <bdPlatformMutex.cpp>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    original = path.read_bytes()
    source = original.decode("latin-1")
    anchors = (
        '#include "bdPlatformMutex.h"',
        "bdPlatformMutex::createMutex()",
        "bdPlatformMutex::lock(MutexHandle &hand)",
        "bdPlatformMutex::unlock(MutexHandle &hand)",
        "bdPlatformMutex::destroy(MutexHandle &hand)",
    )
    for anchor in anchors:
        count = source.count(anchor)
        if count != 1:
            raise RuntimeError(f"expected exactly one source anchor {anchor!r}; found {count}")

    replacement = '''#include "bdPlatformMutex.h"

#if defined(_WIN32)
#include <Windows.h>
#else
#include <new>
#include <pthread.h>
#endif

#if defined(_WIN32)
MutexHandle bdPlatformMutex::createMutex()
{
    return CreateMutexA(NULL, FALSE, NULL);
}

void bdPlatformMutex::lock(MutexHandle &hand)
{
    WaitForSingleObject(hand, 0xFFFFFFFF);
}

void bdPlatformMutex::unlock(MutexHandle &hand)
{
    ReleaseMutex(hand);
}

void bdPlatformMutex::destroy(MutexHandle &hand)
{
    ReleaseMutex(hand);
    CloseHandle(hand);
}
#else
MutexHandle bdPlatformMutex::createMutex()
{
    auto *mutex = new (std::nothrow) pthread_mutex_t;
    if (mutex == nullptr)
        return nullptr;

    pthread_mutexattr_t attributes;
    if (pthread_mutexattr_init(&attributes) != 0)
    {
        delete mutex;
        return nullptr;
    }

    int result = pthread_mutexattr_settype(&attributes, PTHREAD_MUTEX_RECURSIVE);
    if (result == 0)
        result = pthread_mutex_init(mutex, &attributes);
    pthread_mutexattr_destroy(&attributes);

    if (result != 0)
    {
        delete mutex;
        return nullptr;
    }
    return mutex;
}

void bdPlatformMutex::lock(MutexHandle &hand)
{
    if (hand != nullptr)
        (void)pthread_mutex_lock(static_cast<pthread_mutex_t *>(hand));
}

void bdPlatformMutex::unlock(MutexHandle &hand)
{
    if (hand != nullptr)
        (void)pthread_mutex_unlock(static_cast<pthread_mutex_t *>(hand));
}

void bdPlatformMutex::destroy(MutexHandle &hand)
{
    if (hand == nullptr)
        return;

    auto *mutex = static_cast<pthread_mutex_t *>(hand);
    if (pthread_mutex_destroy(mutex) == 0)
    {
        delete mutex;
        hand = nullptr;
    }
}
#endif
'''
    path.write_bytes(replacement.encode("ascii"))
    print(f"Applied recursive pthread mutex implementation to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
