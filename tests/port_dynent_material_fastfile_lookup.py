#!/usr/bin/env python3
"""Use the engine's FastFile material registry for Android rope constraints.

Material_RegisterHandle is implemented in the D3D9 renderer. Android builds
use FastFiles, so this narrowly replaces that one call with the equivalent
Material_Register_FastFile lookup while leaving the Windows path unchanged.
The edits apply only to the disposable upstream checkout used by CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

SOURCE_INCLUDE = '#include "DynEntity_load_obj.h"'
API_INCLUDE = "#include <database/db_material_fastfile.h>"
OLD_CALL = "constraint->material = Material_RegisterHandle(params->materialname, 8);"
NEW_CALL = """#if defined(__ANDROID__)
                    // Match the FastFile branch of Material_Register without importing D3D9.
                    constraint->material = DB_FindFastFileMaterial(params->materialname);
#else
                    constraint->material = Material_RegisterHandle(params->materialname, 8);
#endif"""

API_HEADER = """#pragma once

#include "database.h"

struct Material;
XAssetHeader __cdecl DB_FindXAssetHeader(XAssetType type, char *name, bool errorIfMissing, int waitTime);

// The Android game target uses FastFiles; mirror Material_Register_FastFile.
inline Material *DB_FindFastFileMaterial(const char *name)
{
    return DB_FindXAssetHeader(ASSET_TYPE_MATERIAL, const_cast<char *>(name), true, -1).material;
}
"""


def verify(source: str, header: str) -> None:
    if source.count(API_INCLUDE) != 1:
        raise RuntimeError("expected exactly one lightweight material-registry include")
    if source.count(NEW_CALL) != 1:
        raise RuntimeError("expected exactly one Android FastFile lookup block")
    if source.count(OLD_CALL) != 1:
        raise RuntimeError("expected the original renderer call only in the non-Android branch")
    if header != API_HEADER:
        raise RuntimeError("lightweight material-registry API header does not match the verified declaration")
    if "r_material.h" in header or "d3d9.h" in header.lower():
        raise RuntimeError("lightweight material-registry header must not import D3D9")


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} <DynEntity_load_obj.cpp> <db_material_fastfile.h>", file=sys.stderr)
        return 2

    source_path = Path(sys.argv[1])
    header_path = Path(sys.argv[2])
    source = source_path.read_text(encoding="utf-8")

    if NEW_CALL not in source:
        if source.count(SOURCE_INCLUDE) != 1:
            raise RuntimeError("expected exactly one DynEntity_load_obj.h include")
        if source.count(OLD_CALL) != 1:
            raise RuntimeError(f"expected exactly one original Material_RegisterHandle call; found {source.count(OLD_CALL)}")
        if API_INCLUDE in source:
            raise RuntimeError("lightweight registry include exists without the Android call transformation")
        source = source.replace(SOURCE_INCLUDE, SOURCE_INCLUDE + chr(10) + API_INCLUDE, 1)
        source = source.replace(OLD_CALL, NEW_CALL, 1)

    header_path.parent.mkdir(parents=True, exist_ok=True)
    if header_path.exists() and header_path.read_text(encoding="utf-8") != API_HEADER:
        raise RuntimeError("refusing to overwrite an unexpected existing lightweight material-registry header")
    header_path.write_text(API_HEADER, encoding="utf-8")
    verify(source, header_path.read_text(encoding="utf-8"))
    source_path.write_text(source, encoding="utf-8")
    print("Verified Android rope constraints use the FastFile material registry; Windows keeps Material_RegisterHandle.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Android DynEntity material lookup transform failed: {error}", file=sys.stderr)
        raise SystemExit(1)
