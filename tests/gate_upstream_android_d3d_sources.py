#!/usr/bin/env python3
"""Exclude Windows D3D9 rendering and its cubemap screenshot utility on Android.

The pinned upstream target lists both groups unconditionally. The first Android
root-build failure is CCubeMapProcessor.cpp including windows.h; code search
shows the processor is consumed by the D3D9 screenshot implementation. Android
must supply a native renderer instead of compiling this Windows renderer.
This edits only the disposable upstream checkout used by CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

MARKER = (
    "# ======================================================================\n"
    "# Build target\n"
    "# ======================================================================\n"
)
ANDROID_GUARD = (
    "# Android uses a native renderer; don't compile the Windows D3D9 renderer\n"
    "# or its D3D screenshot-only CubeMapGen utility in the Android target.\n"
    "if(ANDROID)\n"
    "    set(GFX_D3D_FILES)\n"
    "    set(CUBEMAPGENLIB_FILES)\n"
    "endif()\n\n"
)


def verify(text: str) -> None:
    if text.count(ANDROID_GUARD) != 1:
        raise RuntimeError("expected exactly one verified Android D3D source exclusion block")
    if text.count("add_executable(${BIN_NAME}") != 1:
        raise RuntimeError("expected exactly one KisakBlack executable source list")
    target_sources = text.split("add_executable(${BIN_NAME}", 1)[1]
    for variable in ("GFX_D3D_FILES", "CUBEMAPGENLIB_FILES"):
        if target_sources.count(f"\\t${{{variable}}}") != 1:
            raise RuntimeError(f"{variable} must occur exactly once in the executable source list")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <upstream-cmake_files.cmake>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    if ANDROID_GUARD not in text:
        if text.count(MARKER) != 1:
            raise RuntimeError("expected one build-target marker in pinned cmake_files.cmake")
        for variable in ("GFX_D3D_FILES", "CUBEMAPGENLIB_FILES"):
            if text.count(f"set({variable}") != 1:
                raise RuntimeError(f"expected one original definition of {variable}")
        text = text.replace(MARKER, ANDROID_GUARD + MARKER, 1)

    verify(text)
    path.write_text(text, encoding="utf-8")
    print("Verified: Windows D3D9 renderer and screenshot-only CubeMapGen sources are excluded from the Android target.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Android D3D source selection failed: {error}", file=sys.stderr)
        raise SystemExit(1)
