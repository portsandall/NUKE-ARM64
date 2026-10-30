#!/usr/bin/env python3
"""Remove the unnecessary Windows SDK include from generic job-queue declarations.

The header uses LONG64 for one signed 64-bit thread-id field and memcpy in
its inline queue methods. Neither requires the Windows SDK: __int64 is
already covered by the repository's MSVC-compatibility preinclude, and
<string.h> declares memcpy for this C-style header.
"""
from pathlib import Path
import sys

WINDOWS_INCLUDE = "#include <Windows.h>"
OLD_THREAD_ID = "volatile LONG64 ThreadId;"
NEW_THREAD_ID = "volatile __int64 ThreadId;"
STRING_HEADER = "#include <string.h>"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: port_jobqueue_header.py <jobqueue_all.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"missing upstream job-queue header: {path}", file=sys.stderr)
        return 2

    source = path.read_text(encoding="utf-8")
    if source.count(WINDOWS_INCLUDE) != 1:
        print("expected exactly one Windows.h include in jobqueue_all.h", file=sys.stderr)
        return 1
    if source.count(OLD_THREAD_ID) != 1:
        print("expected exactly one LONG64 thread-id field in jobqueue_all.h", file=sys.stderr)
        return 1
    if "memcpy(" not in source:
        print("expected inline memcpy use in jobqueue_all.h", file=sys.stderr)
        return 1

    updated = source.replace(WINDOWS_INCLUDE, STRING_HEADER, 1)
    updated = updated.replace(OLD_THREAD_ID, NEW_THREAD_ID, 1)

    if WINDOWS_INCLUDE in updated or "LONG64" in updated:
        print("Windows-specific declaration remains in jobqueue_all.h", file=sys.stderr)
        return 1
    if updated.count(STRING_HEADER) != 1:
        print("expected one string.h include after transformation", file=sys.stderr)
        return 1

    path.write_text(updated, encoding="utf-8")
    print("Removed job-queue header's Windows.h dependency; retained signed 64-bit ThreadId and memcpy declaration.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
