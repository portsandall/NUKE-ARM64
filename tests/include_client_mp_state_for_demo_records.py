#!/usr/bin/env python3
"""Add the full multiplayer client-state definition to the demo header."""
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: include_client_mp_state_for_demo_records.py DEMO_HEADER CLIENT_HEADER")

    demo_header = Path(sys.argv[1])
    client_header = Path(sys.argv[2])
    if not demo_header.is_file() or not client_header.is_file():
        raise SystemExit("required upstream header is missing")

    client_source = client_header.read_text(encoding="utf-8")
    if "struct clientState_s" not in client_source:
        raise SystemExit("client_mp.h does not define clientState_s")

    include = "#include <client_mp/client_mp.h>"
    demo_source = demo_header.read_text(encoding="utf-8")
    count = demo_source.count(include)
    if count == 0:
        anchor = "#pragma once"
        if demo_source.count(anchor) != 1:
            raise SystemExit("demo_common.h does not have a unique #pragma once anchor")
        demo_source = demo_source.replace(anchor, anchor + "\\n" + include, 1)
        demo_header.write_text(demo_source, encoding="utf-8")
    elif count != 1:
        raise SystemExit("demo_common.h contains duplicate client_mp.h includes")

    verified = demo_header.read_text(encoding="utf-8")
    if verified.count(include) != 1 or not verified.startswith("#pragma once\\n" + include):
        raise SystemExit("client-state include insertion did not verify")
    print("Verified demo_common.h includes the complete clientState_s definition")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
