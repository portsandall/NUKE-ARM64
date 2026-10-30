#!/usr/bin/env python3
"""Apply narrowly scoped Windows-only CMake guards to the pinned KisakBlack checkout.

This changes only the disposable upstream checkout used by CI, never the upstream
repository. Exact unique anchors are required so source drift fails loudly.
"""
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one unguarded block; found {count}")
    return text.replace(old, new, 1)


def gate_vendor_paths(text: str) -> str:
    shared = 'target_link_directories(KisakBlack PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src/libs/libvpx-1.5.0")'
    vendor = [
        'target_link_directories(KisakBlack PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src/steam/redistributable_bin")',
        'target_link_directories(KisakBlack PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src/binklib")',
        'target_link_directories(KisakBlack PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src/nvapi")',
    ]
    old = "\n".join([shared, *vendor])
    new = "\n".join([
        shared,
        "if(WIN32)",
        *("    " + line for line in vendor),
        "endif()",
    ])
    if new in text:
        return text
    return replace_once(text, old, new, "Windows vendor library search paths")


def gate_import_libraries(text: str) -> str:
    heading = "# ----- Links -----\n"
    release = "target_link_libraries(KisakBlack PUBLIC $<$<CONFIG:Release>:d3dx9.lib>)"
    if text.count(heading) != 1 or text.count(release) != 1:
        raise RuntimeError("Windows import-library block anchors are missing or ambiguous")

    start = text.index(heading)
    end = text.index(release, start) + len(release)
    block = text[start:end]
    if block.startswith(heading + "if(WIN32)\n") and text[end:].startswith("\nendif()"):
        return text

    new_block = block.replace(heading, heading + "if(WIN32)\n", 1) + "\nendif()"
    return text[:start] + new_block + text[end:]


def verify(text: str) -> None:
    lines = text.splitlines()
    vendor_markers = (
        'target_link_directories(KisakBlack PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src/steam/redistributable_bin")',
        'target_link_directories(KisakBlack PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src/binklib")',
        'target_link_directories(KisakBlack PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src/nvapi")',
    )
    locations = [[i for i, line in enumerate(lines) if line.strip() == marker] for marker in vendor_markers]
    if not all(len(found) == 1 for found in locations):
        raise RuntimeError("Expected exactly one of each Windows vendor search path")
    first = locations[0][0]
    if lines[first - 1].strip() != "if(WIN32)":
        raise RuntimeError("Vendor search paths are not inside if(WIN32)")
    if [lines[first + j].strip() for j in range(3)] != list(vendor_markers):
        raise RuntimeError("Vendor search path order changed")
    if lines[first + 3].strip() != "endif()":
        raise RuntimeError("Vendor search path guard does not close")

    start = text.index("# ----- Links -----\n")
    release = "target_link_libraries(KisakBlack PUBLIC $<$<CONFIG:Release>:d3dx9.lib>)"
    end = text.index(release, start) + len(release)
    block = text[start:end]
    if not block.startswith("# ----- Links -----\nif(WIN32)\n"):
        raise RuntimeError("Windows import libraries are not gated by if(WIN32)")
    required = (
        "steam_api.lib", "binkw32.lib", "nvapi.lib", "d3d9.lib",
        "ws2_32.lib", "dxguid.lib", "dsound.lib", "winmm.lib",
        "xinput.lib", "xapobase.lib", "dxerr.lib", "libvpx.lib",
        "legacy_stdio_definitions.lib", "d3dx9d.lib", "d3dx9.lib",
    )
    for library in required:
        if library not in block:
            raise RuntimeError(f"Expected Windows library missing from gated block: {library}")
    if not text[end:].startswith("\nendif()"):
        raise RuntimeError("Windows import-library guard does not close before MSVC-only options")

    # Preserve the common multiplayer build define; only Windows compatibility
    # defines are excluded from non-Windows builds.
    if "target_compile_definitions(KisakBlack PUBLIC\n    KISAK_MP\n)" not in text:
        raise RuntimeError("KISAK_MP must remain a common compile definition")
    print("Verified: Windows-only Steam/Bink/NVAPI search paths and import libraries are gated.")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <upstream-CMakeLists.txt>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    text = gate_vendor_paths(text)
    text = gate_import_libraries(text)
    verify(text)
    path.write_text(text, encoding="utf-8")
    print(f"Applied verified Android-facing CMake isolation guards to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
