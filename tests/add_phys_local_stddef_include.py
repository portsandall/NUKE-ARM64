#!/usr/bin/env python3
"""Make the standard offsetof macro explicit in phys_local.h.

The pinned physics header uses offsetof(T_internal, m_data) inside a
templated free-list implementation. Its historical Windows include chain
provided offsetof indirectly; Android's C++ headers do not guarantee that.
Include the standard C definition explicitly in the disposable CI checkout.
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <phys_local.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    include = "#include <stddef.h>"
    anchor = "#include <cstring>\n"

    if source.count(include) == 1:
        print("Already has an explicit stddef include")
        return 0
    if source.count(include) != 0:
        raise RuntimeError("Unexpected duplicate or conditional stddef include")
    if source.count(anchor) != 1:
        raise RuntimeError("Expected exactly one cstring include anchor")
    if "offsetof(T_internal, m_data)" not in source:
        raise RuntimeError("Expected phys_free_list offsetof use was not found")

    source = source.replace(anchor, anchor + include + "\n", 1)
    if source.count(include) != 1:
        raise RuntimeError("Failed to add exactly one stddef include")
    path.write_text(source, encoding="utf-8")
    print("Added explicit <stddef.h> for phys_free_list offsetof")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"phys_local offsetof include fix failed: {error}", file=sys.stderr)
        raise SystemExit(1)
