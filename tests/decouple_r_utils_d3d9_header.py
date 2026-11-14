#!/usr/bin/env python3
"""Keep generic r_utils declarations free of the Windows D3D9 SDK.

R_ReleaseAndSetNULL is a COM/D3D9 helper and is used only by Windows renderer
and YUV code. The other R_* declarations in r_utils.h are platform-neutral.
Keep the helper and its SDK include available on Windows, but do not expose
that renderer-only dependency to Android or other non-Windows targets.
"""
from __future__ import annotations

import sys
from pathlib import Path

D3D_INCLUDE = "#include <d3d9.h>"
TEMPLATE_START = "template <typename T>\ninline void __cdecl R_ReleaseAndSetNULL("


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <r_utils.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")

    if source.count(D3D_INCLUDE) != 1:
        raise RuntimeError(f"expected exactly one {D3D_INCLUDE!r}")
    if source.count(TEMPLATE_START) != 1:
        raise RuntimeError("expected exactly one R_ReleaseAndSetNULL template")

    start = source.index(TEMPLATE_START)
    helper = source[start:].rstrip()
    if helper.count("R_ReleaseAndSetNULL") != 1 or not helper.endswith("}"):
        raise RuntimeError("unexpected content after R_ReleaseAndSetNULL template")
    if "IDirect3DSurface9 *var" not in helper or "var->Release()" not in helper:
        raise RuntimeError("R_ReleaseAndSetNULL no longer matches the audited D3D9 helper")

    updated = source.replace(
        D3D_INCLUDE,
        "#if defined(_WIN32)\n#include <d3d9.h>\n#endif",
        1,
    )
    start = updated.index(TEMPLATE_START)
    helper = updated[start:].rstrip()
    updated = updated[:start] + "#if defined(_WIN32)\n" + helper + "\n#endif\n"

    if updated.count("#if defined(_WIN32)") != 2:
        raise RuntimeError("expected separate Windows guards around D3D include and COM helper")
    guarded_include = "#if defined(_WIN32)\n#include <d3d9.h>\n#endif"
    if updated.count(guarded_include) != 1:
        raise RuntimeError("expected exactly one D3D9 include guarded by _WIN32")
    if not updated.endswith("#endif\n"):
        raise RuntimeError("D3D helper Windows guard was not closed")

    path.write_text(updated, encoding="utf-8")
    print("Guarded r_utils.h's D3D9 include and COM Release helper with _WIN32; generic R_* declarations remain available.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"r_utils.h D3D9 decoupling failed: {error}", file=sys.stderr)
        raise SystemExit(1)
