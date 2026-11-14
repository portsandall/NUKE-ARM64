#!/usr/bin/env python3
"""Replace DynEntity client's broad D3D9 scene header with a narrow scene API.

The pinned DynEntity client needs only GfxBrushModel and three renderer entry
points from r_scene.h. That header also imports r_init.h and the Windows/D3D9
SDK. Keep the declaration boundary small and platform-neutral in the disposable
upstream checkout used by CI. This does not implement the Android renderer.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SOURCE_INCLUDE = "#include <gfx_d3d/r_scene.h>"
REPLACEMENT_INCLUDE = "#include <gfx_d3d/r_dynent_scene_api.h>"
EXPECTED_CALLS = {
    "R_GetBrushModel",
    "R_LinkDynEnt",
    "R_UnlinkDynEnt",
}
API_HEADER = """#pragma once

#include <DynEntity/DynEntity_gamestate.h>
#include <gfx_d3d/r_gfx.h>

// Narrow declarations used by DynEntity client linking. Implementations remain
// the responsibility of the platform renderer.
GfxBrushModel *__cdecl R_GetBrushModel(unsigned int modelIndex);
void __cdecl R_LinkDynEnt(unsigned int dynEntId, DynEntityDrawType drawType,
                          float *mins, float *maxs);
void __cdecl R_UnlinkDynEnt(unsigned int dynEntId, DynEntityDrawType drawType);
"""


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} <DynEntity_client.cpp> <new-header>",
            file=sys.stderr,
        )
        return 2

    source_path = Path(sys.argv[1])
    header_path = Path(sys.argv[2])
    source = source_path.read_text(encoding="utf-8")

    if source.count(SOURCE_INCLUDE) != 1:
        raise RuntimeError(
            f"expected exactly one {SOURCE_INCLUDE!r}; "
            f"found {source.count(SOURCE_INCLUDE)}"
        )
    if source.splitlines().count('#include "DynEntity_client.h"') != 1:
        raise RuntimeError('expected exactly one #include "DynEntity_client.h"')

    # Ensure the narrow header accounts for every renderer function used by
    # this translation unit; do not silently hide an additional D3D dependency.
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)
    called_symbols = set(re.findall(r"\b(R_[A-Za-z0-9_]+)\s*\(", code))
    missing = EXPECTED_CALLS - called_symbols
    unexpected = called_symbols - EXPECTED_CALLS
    if missing or unexpected:
        raise RuntimeError(
            f"renderer call audit changed; missing={sorted(missing)}, "
            f"unexpected={sorted(unexpected)}"
        )

    updated = source.replace(SOURCE_INCLUDE, REPLACEMENT_INCLUDE, 1)
    if SOURCE_INCLUDE in updated or updated.count(REPLACEMENT_INCLUDE) != 1:
        raise RuntimeError("r_scene.h include was not replaced exactly once")

    header_path.parent.mkdir(parents=True, exist_ok=True)
    header_path.write_text(API_HEADER, encoding="utf-8")

    header = header_path.read_text(encoding="utf-8")
    for symbol in EXPECTED_CALLS:
        if header.count(symbol) != 1:
            raise RuntimeError(f"expected exactly one declaration for {symbol}")
    for forbidden in ("Windows.h", "d3d9.h", "r_init.h", "r_scene.h"):
        if forbidden in header:
            raise RuntimeError(f"platform-heavy include leaked into narrow API: {forbidden}")

    source_path.write_text(updated, encoding="utf-8")
    print(
        "Replaced DynEntity_client.cpp's r_scene.h include with a narrow "
        "GfxBrushModel/R_GetBrushModel/R_LinkDynEnt/R_UnlinkDynEnt API; "
        "verified the complete renderer call set."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"DynEntity scene API decoupling failed: {error}", file=sys.stderr)
        raise SystemExit(1)
