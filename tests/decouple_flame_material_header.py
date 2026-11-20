#!/usr/bin/env python3
"""Replace flame_system.h's D3D9-heavy material include with a forward declaration.

The pinned flame header uses Material only in pointer fields and pointer
parameters. The full Material definition is not needed to declare that API.
This edits only the disposable pinned-upstream checkout used by CI.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

INCLUDE = "#include <gfx_d3d/r_material.h>"
REPLACEMENT = "struct Material;"


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <flame_system.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")

    if source.count(INCLUDE) != 1:
        raise RuntimeError(
            f"expected exactly one {INCLUDE!r}; found {source.count(INCLUDE)}"
        )

    # A forward declaration is sufficient only when every active Material use
    # is a pointer. Strip comments before checking so documentation is ignored.
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)
    material_uses = re.findall(r"\bMaterial\b", code)
    material_pointers = re.findall(r"\bMaterial\s*\*", code)
    if not material_uses or len(material_uses) != len(material_pointers):
        raise RuntimeError(
            "flame_system.h has a non-pointer Material use; forward declaration unsafe"
        )

    updated = source.replace(INCLUDE, REPLACEMENT, 1)
    if INCLUDE in updated or updated.count(REPLACEMENT) != 1:
        raise RuntimeError("r_material.h replacement did not occur exactly once")
    if re.search(r"\b(?:IDirect3D|D3D9|D3DX)", re.sub(r"//[^\n]*", "", updated)):
        raise RuntimeError("unexpected active D3D declarations remain in flame_system.h")

    path.write_text(updated, encoding="utf-8")
    print(
        "Replaced r_material.h with struct Material; "
        f"verified all {len(material_pointers)} Material uses are pointers."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"flame_system.h material decoupling failed: {error}", file=sys.stderr)
        raise SystemExit(1)
