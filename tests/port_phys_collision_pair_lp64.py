#!/usr/bin/env python3
"""Use native pointer-width storage for phys_collision_pair on LP64.

The object is allocated from the broad-phase transient buffer using
sizeof(phys_collision_pair) for both single-threaded and multi-threaded paths,
and linked through a native-pointer list. The 20-byte assertion is the
original IA-32 size, not a serialized/fixed-size record.
"""
from __future__ import annotations

import sys
from pathlib import Path

OLD = "static_assert(sizeof(phys_collision_pair) == 20);"
NEW = (
    'static_assert(sizeof(phys_collision_pair) == '
    '(sizeof(void *) == 8 ? 40 : 20), '
    '"phys_collision_pair uses native-pointer transient storage");'
)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <rigid_body.h>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    old_count, new_count = source.count(OLD), source.count(NEW)
    if old_count == 1 and new_count == 0:
        source = source.replace(OLD, NEW, 1)
        print("Updated phys_collision_pair size assertion: IA-32=20, LP64=40")
    elif old_count == 0 and new_count == 1:
        print("phys_collision_pair assertion already uses native pointer width")
    else:
        raise RuntimeError(
            "expected exactly one original or transformed phys_collision_pair assertion; "
            f"found original={old_count}, transformed={new_count}"
        )
    if "struct phys_collision_pair : phys_link_list_base<phys_collision_pair>" not in source:
        raise RuntimeError("phys_collision_pair inheritance/declaration changed")
    path.write_text(source, encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"phys_collision_pair LP64 port failed: {error}", file=sys.stderr)
        raise SystemExit(1)
