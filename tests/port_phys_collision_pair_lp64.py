#!/usr/bin/env python3
"""Patch the stale IA-32 phys_collision_pair assertion and export its ABI fixture."""
from __future__ import annotations

import sys
from pathlib import Path

OLD = "static_assert(sizeof(phys_collision_pair) == 20);"
NEW = (
    'static_assert(sizeof(phys_collision_pair) == '
    '(sizeof(void *) == 8 ? 40 : 20), '
    '"phys_collision_pair uses native-pointer transient storage");'
)
START = "struct phys_collision_pair : phys_link_list_base<phys_collision_pair>"
END = ' "phys_collision_pair uses native-pointer transient storage");'


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} <rigid_body.h> <fixture.hpp>",
            file=sys.stderr,
        )
        return 2

    header = Path(sys.argv[1])
    fixture = Path(sys.argv[2])
    source = header.read_text(encoding="utf-8")
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

    start = source.find(START)
    if start < 0:
        raise RuntimeError("phys_collision_pair declaration not found")
    close = source.find(END, start)
    if close < 0:
        raise RuntimeError("transformed phys_collision_pair assertion not found")
    end = close + len(END)
    block = source[start:end]

    required = (
        "broad_phase_info *m_bpi1;",
        "broad_phase_info *m_bpi2;",
        "float m_hit_time;",
        "struct phys_gjk_cache_info *m_gjk_ci;",
        NEW,
    )
    missing = [token for token in required if token not in block]
    if missing:
        raise RuntimeError(f"upstream phys_collision_pair declaration changed: {missing}")

    fixture_content = (
        "#pragma once\n"
        "struct broad_phase_info;\n"
        "struct phys_gjk_cache_info;\n\n"
        + block
        + "\n"
    )
    header.write_text(source, encoding="utf-8")
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text(fixture_content, encoding="utf-8")
    print("Extracted the exact upstream phys_collision_pair declaration for ABI testing.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"phys_collision_pair LP64 port failed: {error}", file=sys.stderr)
        raise SystemExit(1)
