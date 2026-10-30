#!/usr/bin/env python3
"""Replace Win32 kernel-mutex calls with a recursive POSIX mutex on non-Windows.

The public MutexHandle remains void* so this implementation preserves the
existing handle-sized ABI. Windows retains the original Win32 implementation.
This transform edits only the disposable pinned-source checkout used by CI.
The source contains legacy non-UTF-8 comments, so it is handled as bytes.
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
    expected = b'''#include "bdPlatformMutex.h"

#include <Windows.h>

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
'''
    replacement = b'''#include "bdPlatformMutex.h"

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
    count = original.count(expected)
    if count != 1:
        raise RuntimeError(f"expected exactly one original Win32 mutex implementation; found {count}")

    path.write_bytes(replacement)
    print(f"Applied recursive pthread mutex implementation to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
