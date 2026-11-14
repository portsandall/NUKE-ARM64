#!/usr/bin/env python3
"""Use native LP64 size for the runtime-allocated GJK cache node.

The cache node is allocated and freed by PMM at several sites in
phys_broad_phase.cpp. Keep the IA-32 size, but derive all operational
allocation metadata from sizeof(T) on every architecture. This modifies only
the disposable pinned KisakBlack checkout used by CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

TYPE = "phys_heap_gjk_cache_system_avl_tree::phys_gjk_cache_info_internal"
SIZE = f"sizeof({TYPE})"


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    source = path.read_text(encoding="utf-8")
    old_count = source.count(old)
    new_count = source.count(new)
    if old_count == 1 and new_count == 0:
        source = source.replace(old, new, 1)
        path.write_text(source, encoding="utf-8")
        print(f"Updated {label}")
    elif old_count == 0 and new_count == 1:
        print(f"Already updated {label}")
    else:
        raise RuntimeError(
            f"{label}: expected one original or transformed occurrence; "
            f"found original={old_count}, transformed={new_count}"
        )


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <KisakBlack checkout>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1])
    header = root / "src/physics/phys_gjk.h"
    implementation = root / "src/physics/phys_broad_phase.cpp"
    if not header.is_file() or not implementation.is_file():
        raise RuntimeError("pinned GJK cache source files are missing")

    replace_once(
        header,
        f"static_assert(sizeof({TYPE}) == 0x90);",
        f"""static_assert(
    sizeof({TYPE}) == (sizeof(void *) == 8 ? 0xA0 : 0x90),
    "GJK cache nodes use native-pointer runtime storage");""",
        "GJK cache node size assertion",
    )

    replacements = (
        (
            "PMM_VALIDATE(v4, 0x90u, 0x10u);",
            f"PMM_VALIDATE(v4, {SIZE}, 0x10u);",
            "GJK cache validation through v4",
        ),
        (
            "PMM_FREE((unsigned __int8 *)v4, 0x90u, 0x10u);",
            f"PMM_FREE((unsigned __int8 *)v4, {SIZE}, 0x10u);",
            "GJK cache free through v4",
        ),
        (
            "PMM_ALLOC(0x90u, 0x10u);",
            f"PMM_ALLOC({SIZE}, 0x10u);",
            "GJK cache allocation",
        ),
        (
            "PMM_VALIDATE(m_gjk_ci, 0x90u, 0x10u);",
            f"PMM_VALIDATE(m_gjk_ci, {SIZE}, 0x10u);",
            "GJK cache validation through m_gjk_ci",
        ),
        (
            "PMM_FREE((unsigned __int8 *)m_gjk_ci, 0x90u, 0x10u);",
            f"PMM_FREE((unsigned __int8 *)m_gjk_ci, {SIZE}, 0x10u);",
            "GJK cache free through m_gjk_ci",
        ),
        (
            "PMM_VALIDATE(v21, 0x90u, 0x10u);",
            f"PMM_VALIDATE(v21, {SIZE}, 0x10u);",
            "GJK cache validation through v21",
        ),
        (
            "PMM_FREE((unsigned __int8 *)v21, 0x90u, 0x10u);",
            f"PMM_FREE((unsigned __int8 *)v21, {SIZE}, 0x10u);",
            "GJK cache free through v21",
        ),
        (
            "PMM_VALIDATE(v31, 0x90u, 0x10u);",
            f"PMM_VALIDATE(v31, {SIZE}, 0x10u);",
            "GJK cache validation through v31",
        ),
        (
            "PMM_FREE((unsigned __int8 *)v31, 0x90u, 0x10u);",
            f"PMM_FREE((unsigned __int8 *)v31, {SIZE}, 0x10u);",
            "GJK cache free through v31",
        ),
    )
    for old, new, label in replacements:
        replace_once(implementation, old, new, label)

    header_text = header.read_text(encoding="utf-8")
    impl_text = implementation.read_text(encoding="utf-8")
    if "sizeof(void *) == 8 ? 0xA0 : 0x90" not in header_text:
        raise RuntimeError("native LP64 GJK cache assertion is missing")
    for expression in (
        f"PMM_ALLOC({SIZE}, 0x10u);",
        f"PMM_VALIDATE(v4, {SIZE}, 0x10u);",
        f"PMM_FREE((unsigned __int8 *)v4, {SIZE}, 0x10u);",
        f"PMM_VALIDATE(m_gjk_ci, {SIZE}, 0x10u);",
        f"PMM_FREE((unsigned __int8 *)m_gjk_ci, {SIZE}, 0x10u);",
        f"PMM_VALIDATE(v21, {SIZE}, 0x10u);",
        f"PMM_FREE((unsigned __int8 *)v21, {SIZE}, 0x10u);",
        f"PMM_VALIDATE(v31, {SIZE}, 0x10u);",
        f"PMM_FREE((unsigned __int8 *)v31, {SIZE}, 0x10u);",
    ):
        if expression not in impl_text:
            raise RuntimeError(f"native GJK cache allocation metadata missing: {expression}")

    print("Verified native GJK cache size and matching PMM allocation/free metadata.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"GJK cache LP64 port failed: {error}", file=sys.stderr)
        raise SystemExit(1)
