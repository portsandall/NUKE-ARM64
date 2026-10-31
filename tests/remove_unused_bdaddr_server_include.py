#!/usr/bin/env python3
"""Remove an unused server implementation include from the DemonWare address header.

bdAddr.h defines the address, NAT, security-key and endpoint types used by its
DemonWare consumers. It does not reference server_mp declarations. Including
sv_main_mp.h here drags server/client implementation headers into every
translation unit that uses bdAddr.h, including renderer and physics headers
with Windows-only dependencies and 32-bit executable-layout assertions.

This transform edits only the disposable pinned KisakBlack checkout. It fails
closed if the upstream include or the header's dependency shape changes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

INCLUDE = "#include <server_mp/sv_main_mp.h>"
SERVER_TYPES = (
    "serverStatic_t",
    "server_t",
    "client_t",
    "clientState_s",
    "netadr_t",
    "netchan_t",
    "msg_t",
)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <bdAddr.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    count = source.count(INCLUDE)
    if count != 1:
        raise RuntimeError(
            f"expected exactly one unused sv_main_mp.h include; found {count}"
        )

    updated = source.replace(INCLUDE + "\n", "", 1)
    if INCLUDE in updated:
        raise RuntimeError("server implementation include remains after transform")

    # Ensure this public header has not acquired declarations supplied by the
    # server header before continuing to remove the transitive dependency.
    code = re.sub(r"/\\*.*?\\*/|//[^\\n]*", "", updated, flags=re.DOTALL)
    for name in SERVER_TYPES:
        if re.search(rf"\\b{re.escape(name)}\\b", code):
            raise RuntimeError(
                f"bdAddr.h now references server-owned type {name}; refusing transform"
            )

    path.write_text(updated, encoding="utf-8")
    print(
        "Removed unused server_mp/sv_main_mp.h include from bdAddr.h; "
        "verified no server-owned declarations are referenced."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"bdAddr header dependency transform failed: {error}", file=sys.stderr)
        raise SystemExit(1)
