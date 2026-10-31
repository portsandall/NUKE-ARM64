#!/usr/bin/env python3
"""Make the polymorphic destructible auto-activation object LP64-aware.

The callback is an ordinary runtime C++ object: it contains a vptr and a
centity_s pointer. Its IA-32 size is 12 bytes; on Android AArch64 the vptr and
member pointer are both 8 bytes, making the native object 24 bytes. The
transformation changes only the stale reverse-engineered size assertion and
exports the exact upstream declaration block for a host/Android layout probe.
"""
from __future__ import annotations

import sys
from pathlib import Path

OLD = "static_assert(sizeof(destructible_ent_aa) == 12);"
NEW = (
    'static_assert(sizeof(destructible_ent_aa) == '
    '(sizeof(void *) == 8 ? 24 : 12), '
    '"destructible_ent_aa uses native-pointer runtime storage");'
)
START = "struct phys_auto_activate_callback"
END = "struct __declspec(align(8)) gjk_entity_info_t"

REQUIRED = (
    "virtual bool has_auto_activated() = 0;",
    "virtual void auto_activate(struct broad_phase_info *) = 0;",
    "struct destructible_ent_aa : phys_auto_activate_callback",
    "centity_s *m_cent;",
    "struct dynamic_ent_aa : phys_auto_activate_callback",
    "DynEntityDef *m_dynEntDef;",
)


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} <phys_gjk_collision_detection.h> <fixture.hpp>",
            file=sys.stderr,
        )
        return 2

    header = Path(sys.argv[1])
    fixture = Path(sys.argv[2])
    source = header.read_text(encoding="utf-8")

    old_count = source.count(OLD)
    new_count = source.count(NEW)
    if old_count == 1 and new_count == 0:
        source = source.replace(OLD, NEW, 1)
        print("Updated destructible_ent_aa size assertion: IA-32=12, LP64=24")
    elif old_count == 0 and new_count == 1:
        print("destructible_ent_aa size assertion already uses native pointer width")
    else:
        raise RuntimeError(
            "expected exactly one original or transformed destructible_ent_aa assertion; "
            f"found original={old_count}, transformed={new_count}"
        )

    start = source.find(START)
    end = source.find(END, start + len(START)) if start >= 0 else -1
    if start < 0 or end < 0:
        raise RuntimeError("could not isolate the upstream auto-activation declarations")
    block = source[start:end]
    missing = [token for token in REQUIRED if token not in block]
    if missing:
        raise RuntimeError(f"upstream auto-activation declarations changed; missing: {missing}")
    if block.count(NEW) != 1:
        raise RuntimeError("fixture must contain exactly one LP64-aware destructible assertion")

    fixture_content = (
        "#pragma once\n"
        "struct centity_s;\n"
        "struct DynEntityDef;\n"
        "struct broad_phase_info;\n\n"
        + block
    )
    header.write_text(source, encoding="utf-8")
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text(fixture_content, encoding="utf-8")
    print("Extracted the exact upstream base/destructible/dynamic callback declarations for ABI testing.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"auto-activation LP64 port failed: {error}", file=sys.stderr)
        raise SystemExit(1)
