#!/usr/bin/env python3
"""Separate the shared primary-light runtime type from the D3D9 renderer API.

com_bsp_load_obj.h only needs ComPrimaryLight's data layout, not renderer
functions. Keeping that type in a small qcommon header prevents BSP/DynEntity
loaders from importing r_rendercmds.h -> r_scene.h -> r_init.h -> Windows.h.

The same transformation sizes the runtime primary-light array using the native
LP64 object size. The BSP disk records remain fixed-width and are not changed.
"""
from __future__ import annotations

import sys
from pathlib import Path

COMMON_INCLUDE = "#include <qcommon/com_primary_light_types.h>"
RENDERER_INCLUDE = "#include <gfx_d3d/r_primarylights.h>"
STRUCT_MARKER = "struct ComPrimaryLight // sizeof=0xDC"
RUNTIME_ALLOC = 'Hunk_Alloc(sizeof(ComPrimaryLight) * diskLightCount, "Com_LoadPrimaryLights", 14);'
LEGACY_ALLOC = 'Hunk_Alloc(220 * diskLightCount, "Com_LoadPrimaryLights", 14);'
VERSION14_ALLOC = 'Hunk_Alloc(sizeof(ComPrimaryLight) * 2, "Com_LoadPrimaryLights", 14);'
LEGACY_VERSION14_ALLOC = 'Hunk_Alloc(0x1B8u, "Com_LoadPrimaryLights", 14);'


def extract_struct(source: str) -> str:
    if source.count(STRUCT_MARKER) != 1:
        raise RuntimeError("expected exactly one ComPrimaryLight runtime definition")
    start = source.index(STRUCT_MARKER)
    opening = source.index("{", start)
    depth = 0
    closing = -1
    for index in range(opening, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                closing = index
                break
    if closing < 0:
        raise RuntimeError("unterminated ComPrimaryLight definition")
    semicolon = source.find(";", closing)
    if semicolon < 0:
        raise RuntimeError("ComPrimaryLight definition is missing its terminator")
    return source[start:semicolon + 1]


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return source.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 4:
        print(
            f"usage: {Path(sys.argv[0]).name} <com_bsp_load_obj.h> "
            "<r_primarylights.h> <com_bsp_load_obj.cpp>",
            file=sys.stderr,
        )
        return 2

    bsp_header_path, renderer_header_path, bsp_source_path = map(Path, sys.argv[1:])
    bsp_header = bsp_header_path.read_text(encoding="utf-8")
    renderer_header = renderer_header_path.read_text(encoding="utf-8")
    bsp_source = bsp_source_path.read_text(encoding="utf-8")

    common_header_path = bsp_header_path.parent / "com_primary_light_types.h"

    if STRUCT_MARKER in renderer_header:
        block = extract_struct(renderer_header)
        common_header = (
            "#pragma once\n\n"
            "// Shared runtime representation used by BSP loading and the renderer.\n"
            + block
            + "\n"
        )
        if common_header_path.exists():
            existing = common_header_path.read_text(encoding="utf-8")
            if existing != common_header:
                raise RuntimeError("existing com_primary_light_types.h differs from extracted type")
        else:
            common_header_path.write_text(common_header, encoding="utf-8")
        renderer_header = replace_once(
            renderer_header, block, COMMON_INCLUDE, "renderer type extraction"
        )
    else:
        if renderer_header.count(COMMON_INCLUDE) != 1 or not common_header_path.exists():
            raise RuntimeError("renderer header is neither original nor fully transformed")

    if RENDERER_INCLUDE in bsp_header:
        bsp_header = replace_once(
            bsp_header, RENDERER_INCLUDE, COMMON_INCLUDE, "BSP header renderer decoupling"
        )
    elif bsp_header.count(COMMON_INCLUDE) != 1:
        raise RuntimeError("BSP header is neither original nor fully transformed")

    legacy_count = bsp_source.count(LEGACY_ALLOC)
    native_count = bsp_source.count(RUNTIME_ALLOC)
    if legacy_count == 2 and native_count == 0:
        bsp_source = bsp_source.replace(LEGACY_ALLOC, RUNTIME_ALLOC)
    elif not (legacy_count == 0 and native_count == 2):
        raise RuntimeError(
            f"expected two legacy or two native primary-light array allocations; "
            f"legacy={legacy_count}, native={native_count}"
        )

    legacy_v14_count = bsp_source.count(LEGACY_VERSION14_ALLOC)
    native_v14_count = bsp_source.count(VERSION14_ALLOC)
    if legacy_v14_count == 1 and native_v14_count == 0:
        bsp_source = bsp_source.replace(LEGACY_VERSION14_ALLOC, VERSION14_ALLOC)
    elif not (legacy_v14_count == 0 and native_v14_count == 1):
        raise RuntimeError(
            f"expected one legacy or native version-14 allocation; "
            f"legacy={legacy_v14_count}, native={native_v14_count}"
        )

    if RENDERER_INCLUDE in bsp_header or STRUCT_MARKER in renderer_header:
        raise RuntimeError("renderer coupling or duplicate ComPrimaryLight definition remains")
    if "Hunk_Alloc(220 * diskLightCount" in bsp_source or "Hunk_Alloc(0x1B8u" in bsp_source:
        raise RuntimeError("hard-coded IA-32 ComPrimaryLight allocation remains")

    bsp_header_path.write_text(bsp_header, encoding="utf-8")
    renderer_header_path.write_text(renderer_header, encoding="utf-8")
    bsp_source_path.write_text(bsp_source, encoding="utf-8")
    print(
        "Extracted shared ComPrimaryLight layout; decoupled com_bsp_load_obj.h from "
        "r_primarylights.h; sized BSP runtime allocations with sizeof(ComPrimaryLight)."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ComPrimaryLight LP64 portability transformation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
