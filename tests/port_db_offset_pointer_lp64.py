#!/usr/bin/env python3
"""Make FastFile offset relocation write complete native pointers on LP64."""
from __future__ import annotations

import sys
from pathlib import Path

OLD_DECL = "void __cdecl DB_ConvertOffsetToPointer(unsigned int *data);"
NEW_DECL = "void __cdecl DB_ConvertOffsetToPointer(void *data);"
OLD_FUNCTION = """void __cdecl DB_ConvertOffsetToPointer(unsigned int *data)
{
    *data = (unsigned int)&g_streamBlocks[(unsigned int)(*data - 1) >> 29].data[(*data - 1) & 0x1FFFFFFF];
}"""
NEW_FUNCTION = """void __cdecl DB_ConvertOffsetToPointer(void *data)
{
    const uint32_t offset = DB_ReadSerializedPointerOffset32(data);
    void *pointer =
        &g_streamBlocks[(offset - 1) >> 29].data[(offset - 1) & 0x1FFFFFFF];
    DB_WriteNativePointerSlot(data, pointer);
}"""
HELPER_INCLUDE = '#include "db_stream_pointer_relocation.h"'
HELPER_CONTENT = """#pragma once

#include <stdint.h>
#include <string.h>

// FastFile pointer slots store a 32-bit offset even when runtime pointers are
// native-width. Read the wire value separately from the resolved pointer.
static inline uint32_t DB_ReadSerializedPointerOffset32(const void *slot)
{
    uint32_t offset;
    memcpy(&offset, slot, sizeof(offset));
    return offset;
}

static inline void DB_WriteNativePointerSlot(void *slot, void *pointer)
{
    memcpy(slot, &pointer, sizeof(pointer));
}
"""


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return source.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 4:
        print(
            f"usage: {Path(sys.argv[0]).name} <db_stream_load.h> "
            "<db_stream_load.cpp> <new-helper-header>",
            file=sys.stderr,
        )
        return 2

    header_path, source_path, helper_path = map(Path, sys.argv[1:])
    header = header_path.read_text(encoding="utf-8")
    source = source_path.read_text(encoding="utf-8")

    if OLD_DECL in header:
        header = replace_once(header, OLD_DECL, NEW_DECL, "pointer conversion declaration")
    elif header.count(NEW_DECL) != 1:
        raise RuntimeError("expected the original or already-transformed pointer declaration")
    if OLD_DECL in header or header.count(NEW_DECL) != 1:
        raise RuntimeError("pointer conversion declaration did not reach the expected state")

    if helper_path.exists():
        if helper_path.read_text(encoding="utf-8") != HELPER_CONTENT:
            raise RuntimeError("existing db_stream_pointer_relocation.h has unexpected contents")
    else:
        helper_path.parent.mkdir(parents=True, exist_ok=True)
        helper_path.write_text(HELPER_CONTENT, encoding="utf-8")

    if HELPER_INCLUDE not in source:
        source = replace_once(
            source,
            '#include "db_stream_load.h"\n',
            '#include "db_stream_load.h"\n' + HELPER_INCLUDE + "\n",
            "pointer relocation helper include",
        )
    if source.count(HELPER_INCLUDE) != 1:
        raise RuntimeError("db_stream_load.cpp must include the helper exactly once")

    if OLD_FUNCTION in source:
        source = replace_once(source, OLD_FUNCTION, NEW_FUNCTION, "pointer conversion function")
    elif source.count(NEW_FUNCTION) != 1:
        raise RuntimeError("expected the original or already-transformed pointer conversion function")
    if OLD_FUNCTION in source or source.count(NEW_FUNCTION) != 1:
        raise RuntimeError("pointer conversion function did not reach the expected state")

    if helper_path.read_text(encoding="utf-8") != HELPER_CONTENT:
        raise RuntimeError("generated pointer relocation helper differs from expected content")
    header_path.write_text(header, encoding="utf-8")
    source_path.write_text(source, encoding="utf-8")
    print(
        "Verified 32-bit FastFile offsets are read separately and resolved "
        "addresses are stored at native pointer width."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"DB pointer-width transform failed: {error}", file=sys.stderr)
        raise SystemExit(1)
