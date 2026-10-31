#!/usr/bin/env python3
"""Make StringTable runtime layout assertions correct for native pointer width.

The pinned source's 20-byte assertion describes its 32-bit reference layout.
On LP64 the three pointer fields are 64-bit, so the runtime structure is 32 bytes.
This transforms only the disposable upstream checkout used by CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

OLD_ASSERT = "static_assert(sizeof(StringTable) == 20);"
NEW_ASSERTS = """static_assert(sizeof(int) == 4, "StringTable integer fields must remain 32-bit");
static_assert(sizeof(StringTableCell) == (sizeof(void *) == 8 ? 16 : 8),
              "StringTableCell must use native pointer width");
static_assert(offsetof(StringTableCell, string) == 0);
static_assert(offsetof(StringTableCell, hash) == sizeof(void *));
static_assert(sizeof(StringTable) == (sizeof(void *) == 8 ? 32 : 20),
              "StringTable must use native pointer width");
static_assert(offsetof(StringTable, name) == 0);
static_assert(offsetof(StringTable, columnCount) == sizeof(void *));
static_assert(offsetof(StringTable, rowCount) == sizeof(void *) + sizeof(int));
static_assert(offsetof(StringTable, values) == (sizeof(void *) == 8 ? 16 : 12));
static_assert(offsetof(StringTable, cellIndex) == (sizeof(void *) == 8 ? 24 : 16));"""


def verify(text: str) -> None:
    if "#include <cstddef>" not in text:
        raise RuntimeError("com_stringtable.h must include <cstddef> for offsetof")
    if text.count(NEW_ASSERTS) != 1:
        raise RuntimeError("expected exactly one pointer-width-aware StringTable layout block")
    if OLD_ASSERT in text:
        raise RuntimeError("obsolete 32-bit-only StringTable size assertion remains")
    if "static_assert(sizeof(StringTable) == (sizeof(void *) == 8 ? 32 : 20)" not in text:
        raise RuntimeError("LP64/ILP32 StringTable size gate is missing")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <com_stringtable.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    if NEW_ASSERTS not in text:
        if text.count(OLD_ASSERT) != 1:
            raise RuntimeError(
                f"expected exactly one original StringTable size assertion; found {text.count(OLD_ASSERT)}"
            )
        if text.count("#pragma once") != 1:
            raise RuntimeError("expected exactly one #pragma once")
        text = text.replace("#pragma once", "#pragma once\n\n#include <cstddef>", 1)
        text = text.replace(OLD_ASSERT, NEW_ASSERTS, 1)
        text = text.replace(
            "struct StringTableCell // sizeof=0x8",
            "struct StringTableCell // 32-bit reference size=0x8; LP64 size=0x10",
            1,
        )
        text = text.replace(
            "struct StringTable // sizeof=0x14",
            "struct StringTable // 32-bit reference size=0x14; LP64 size=0x20",
            1,
        )

    verify(text)
    path.write_text(text, encoding="utf-8")
    print("Verified StringTableCell and StringTable native-pointer layouts (LP64 16/32 bytes; ILP32 8/20 bytes).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"StringTable LP64 layout transform failed: {error}", file=sys.stderr)
        raise SystemExit(1)
