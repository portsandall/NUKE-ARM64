#!/usr/bin/env python3
"""Remove the unused local 3DES callback that conflicts with libtomcrypt's declaration.

The descriptor referencing this stub is entirely commented out in KisakBlack.
The actual encryption path uses libtomcrypt's registered cipher implementation.
This transform applies only to the disposable pinned-source checkout used by CI.
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <bdCypher3Des.cpp>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    unused_stub = (
        "static void des3_done(symmetric_key *skey)\n"
        "{\n"
        "    //LTC_UNUSED_PARAM(skey);\n"
        "    // 3DES has no dynamic key state to free\n"
        "}\n"
    )
    count = source.count(unused_stub)
    if count != 1:
        raise RuntimeError(f"expected exactly one unused des3_done stub; found {count}")

    source = source.replace(unused_stub, "", 1)
    if "static void des3_done" in source:
        raise RuntimeError("static des3_done definition remains after transformation")

    path.write_text(source, encoding="utf-8")
    print(f"Removed unused static des3_done stub from {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
