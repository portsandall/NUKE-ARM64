#!/usr/bin/env python3
"""Replace xanim.h's D3D9 include with forward declarations for pointer fields."""
from __future__ import annotations
import re
import sys
from pathlib import Path

INCLUDE = "#include <d3d9.h>"
INTERFACES = ("IDirect3DVertexBuffer9", "IDirect3DIndexBuffer9")
REPLACEMENT = "struct IDirect3DVertexBuffer9;\nstruct IDirect3DIndexBuffer9;"


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <xanim.h>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    if source.count(INCLUDE) != 1:
        raise RuntimeError(f"expected exactly one {INCLUDE!r}")
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)
    found = set(re.findall(r"\bIDirect3D[A-Za-z0-9_]+\b", code))
    if found != set(INTERFACES):
        raise RuntimeError(f"unexpected active D3D interface types in xanim.h: {sorted(found)}")
    for name in INTERFACES:
        occurrences = re.findall(rf"\b{name}\b", code)
        pointers = re.findall(rf"\b{name}\s*\*", code)
        if len(occurrences) != 1 or len(pointers) != 1:
            raise RuntimeError(f"{name} is not a single pointer-only use in xanim.h")
    updated = source.replace(INCLUDE, REPLACEMENT, 1)
    if INCLUDE in updated:
        raise RuntimeError("d3d9.h remains in xanim.h")
    path.write_text(updated, encoding="utf-8")
    print("Replaced d3d9.h with forward declarations for the two pointer-only XSurface interfaces.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"xanim.h D3D9 decoupling failed: {error}", file=sys.stderr)
        raise SystemExit(1)
