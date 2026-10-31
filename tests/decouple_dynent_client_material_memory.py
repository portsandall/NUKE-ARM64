#!/usr/bin/env python3
"""Extract MaterialMemory into a data-only header for renderer-independent users.

Pinned KisakBlack defines MaterialMemory inside r_material.h, which imports
D3D9. DynEntity_client.cpp only needs the two-field data type in its comparison
helper. Keep the declaration in a tiny header that forward-declares Material.
The renderer header still includes it for existing renderer/database users.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SCENE_API_INCLUDE = "#include <gfx_d3d/r_dynent_scene_api.h>"
MATERIAL_MEMORY_INCLUDE = "#include <gfx_d3d/r_material_memory.h>"
MATERIAL_HEADER_INCLUDE = '#include "r_material_memory.h"'
STRUCT_PATTERN = re.compile(
    r"(?m)^struct MaterialMemory // sizeof=0x8\n"
    r"\{[^\n]*\n"
    r"[ \t]*Material \*material;[^\n]*\n"
    r"[ \t]*int memory;[^\n]*\n"
    r"\};"
)
HEADER_CONTENT = """#pragma once

// Shared data-only entry; the renderer owns Material's complete definition.
struct Material;
struct MaterialMemory
{
    Material *material;
    int memory;
};
"""


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return source.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 4:
        print(
            f"usage: {Path(sys.argv[0]).name} <DynEntity_client.cpp> "
            "<r_material.h> <new-header>",
            file=sys.stderr,
        )
        return 2

    client_path, material_path, light_header_path = map(Path, sys.argv[1:])
    client = client_path.read_text(encoding="utf-8")
    material = material_path.read_text(encoding="utf-8")

    # Extract the existing definition exactly once, or accept the same already
    # transformed state on re-run. Do not silently tolerate a changed layout.
    matches = list(STRUCT_PATTERN.finditer(material))
    if len(matches) == 1:
        if light_header_path.exists():
            existing_header = light_header_path.read_text(encoding="utf-8")
            if existing_header != HEADER_CONTENT:
                raise RuntimeError("existing r_material_memory.h has unexpected contents")
        else:
            light_header_path.parent.mkdir(parents=True, exist_ok=True)
            light_header_path.write_text(HEADER_CONTENT, encoding="utf-8")
        material = material[:matches[0].start()] + material[matches[0].end():]
    elif len(matches) == 0 and light_header_path.exists():
        if light_header_path.read_text(encoding="utf-8") != HEADER_CONTENT:
            raise RuntimeError("already-extracted material-memory header changed")
    else:
        raise RuntimeError(
            f"expected one MaterialMemory definition or an already-extracted header; "
            f"found {len(matches)} definitions"
        )

    if MATERIAL_HEADER_INCLUDE not in material:
        material = replace_once(
            material, "#pragma once\n",
            "#pragma once\n\n" + MATERIAL_HEADER_INCLUDE + "\n",
            "renderer header include",
        )
    if material.count(MATERIAL_HEADER_INCLUDE) != 1:
        raise RuntimeError("r_material.h must include the data-only MaterialMemory header once")
    if STRUCT_PATTERN.search(material):
        raise RuntimeError("duplicate MaterialMemory definition remains in r_material.h")

    if MATERIAL_MEMORY_INCLUDE not in client:
        client = replace_once(
            client, SCENE_API_INCLUDE + "\n",
            SCENE_API_INCLUDE + "\n" + MATERIAL_MEMORY_INCLUDE + "\n",
            "DynEntity client data-header include",
        )
    if client.count(MATERIAL_MEMORY_INCLUDE) != 1:
        raise RuntimeError("DynEntity_client.cpp must include the data-only header once")
    if not re.search(
        r"bool\s+CompareMaterialMemory\s*\(\s*const\s+MaterialMemory\s*&\s*one\s*,\s*const\s+MaterialMemory\s*&\s*two\s*\)",
        client,
    ):
        raise RuntimeError("DynEntity client's MaterialMemory comparison signature changed")

    header = light_header_path.read_text(encoding="utf-8")
    if header != HEADER_CONTENT:
        raise RuntimeError("generated MaterialMemory header differs from the expected data layout")
    if "Windows.h" in header or "d3d9.h" in header or "r_material.h" in header:
        raise RuntimeError("D3D9 dependency leaked into the data-only header")

    material_path.write_text(material, encoding="utf-8")
    client_path.write_text(client, encoding="utf-8")
    print(
        "Extracted MaterialMemory into a D3D9-free data header; r_material.h "
        "retains the shared definition and DynEntity_client.cpp includes it "
        "without importing the renderer."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"MaterialMemory header extraction failed: {error}", file=sys.stderr)
        raise SystemExit(1)
