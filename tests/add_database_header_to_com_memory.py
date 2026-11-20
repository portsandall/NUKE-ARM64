#!/usr/bin/env python3
"""Make com_memory.h include the database declarations it uses directly.

After removing a transitive renderer header, com_memory.h's declarations still
use XAssetType and XAssetHeader. Those types are defined by the platform-neutral
database/database.h, so this makes that dependency explicit.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DATABASE_INCLUDE = "#include <database/database.h>"
XANIM_INCLUDE = "#include <xanim/xanim.h>"


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} <com_memory.h> <database.h>",
            file=sys.stderr,
        )
        return 2

    header_path = Path(sys.argv[1])
    database_path = Path(sys.argv[2])
    source = header_path.read_text(encoding="utf-8")
    database = database_path.read_text(encoding="utf-8")

    if source.count("#pragma once") != 1:
        raise RuntimeError("expected exactly one #pragma once in com_memory.h")
    if source.count(XANIM_INCLUDE) != 1:
        raise RuntimeError(f"expected exactly one {XANIM_INCLUDE!r}")
    if DATABASE_INCLUDE in source:
        raise RuntimeError(f"{DATABASE_INCLUDE!r} is already present")

    db_code = re.sub(r"/\*.*?\*/|//[^\n]*", "", database, flags=re.DOTALL)
    for name in ("XAssetType", "XAssetHeader"):
        if not re.search(rf"\b{name}\b", db_code):
            raise RuntimeError(f"database/database.h does not define {name}")

    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)
    for name in ("XAssetType", "XAssetHeader"):
        if not re.search(rf"\b{name}\b", code):
            raise RuntimeError(f"com_memory.h no longer uses {name}; review transform")

    updated = source.replace("#pragma once", "#pragma once\n" + DATABASE_INCLUDE, 1)
    if updated.count(DATABASE_INCLUDE) != 1:
        raise RuntimeError("database include was not inserted exactly once")
    header_path.write_text(updated, encoding="utf-8")
    print(
        "Added the direct database/database.h dependency to com_memory.h; "
        "verified it defines XAssetType and XAssetHeader."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"com_memory.h database include fix failed: {error}", file=sys.stderr)
        raise SystemExit(1)
