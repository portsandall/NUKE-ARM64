#!/usr/bin/env python3
"""Port the runtime-only convex-hull node's allocation metadata to LP64.

The pinned chull_t contains native pointers and is dynamically allocated,
linked, rendered, and freed by the physics runtime. It is not a fixed 32-byte
serialized record. Keep the original IA-32 layout, while using the native
pointer-sized layout and matching PMM size/alignment on 64-bit targets.
This edits only the disposable pinned upstream checkout used by CI.
"""
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> str:
    source = path.read_text(encoding="utf-8")
    old_count = source.count(old)
    new_count = source.count(new)
    if old_count == 1 and new_count == 0:
        source = source.replace(old, new, 1)
        path.write_text(source, encoding="utf-8")
        print(f"Updated {label}")
        return source
    if old_count == 0 and new_count == 1:
        print(f"Already updated {label}")
        return source
    raise RuntimeError(
        f"{label}: expected one original or one transformed occurrence; "
        f"found original={old_count}, transformed={new_count}"
    )


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} <phys_local.h> <phys_convex_hull.cpp>",
            file=sys.stderr,
        )
        return 2

    header = Path(sys.argv[1])
    implementation = Path(sys.argv[2])

    replace_once(
        header,
        "static_assert(sizeof(chull_t) == 0x20);",
        """static_assert(
    sizeof(chull_t) == (sizeof(void *) == 8 ? 0x38 : 0x20),
    "chull_t uses native pointers and is allocated as a runtime object");""",
        "chull_t native-pointer size assertion",
    )
    source = replace_once(
        implementation,
        "chull_t *hull = (chull_t *)PMM_ALLOC(sizeof(chull_t), 4u);",
        "chull_t *hull = (chull_t *)PMM_ALLOC(sizeof(chull_t), alignof(chull_t));",
        "chull_t allocation size/alignment",
    )
    source = replace_once(
        implementation,
        "PMM_FREE((unsigned __int8 *)first, 0x20u, 4u);",
        "PMM_FREE((unsigned __int8 *)first, sizeof(*first), alignof(chull_t));",
        "chull_t deallocation size/alignment",
    )

    if "PMM_ALLOC(sizeof(chull_t), alignof(chull_t))" not in source:
        raise RuntimeError("chull_t allocation does not use native size/alignment")
    if "PMM_FREE((unsigned __int8 *)first, sizeof(*first), alignof(chull_t))" not in source:
        raise RuntimeError("chull_t free does not match native allocation metadata")
    if "0x20u, 4u" in source:
        raise RuntimeError("stale hard-coded chull_t free metadata remains")

    print("Verified matching PMM allocation/free metadata for the native chull_t layout.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"chull_t LP64 port failed: {error}", file=sys.stderr)
        raise SystemExit(1)
