#!/usr/bin/env python3
"""Decouple FX primitive declarations from the Windows-only D3D9 material header.

The pinned fxprimitives.h uses Material only as pointer fields. Its other
transitive types come from the platform-neutral database and gfx headers.
This edits only the disposable pinned-upstream checkout used by CI.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MATERIAL_INCLUDE = '#include "r_material.h"'
REPLACEMENT = (
    "#include <database/database.h>\n"
    "#include <gfx_d3d/r_gfx.h>\n"
    "struct Material;"
)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <fxprimitives.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")

    if source.count(MATERIAL_INCLUDE) != 1:
        raise RuntimeError(
            f"expected exactly one {MATERIAL_INCLUDE!r}; "
            f"found {source.count(MATERIAL_INCLUDE)}"
        )
    if source.count("#include <universal/q_shared.h>") != 1:
        raise RuntimeError("expected the shared q_shared.h include exactly once")

    # Require every Material use to be pointer-only before replacing its
    # complete D3D9-backed definition with a forward declaration.
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)
    material_names = re.findall(r"\bMaterial\b", code)
    material_pointers = re.findall(r"\bMaterial\s*\*", code)
    if not material_names or len(material_names) != len(material_pointers):
        raise RuntimeError(
            "fxprimitives.h contains a non-pointer Material use; "
            "a forward declaration would be unsafe"
        )

    updated = source.replace(MATERIAL_INCLUDE, REPLACEMENT, 1)
    if MATERIAL_INCLUDE in updated:
        raise RuntimeError("D3D9 material header include remains after transform")
    for required in (
        "#include <database/database.h>",
        "#include <gfx_d3d/r_gfx.h>",
        "struct Material;",
    ):
        if updated.count(required) != 1:
            raise RuntimeError(f"expected exactly one {required!r}")
    if "d3d9.h" in updated:
        raise RuntimeError("D3D9 header leaked into the platform-neutral FX header")

    path.write_text(updated, encoding="utf-8")
    print(
        "Replaced r_material.h with database/database.h, gfx_d3d/r_gfx.h, "
        f"and a Material forward declaration; verified {len(material_pointers)} "
        "pointer-only Material uses."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"FX primitive header decoupling failed: {error}", file=sys.stderr)
        raise SystemExit(1)
