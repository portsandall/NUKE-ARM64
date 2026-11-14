#!/usr/bin/env python3
"""Split ShaderConstantSet's POD layout from D3D9-heavy renderer declarations.

bg_local.h embeds ShaderConstantSet by value, but does not need renderer APIs.
Share the plain data layout with gameplay while leaving renderer declarations
and implementations in r_shader_constant_set.h.
"""
from __future__ import annotations

import sys
from pathlib import Path

BG_INCLUDE = "#include <gfx_d3d/r_shader_constant_set.h>"
BG_REPLACEMENT = "#include <qcommon/shader_constant_set_types.h>"
STRUCT_BLOCK = """struct ShaderConstantSet // sizeof=0x78
{                                       // XREF: cpose_t/r
    float value[7][4];
    unsigned __int8 constantSource[7];
    unsigned __int8 used;
};"""

DATA_HEADER = """#pragma once

// Renderer-independent ShaderConstantSet data shared by gameplay and renderer.
struct ShaderConstantSet // sizeof=0x78
{
    float value[7][4];
    unsigned char constantSource[7];
    unsigned char used;
};

static_assert(sizeof(ShaderConstantSet) == 0x78,
              "ShaderConstantSet serialized/runtime data layout changed");
static_assert(alignof(ShaderConstantSet) == alignof(float),
              "ShaderConstantSet alignment changed");
"""


def main() -> int:
    if len(sys.argv) != 4:
        print(
            f"usage: {Path(sys.argv[0]).name} <bg_local.h> "
            "<r_shader_constant_set.h> <new-data-header>",
            file=sys.stderr,
        )
        return 2

    bg_path, renderer_path, data_path = map(Path, sys.argv[1:])
    bg_source = bg_path.read_text(encoding="utf-8")
    renderer_source = renderer_path.read_text(encoding="utf-8")

    if bg_source.count(BG_INCLUDE) != 1:
        raise RuntimeError(
            f"expected exactly one gameplay include {BG_INCLUDE!r}; "
            f"found {bg_source.count(BG_INCLUDE)}"
        )
    if bg_source.count("ShaderConstantSet constantSet;") != 1:
        raise RuntimeError("bg_local.h no longer has the expected by-value constantSet member")
    if STRUCT_BLOCK not in renderer_source or renderer_source.count(STRUCT_BLOCK) != 1:
        raise RuntimeError("r_shader_constant_set.h ShaderConstantSet definition changed")
    if data_path.exists():
        raise RuntimeError(f"refusing to overwrite existing data header: {data_path}")

    updated_bg = bg_source.replace(BG_INCLUDE, BG_REPLACEMENT, 1)
    updated_renderer = renderer_source.replace(
        STRUCT_BLOCK,
        '#include <qcommon/shader_constant_set_types.h>',
        1,
    )

    if BG_INCLUDE in updated_bg or BG_REPLACEMENT not in updated_bg:
        raise RuntimeError("bg_local.h renderer-include replacement failed")
    if STRUCT_BLOCK in updated_renderer or updated_renderer.count(BG_REPLACEMENT) != 1:
        raise RuntimeError("renderer header did not adopt the shared ShaderConstantSet type")
    if "rb_state.h" not in updated_renderer or "r_gfx.h" not in updated_renderer:
        raise RuntimeError("renderer declarations lost their existing renderer dependencies")
    if "ShaderConstantSet" not in DATA_HEADER or "d3d9.h" in DATA_HEADER or "Windows.h" in DATA_HEADER:
        raise RuntimeError("new shared data header is not renderer-independent")

    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(DATA_HEADER, encoding="utf-8")
    bg_path.write_text(updated_bg, encoding="utf-8")
    renderer_path.write_text(updated_renderer, encoding="utf-8")

    # Re-read the written files so the check covers on-disk output, not only
    # the in-memory replacement strings.
    written_bg = bg_path.read_text(encoding="utf-8")
    written_renderer = renderer_path.read_text(encoding="utf-8")
    written_data = data_path.read_text(encoding="utf-8")
    if BG_REPLACEMENT not in written_bg or BG_INCLUDE in written_bg:
        raise RuntimeError("written bg_local.h still imports the renderer header")
    if BG_REPLACEMENT not in written_renderer or STRUCT_BLOCK in written_renderer:
        raise RuntimeError("written renderer header does not share the data-only type")
    if "d3d9.h" in written_data or "Windows.h" in written_data:
        raise RuntimeError("D3D/Windows dependency leaked into the shared type header")

    print(
        "Moved the plain ShaderConstantSet layout to qcommon; bg_local.h now "
        "imports the data-only type header instead of r_shader_constant_set.h."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ShaderConstantSet data-header split failed: {error}", file=sys.stderr)
        raise SystemExit(1)
