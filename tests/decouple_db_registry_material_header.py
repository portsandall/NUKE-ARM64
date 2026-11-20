#!/usr/bin/env python3
"""Remove the D3D9 material implementation header from DB registry declarations.

The pinned db_registry.h uses Material and MaterialTechniqueSet only through
pointer declarations (including a pointer to XAssetPoolEntry<Material>).
The full renderer definition is not needed by these declarations. This edits
only the disposable pinned-upstream checkout used by CI.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

INCLUDE = "#include <gfx_d3d/r_material.h>"
MATERIAL_FORWARD = "struct Material;"
TECHNIQUE_FORWARD = "struct MaterialTechniqueSet;"


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <db_registry.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")

    if source.count(INCLUDE) != 1:
        raise RuntimeError(
            f"expected exactly one {INCLUDE!r}; found {source.count(INCLUDE)}"
        )
    if source.count(MATERIAL_FORWARD) != 1:
        raise RuntimeError("expected exactly one existing Material forward declaration")
    if TECHNIQUE_FORWARD in source:
        raise RuntimeError("MaterialTechniqueSet forward declaration already exists")

    # Do not replace the full definition if either material type is used by
    # value. Strip comments so documentation does not affect the audit.
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)
    if re.search(r"\bMaterial\s+(?!\*)\w+", code):
        raise RuntimeError("db_registry.h contains a non-pointer Material use")
    if re.search(r"\bMaterialTechniqueSet\s+(?!\*)\w+", code):
        raise RuntimeError("db_registry.h contains a non-pointer MaterialTechniqueSet use")

    required_declarations = (
        "void __cdecl Load_MaterialAsset(Material **material);",
        "void __cdecl Mark_MaterialAsset(Material *material);",
        "void __cdecl Mark_MaterialTechniqueSetAsset(MaterialTechniqueSet *techniqueSet);",
        "XAssetPoolEntry<Material> *__cdecl DB_GetMaterialAtIndex(unsigned int index);",
        "int __cdecl DB_GetMaterialIndex(const Material *material);",
    )
    for declaration in required_declarations:
        if source.count(declaration) != 1:
            raise RuntimeError(
                f"expected exactly one audited declaration: {declaration}"
            )

    updated = source.replace(INCLUDE + "\n", "", 1)
    updated = updated.replace(
        MATERIAL_FORWARD + "\n",
        MATERIAL_FORWARD + "\n" + TECHNIQUE_FORWARD + "\n",
        1,
    )

    if INCLUDE in updated:
        raise RuntimeError("D3D9 r_material.h include remains after transformation")
    if updated.count(MATERIAL_FORWARD) != 1 or updated.count(TECHNIQUE_FORWARD) != 1:
        raise RuntimeError("material forward-declaration set is not exact")
    active = re.sub(r"/\*.*?\*/|//[^\n]*", "", updated, flags=re.DOTALL)
    if re.search(r"\b(?:IDirect3D\w*|D3D9|D3DX)\b", active):
        raise RuntimeError("D3D renderer declarations remain in db_registry.h")

    path.write_text(updated, encoding="utf-8")
    print(
        "Removed db_registry.h's D3D9 material include; retained Material and "
        "MaterialTechniqueSet as forward-declared pointer-only types."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"DB registry material-header decoupling failed: {error}", file=sys.stderr)
        raise SystemExit(1)
