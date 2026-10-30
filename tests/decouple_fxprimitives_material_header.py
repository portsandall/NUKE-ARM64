#!/usr/bin/env python3
"""Decouple platform-neutral FX primitive declarations from the D3D9 material header.

The pinned fxprimitives.h only stores Material pointers. Pulling in r_material.h
therefore leaks the Windows-only d3d9.h dependency into gameplay headers such
as DynEntity_client.h. This transform edits only the disposable CI checkout.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MATERIAL_INCLUDE = '#include "r_material.h"'
MATERIAL_FORWARD_DECL = "struct Material;"


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
    # complete D3D9-backed declaration with a forward declaration.
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)
    material_names = re.findall(r"\bMaterial\b", code)
    material_pointers = re.findall(r"\bMaterial\s*\*", code)
    if not material_names or len(material_names) != len(material_pointers):
        raise RuntimeError(
            "fxprimitives.h contains a non-pointer Material use; "
            "a forward declaration would be unsafe"
        )

    updated = source.replace(MATERIAL_INCLUDE, MATERIAL_FORWARD_DECL, 1)
    if MATERIAL_INCLUDE in updated:
        raise RuntimeError("D3D9 material header include remains after transform")
    if updated.count(MATERIAL_FORWARD_DECL) != 1:
        raise RuntimeError("expected exactly one Material forward declaration")

    path.write_text(updated, encoding="utf-8")
    print(
        f"Replaced D3D9-backed r_material.h include with a Material forward "
        f"declaration; verified {len(material_pointers)} pointer-only uses."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"FX primitive header decoupling failed: {error}", file=sys.stderr)
        raise SystemExit(1)
