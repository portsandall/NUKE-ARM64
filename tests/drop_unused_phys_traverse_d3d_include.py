#!/usr/bin/env python3
"""Remove an unused D3D9 material-header dependency from physics traversal.

The pinned phys_traverse.h includes r_material.h but does not reference any
material, renderer, shader, texture, or Direct3D declarations from it. That
header unconditionally includes d3d9.h, which prevents Android compilation.
The transform edits only the disposable pinned-source checkout and fails
closed if the header starts using any of those declarations.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

INCLUDE = "#include <gfx_d3d/r_material.h>"
FORBIDDEN = (
    "Material", "MaterialInfo", "dmaterial_t", "GfxImage", "GfxTexture",
    "GfxStateBits", "IDirect3D", "D3D", "Shader", "Technique", "Texture",
)

def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <phys_traverse.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    if source.count(INCLUDE) != 1:
        raise RuntimeError(
            f"expected one D3D material include in {path}; found {source.count(INCLUDE)}"
        )

    code = re.sub(r"/\*[\s\S]*?\*/|//[^\n]*", "", source)
    references = [
        name for name in FORBIDDEN
        if re.search(rf"\b{re.escape(name)}\b", code)
    ]
    if references:
        raise RuntimeError(
            "phys_traverse.h now references renderer/material declarations; "
            f"refusing to remove include: {references}"
        )

    path.write_text(source.replace(INCLUDE + "\n", "", 1), encoding="utf-8")
    if INCLUDE in path.read_text(encoding="utf-8"):
        raise RuntimeError("D3D material include remains after transform")
    print("Removed unused D3D9-backed r_material.h include from phys_traverse.h.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"phys_traverse D3D dependency transform failed: {error}", file=sys.stderr)
        raise SystemExit(1)
