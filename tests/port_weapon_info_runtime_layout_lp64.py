#!/usr/bin/env python3
"""Preserve native pointer-width layout for the runtime weaponInfo_s object.

The pinned 0x24 assertion is the 32-bit reference layout. weaponInfo_s is a
client runtime structure containing seven native pointers; it is not a disk
asset record. The LP64 object is 0x40 bytes. Check key offsets as well as size
so this does not hide a changed field order or unexpected packing.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

OLD_ASSERT = "static_assert(sizeof(weaponInfo_s) == 0x24);"
NEW_ASSERTS = """static_assert(sizeof(weaponInfo_s) == (sizeof(void *) == 4 ? 0x24 : 0x40),
              "weaponInfo_s must use the native pointer width");
static_assert(alignof(weaponInfo_s) == alignof(void *));
static_assert(__builtin_offsetof(weaponInfo_s, handModel) == 0);
static_assert(__builtin_offsetof(weaponInfo_s, gogglesModel) == sizeof(void *));
static_assert(__builtin_offsetof(weaponInfo_s, rocketModel) == 2 * sizeof(void *));
static_assert(__builtin_offsetof(weaponInfo_s, weapModelIdx) == 3 * sizeof(void *));
static_assert(__builtin_offsetof(weaponInfo_s, registered) ==
              (sizeof(void *) == 4 ? 16 : 28));
static_assert(__builtin_offsetof(weaponInfo_s, item) ==
              (sizeof(void *) == 4 ? 20 : 32));
static_assert(__builtin_offsetof(weaponInfo_s, translatedDisplayName) ==
              (sizeof(void *) == 4 ? 24 : 40));
static_assert(__builtin_offsetof(weaponInfo_s, translatedModename) ==
              (sizeof(void *) == 4 ? 28 : 48));
static_assert(__builtin_offsetof(weaponInfo_s, translatedAIOverlayDescription) ==
              (sizeof(void *) == 4 ? 32 : 56));"""
OLD_COMMENT = "struct weaponInfo_s // sizeof=0x24"
NEW_COMMENT = "struct weaponInfo_s // ILP32 size=0x24; LP64 size=0x40"


def verify(source: str) -> None:
    if source.count(NEW_ASSERTS) != 1:
        raise RuntimeError("expected exactly one complete pointer-width-aware weaponInfo_s layout block")
    if OLD_ASSERT in source:
        raise RuntimeError("obsolete 32-bit-only weaponInfo_s size assertion remains")
    code = re.sub(r"/\*.*?\*/|//[^\\n]*", "", source, flags=re.DOTALL)
    fields = (
        r"XModel\\s*\\*\\s*handModel\\s*;",
        r"XModel\\s*\\*\\s*gogglesModel\\s*;",
        r"XModel\\s*\\*\\s*rocketModel\\s*;",
        r"unsigned\\s+__int8\\s+weapModelIdx\\s*;",
        r"int\\s+registered\\s*;",
        r"const\\s+struct\\s+gitem_s\\s*\\*\\s*item\\s*;",
        r"const\\s+char\\s*\\*\\s*translatedDisplayName\\s*;",
        r"const\\s+char\\s*\\*\\s*translatedModename\\s*;",
        r"const\\s+char\\s*\\*\\s*translatedAIOverlayDescription\\s*;",
    )
    for pattern in fields:
        if re.search(pattern, code) is None:
            raise RuntimeError(f"weaponInfo_s field/layout guard failed: {pattern}")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <cg_weapons.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    if NEW_ASSERTS not in source:
        if source.count(OLD_ASSERT) != 1:
            raise RuntimeError(
                f"expected exactly one original weaponInfo_s assertion; found {source.count(OLD_ASSERT)}"
            )
        if source.count(OLD_COMMENT) != 1:
            raise RuntimeError(
                f"expected exactly one original weaponInfo_s size comment; found {source.count(OLD_COMMENT)}"
            )
        source = source.replace(OLD_ASSERT, NEW_ASSERTS, 1)
        source = source.replace(OLD_COMMENT, NEW_COMMENT, 1)

    verify(source)
    path.write_text(source, encoding="utf-8")
    print("Updated weaponInfo_s runtime layout: ILP32=0x24, LP64=0x40; verified pointer-field offsets.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"weaponInfo_s LP64 layout transform failed: {error}", file=sys.stderr)
        raise SystemExit(1)
