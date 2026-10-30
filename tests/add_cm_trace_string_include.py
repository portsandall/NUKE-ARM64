#!/usr/bin/env python3
"""Declare memset where cm_trace.h's trace_t constructor uses it."""
from __future__ import annotations

import sys
from pathlib import Path

INCLUDE = "#include <string.h>"

def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <cm_trace.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    if source.count("memset(") != 1:
        raise RuntimeError(
            f"expected one memset call in cm_trace.h; found {source.count('memset(')}"
        )
    if INCLUDE in source:
        raise RuntimeError("string.h is already included; refusing duplicate transform")
    if not source.startswith("#pragma once\n"):
        raise RuntimeError("unexpected cm_trace.h prologue; refusing to insert include")

    updated = source.replace(
        "#pragma once\n",
        "#pragma once\n\n#include <string.h>\n",
        1,
    )
    path.write_text(updated, encoding="utf-8")
    verified = path.read_text(encoding="utf-8")
    if verified.count(INCLUDE) != 1 or "memset(" not in verified:
        raise RuntimeError("memset declaration check failed after transform")
    print("Added <string.h> to cm_trace.h for its memset constructor.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"cm_trace memset include transform failed: {error}", file=sys.stderr)
        raise SystemExit(1)
