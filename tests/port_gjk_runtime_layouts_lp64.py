#!/usr/bin/env python3
"""Use native LP64 sizes for runtime-allocated GJK geometry objects.

The seven GJK shape types below are allocated from phys_simple_allocator<T>
or a query allocator using sizeof(T), then freed through the same typed pool.
They contain native pointers, so the original 32-bit reverse-engineered size
comments/assertions must not constrain AArch64 runtime object layouts.

This modifies only the disposable pinned KisakBlack checkout used by CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

# (type name, original IA-32 size, observed LP64 size)
LAYOUTS = (
    ("gjk_aabb_t", 128, 144),
    ("gjk_obb_t", 160, 176),
    ("gjk_brush_t", 96, 112),
    ("gjk_partition_t", 112, 128),
    ("gjk_double_sphere_t", 144, 160),
    ("gjk_cylinder_t", 160, 176),
    ("gjk_polygon_cylinder_t", 128, 144),
)


def transform(source: str, name: str, ia32_size: int, lp64_size: int) -> str:
    old = f"static_assert(sizeof({name}) == {ia32_size});"
    new = (
        f"static_assert(sizeof({name}) == "
        f"(sizeof(void *) == 8 ? {lp64_size} : {ia32_size}), "
        f"\\"{name} uses native-pointer runtime storage\\");"
    )
    old_count = source.count(old)
    new_count = source.count(new)
    if old_count == 1 and new_count == 0:
        source = source.replace(old, new, 1)
        print(f"Updated {name}: IA-32={ia32_size}, LP64={lp64_size}")
        return source
    if old_count == 0 and new_count == 1:
        print(f"Already updated {name}")
        return source
    raise RuntimeError(
        f"{name}: expected one original or transformed assertion; "
        f"found original={old_count}, transformed={new_count}"
    )


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <phys_colgeom.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    for name, ia32_size, lp64_size in LAYOUTS:
        source = transform(source, name, ia32_size, lp64_size)

    for name, ia32_size, lp64_size in LAYOUTS:
        expected = (
            f"(sizeof(void *) == 8 ? {lp64_size} : {ia32_size})"
        )
        if expected not in source:
            raise RuntimeError(f"{name}: native pointer-size assertion missing")

    path.write_text(source, encoding="utf-8")
    print("Verified all seven runtime GJK geometry assertions use pointer-width layouts.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"GJK LP64 layout port failed: {error}", file=sys.stderr)
        raise SystemExit(1)
