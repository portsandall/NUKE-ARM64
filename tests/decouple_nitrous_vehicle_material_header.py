#!/usr/bin/env python3
"""Remove the D3D9-heavy material header from the vehicle data declarations.

The pinned vehicle header only stores a Material pointer in vehicle_info_t.
An incomplete Material declaration is sufficient for that field and avoids
pulling r_material.h -> d3d9.h into gameplay/physics translation units.
This intentionally does not provide Material_RegisterHandle or a renderer.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

INCLUDE = "#include <gfx_d3d/r_material.h>"
REPLACEMENT = "struct Material;"


def main() -> int:
    if len(sys.argv) != 2:
        print(
            f"usage: {Path(sys.argv[0]).name} <nitrous_vehicle.h>",
            file=sys.stderr,
        )
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    if source.count(INCLUDE) != 1:
        raise RuntimeError(
            f"expected exactly one {INCLUDE!r}; found {source.count(INCLUDE)}"
        )
    if source.count(REPLACEMENT) != 0:
        raise RuntimeError("Material forward declaration already exists")

    # Verify every live Material use in this header is pointer-only. Strip
    # comments first so documentation cannot satisfy the check accidentally.
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)
    code = code.replace(INCLUDE, "")
    uses = re.findall(r"\bMaterial\b", code)
    pointer_uses = re.findall(r"\bMaterial\s*\*", code)
    if len(uses) != 1 or len(pointer_uses) != 1:
        raise RuntimeError(
            "nitrous_vehicle.h Material dependency changed: "
            f"uses={len(uses)}, pointer_uses={len(pointer_uses)}"
        )

    updated = source.replace(INCLUDE, REPLACEMENT, 1)
    if INCLUDE in updated or updated.count(REPLACEMENT) != 1:
        raise RuntimeError("vehicle Material forward-declaration replacement failed")
    if "Windows.h" in updated or "d3d9.h" in updated:
        raise RuntimeError("Windows/D3D9 include leaked into vehicle header")

    path.write_text(updated, encoding="utf-8")
    print(
        "Removed r_material.h from nitrous_vehicle.h; verified its sole "
        "Material use is the opaque Material* compassIconMaterial field."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"nitrous_vehicle.h material decoupling failed: {error}", file=sys.stderr)
        raise SystemExit(1)
