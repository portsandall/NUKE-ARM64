#!/usr/bin/env python3
"""Include clientState_s where demoMain stores an array of the complete type.

Only the disposable pinned upstream checkout used by CI is modified.
"""
from __future__ import annotations

import sys
from pathlib import Path

ANCHOR = "#include <cgame_mp/cg_scoreboard_mp.h>"
INCLUDE = "#include <client_mp/client_mp.h>"
FIELD = "clientState_s client[32];"


def verify(source: str, source_path: Path) -> None:
    if source.count(INCLUDE) != 1:
        raise RuntimeError("expected exactly one client_mp.h include")
    if source.count(FIELD) != 1:
        raise RuntimeError("expected exactly one demoMain client[32] field")
    if source.index(INCLUDE) > source.index(FIELD):
        raise RuntimeError("clientState_s definition must precede its by-value field")

    client_header = source_path.parents[1] / "client_mp" / "client_mp.h"
    if not client_header.is_file():
        raise RuntimeError("client_mp/client_mp.h is missing")
    client_source = client_header.read_text(encoding="utf-8")
    if client_source.count("struct clientState_s") != 1:
        raise RuntimeError("expected one concrete clientState_s definition in client_mp.h")
    if "demo_common.h" in client_source:
        raise RuntimeError("client_mp.h unexpectedly depends on demo_common.h; refusing a possible include cycle")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <demo_common.h>", file=sys.stderr)
        return 2

    source_path = Path(sys.argv[1])
    source = source_path.read_text(encoding="utf-8")
    if INCLUDE not in source:
        if source.count(ANCHOR) != 1:
            raise RuntimeError("expected exactly one scoreboard include anchor")
        source = source.replace(ANCHOR, ANCHOR + chr(10) + INCLUDE, 1)

    verify(source, source_path)
    source_path.write_text(source, encoding="utf-8")
    print("Verified demo_common.h sees the full clientState_s definition before demoMain::client[32].")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"demo client-state header transform failed: {error}", file=sys.stderr)
        raise SystemExit(1)
