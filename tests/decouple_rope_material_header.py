#!/usr/bin/env python3
"""Replace rope.h's D3D9-heavy material include with pointer forward declarations."""
from __future__ import annotations
import re
import sys
from pathlib import Path

INCLUDE = "#include <gfx_d3d/r_material.h>"
REPLACEMENT = "struct Material;\nunion GfxDrawSurf;"
EXPECTED = ("Material", "GfxDrawSurf")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <rope.h>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    if source.count(INCLUDE) != 1:
        raise RuntimeError(f"expected exactly one {INCLUDE!r}")
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)
    counts = {}
    for name in EXPECTED:
        occurrences = re.findall(rf"\b{name}\b", code)
        pointers = re.findall(rf"\b{name}\s*\*", code)
        if not occurrences or len(occurrences) != len(pointers):
            raise RuntimeError(f"{name} is not pointer-only in rope.h")
        counts[name] = len(occurrences)
    updated = source.replace(INCLUDE, REPLACEMENT, 1)
    if INCLUDE in updated or updated.count("struct Material;") != 1 or updated.count("union GfxDrawSurf;") != 1:
        raise RuntimeError("rope.h forward-declaration replacement failed")
    path.write_text(updated, encoding="utf-8")
    print(f"Removed r_material.h; verified pointer-only Material ({counts['Material']}) and GfxDrawSurf ({counts['GfxDrawSurf']}) uses.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"rope.h D3D9 decoupling failed: {error}", file=sys.stderr)
        raise SystemExit(1)
