#!/usr/bin/env python3
"""Make generic job-queue declarations and storage layout LP64-safe.

The header's Windows include was only supplying LONG64, memcpy and offsetof.
The 32-bit jqBatch assertion describes the original x86 runtime object, not
serialized data: the queue allocates nodes using sizeof(NodeType) and copies
batches using sizeof(jqBatch). On LP64, retain native pointer widths and
request sufficient alignment for the node's pointer members.
"""
from pathlib import Path
import sys

WINDOWS_INCLUDE = "#include <Windows.h>"
OLD_THREAD_ID = "volatile LONG64 ThreadId;"
NEW_THREAD_ID = "volatile __int64 ThreadId;"
OLD_BATCH_ASSERT = "static_assert(sizeof(jqBatch) == 124);"
NEW_BATCH_ASSERT = (
    'static_assert(sizeof(jqBatch) == (sizeof(void *) == 8 ? 152 : 124), '
    '"jqBatch is an internal runtime queue payload with native pointers");'
)
OLD_NODE_ALLOC = "tlMemAlloc(blockSize + sizeof(NodeBlockEntry), 4u, 0);"
NEW_NODE_ALLOC = "tlMemAlloc(blockSize + sizeof(NodeBlockEntry), alignof(NodeType), 0);"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"expected one {label}, found {count}")
    return source.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: port_jobqueue_header.py <jobqueue_all.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"missing upstream job-queue header: {path}", file=sys.stderr)
        return 2

    source = path.read_text(encoding="utf-8")
    if "memcpy(" not in source or "offsetof(" not in source:
        print("expected inline memcpy and offsetof uses in jobqueue_all.h", file=sys.stderr)
        return 1
    if "#include <stddef.h>" in source or "#include <string.h>" in source:
        print("jobqueue_all.h already contains one of the required C headers", file=sys.stderr)
        return 1

    updated = replace_once(
        source, WINDOWS_INCLUDE,
        "#include <stddef.h>\n#include <string.h>",
        "Windows SDK include",
    )
    updated = replace_once(updated, OLD_THREAD_ID, NEW_THREAD_ID, "64-bit thread ID")
    updated = replace_once(updated, OLD_BATCH_ASSERT, NEW_BATCH_ASSERT, "jqBatch size assertion")
    updated = replace_once(updated, OLD_NODE_ALLOC, NEW_NODE_ALLOC, "job-queue node allocation")

    if WINDOWS_INCLUDE in updated or "LONG64" in updated:
        print("Windows-specific declaration remains in jobqueue_all.h", file=sys.stderr)
        return 1
    if updated.count("#include <stddef.h>") != 1 or updated.count("#include <string.h>") != 1:
        print("expected one declaration include for offsetof and memcpy", file=sys.stderr)
        return 1
    if OLD_NODE_ALLOC in updated or NEW_NODE_ALLOC not in updated:
        print("job-queue node allocation alignment was not updated", file=sys.stderr)
        return 1

    path.write_text(updated, encoding="utf-8")
    print("Removed jobqueue_all.h Windows SDK header dependency.")
    print("Preserved signed 64-bit thread IDs and added standard declarations for offsetof/memcpy.")
    print("Made jqBatch size architecture-aware and aligned node blocks to alignof(NodeType).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
