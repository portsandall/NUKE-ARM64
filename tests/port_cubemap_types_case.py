#!/usr/bin/env python3
"""Correct a case-mismatched ATI CubeMapGen header include on case-sensitive filesystems.

KisakBlack tracks src/CubeMapGenLib/Types.h, but VectorMacros.h includes
"types.h". Windows filesystems commonly hide this mismatch; Linux/Android CI
does not. This transform edits only the disposable pinned-source checkout.
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <VectorMacros.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_bytes()
    wrong = b'#include "types.h"'
    correct = b'#include "Types.h"'

    if not path.with_name("Types.h").is_file():
        raise RuntimeError(f"expected case-correct sibling header is missing: {path.with_name('Types.h')}")
    if path.with_name("types.h").exists():
        raise RuntimeError("unexpected lowercase types.h exists; refusing ambiguous transform")

    count = source.count(wrong)
    if count != 1:
        raise RuntimeError(f"expected exactly one lowercase types.h include; found {count}")
    if source.count(correct) != 0:
        raise RuntimeError("case-correct Types.h include already exists; refusing duplicate transform")

    path.write_bytes(source.replace(wrong, correct, 1))
    print(f"Corrected case-sensitive Types.h include in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
