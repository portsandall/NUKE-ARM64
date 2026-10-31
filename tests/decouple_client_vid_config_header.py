#!/usr/bin/env python3
"""Move vidConfig_t out of the D3D9 renderer header.

cl_main_mp.h stores vidConfig_t by value but does not need renderer APIs.
Keep the renderer's public header compatible by including the shared data
header from r_init.h, while gameplay includes only the data definition.
The transformation modifies only the disposable pinned KisakBlack checkout.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

CL_RENDERER_INCLUDE = "#include <gfx_d3d/r_init.h>"
CL_DATA_INCLUDE = "#include <qcommon/vid_config_types.h>"
RINIT_DATA_INCLUDE = "#include <qcommon/vid_config_types.h>"
VIDEO_FIELD = "vidConfig_t vidConfig;"
STRUCT_RE = re.compile(
    r"(?ms)^struct __declspec\\(align\\(4\\)\\) vidConfig_t // sizeof=0x38\\n"
    r"\\{.*?^\\};\\n?"
)

DATA_HEADER = """#pragma once

#include <cstddef>
#include <cstdint>
#include <type_traits>

// Display configuration data shared by gameplay and the renderer.
// Kept independent of the Windows/D3D9 device declarations in r_init.h.
struct alignas(4) vidConfig_t
{
    std::uint32_t sceneWidth;
    std::uint32_t sceneHeight;
    std::uint32_t displayWidth;
    std::uint32_t displayHeight;
    std::uint16_t outputDisplayWidth;
    std::uint16_t outputDisplayHeight;
    std::uint32_t displayFrequency;
    bool isToolMode;
    std::int32_t isFullscreen;
    float aspectRatioWindow;
    float aspectRatioScenePixel;
    float aspectRatioDisplayPixel;
    std::uint32_t maxTextureSize;
    std::uint32_t maxTextureMaps;
    bool deviceSupportsGamma;
};

static_assert(std::is_standard_layout_v<vidConfig_t>);
static_assert(std::is_trivially_copyable_v<vidConfig_t>);
static_assert(sizeof(vidConfig_t) == 0x38);
static_assert(alignof(vidConfig_t) == 4);
static_assert(offsetof(vidConfig_t, sceneWidth) == 0x00);
static_assert(offsetof(vidConfig_t, sceneHeight) == 0x04);
static_assert(offsetof(vidConfig_t, displayWidth) == 0x08);
static_assert(offsetof(vidConfig_t, displayHeight) == 0x0C);
static_assert(offsetof(vidConfig_t, outputDisplayWidth) == 0x10);
static_assert(offsetof(vidConfig_t, outputDisplayHeight) == 0x12);
static_assert(offsetof(vidConfig_t, displayFrequency) == 0x14);
static_assert(offsetof(vidConfig_t, isToolMode) == 0x18);
static_assert(offsetof(vidConfig_t, isFullscreen) == 0x1C);
static_assert(offsetof(vidConfig_t, aspectRatioWindow) == 0x20);
static_assert(offsetof(vidConfig_t, aspectRatioScenePixel) == 0x24);
static_assert(offsetof(vidConfig_t, aspectRatioDisplayPixel) == 0x28);
static_assert(offsetof(vidConfig_t, maxTextureSize) == 0x2C);
static_assert(offsetof(vidConfig_t, maxTextureMaps) == 0x30);
static_assert(offsetof(vidConfig_t, deviceSupportsGamma) == 0x34);
"""

EXPECTED_FIELDS = (
    "sceneWidth", "sceneHeight", "displayWidth", "displayHeight",
    "outputDisplayWidth", "outputDisplayHeight", "displayFrequency",
    "isToolMode", "isFullscreen", "aspectRatioWindow",
    "aspectRatioScenePixel", "aspectRatioDisplayPixel",
    "maxTextureSize", "maxTextureMaps", "deviceSupportsGamma",
)


def transform(client_path: Path, renderer_path: Path, data_path: Path) -> None:
    client = client_path.read_text(encoding="utf-8")
    renderer = renderer_path.read_text(encoding="utf-8")

    if client.count(CL_RENDERER_INCLUDE) != 1:
        raise RuntimeError("expected exactly one cl_main_mp.h r_init.h include")
    if client.count(VIDEO_FIELD) != 1:
        raise RuntimeError("expected exactly one clientConnection_t vidConfig_t field")
    if renderer.count("struct __declspec(align(4)) vidConfig_t // sizeof=0x38") != 1:
        raise RuntimeError("expected exactly one original aligned vidConfig_t definition")
    if renderer.count(RINIT_DATA_INCLUDE) != 0:
        raise RuntimeError("shared vidConfig_t header is already present in r_init.h")
    if data_path.exists():
        raise RuntimeError(f"refusing to overwrite existing shared data header: {data_path}")

    match = STRUCT_RE.search(renderer)
    if not match:
        raise RuntimeError("could not extract the complete original vidConfig_t definition")
    original_struct = match.group(0)
    for field in EXPECTED_FIELDS:
        if len(re.findall(rf"\\b{re.escape(field)}\\b", original_struct)) != 1:
            raise RuntimeError(f"unexpected original vidConfig_t field: {field}")

    updated_client = client.replace(CL_RENDERER_INCLUDE, CL_DATA_INCLUDE, 1)
    updated_renderer = renderer[:match.start()] + renderer[match.end():]
    pragma = "#pragma once\\n"
    if updated_renderer.count(pragma) != 1:
        raise RuntimeError("expected one r_init.h pragma once")
    updated_renderer = updated_renderer.replace(
        pragma, pragma + RINIT_DATA_INCLUDE + "\\n", 1
    )

    if CL_RENDERER_INCLUDE in updated_client or updated_client.count(CL_DATA_INCLUDE) != 1:
        raise RuntimeError("client renderer include was not replaced exactly once")
    if RINIT_DATA_INCLUDE not in updated_renderer:
        raise RuntimeError("renderer header did not include the shared video type")
    if "struct __declspec(align(4)) vidConfig_t" in updated_renderer:
        raise RuntimeError("renderer header still defines vidConfig_t")
    if "vidConfig_t" not in DATA_HEADER or "Windows.h" in DATA_HEADER or "d3d9.h" in DATA_HEADER.lower():
        raise RuntimeError("shared data header is not renderer-independent")

    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(DATA_HEADER, encoding="utf-8")
    client_path.write_text(updated_client, encoding="utf-8")
    renderer_path.write_text(updated_renderer, encoding="utf-8")

    written_client = client_path.read_text(encoding="utf-8")
    written_renderer = renderer_path.read_text(encoding="utf-8")
    written_data = data_path.read_text(encoding="utf-8")
    if CL_RENDERER_INCLUDE in written_client or CL_DATA_INCLUDE not in written_client:
        raise RuntimeError("written gameplay header still imports r_init.h")
    if RINIT_DATA_INCLUDE not in written_renderer or "struct __declspec(align(4)) vidConfig_t" in written_renderer:
        raise RuntimeError("written renderer header does not use the shared video type")
    if "Windows.h" in written_data or "d3d9.h" in written_data.lower():
        raise RuntimeError("Windows/D3D9 dependency leaked into the shared type header")

    print("Moved vidConfig_t to qcommon/vid_config_types.h; cl_main_mp.h no longer imports D3D9 r_init.h.")


def main() -> int:
    if len(sys.argv) != 4:
        print(
            f"usage: {Path(sys.argv[0]).name} <cl_main_mp.h> <r_init.h> <new-data-header>",
            file=sys.stderr,
        )
        return 2
    transform(*(Path(p) for p in sys.argv[1:]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"vidConfig_t renderer-header separation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
