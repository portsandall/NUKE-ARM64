#!/usr/bin/env python3
"""Add direct platform socket and placement-new headers to two DemonWare headers.

bdAddr.h uses in_addr/inet_addr but its Winsock include is commented out.
Use Winsock on Windows and arpa/inet on POSIX. bdArray.h uses placement new
but relies on an unrelated transitive include for <new>. These changes make
the dependencies explicit without changing structure layout or behaviour.
"""
from __future__ import annotations

import sys
from pathlib import Path

OLD_SOCKET_LINE = "//#include <winsock2.h>   // inet_addr, inet_ntoa"
SOCKET_BLOCK = """#if defined(_WIN32)
#include <winsock2.h>
#else
#include <arpa/inet.h>
#endif"""
NEW_HEADER = "#include <new>"


def update_addr(path: Path) -> None:
    source = path.read_bytes()
    if source.count(OLD_SOCKET_LINE.encode("ascii")) == 1:
        source = source.replace(OLD_SOCKET_LINE.encode("ascii"), SOCKET_BLOCK.encode("ascii"), 1)
    elif source.count(SOCKET_BLOCK.encode("ascii")) == 1:
        pass
    else:
        raise RuntimeError("bdAddr.h socket include does not match the expected upstream shape")

    if source.count(SOCKET_BLOCK.encode("ascii")) != 1:
        raise RuntimeError("expected exactly one conditional socket header block")
    if b"#include <arpa/inet.h>" not in source or b"#include <winsock2.h>" not in source:
        raise RuntimeError("conditional socket headers are incomplete")
    path.write_bytes(source)


def update_array(path: Path) -> None:
    source = path.read_bytes()
    if source.count(b"#include <new>") == 0:
        anchor = b"#include <cstdint>"
        if source.count(anchor) != 1:
            raise RuntimeError("bdArray.h no longer has one cstdint include anchor")
        source = source.replace(anchor, anchor + b"\n\n#include <new>", 1)
    if source.count(b"#include <new>") != 1:
        raise RuntimeError("expected exactly one explicit <new> include")
    path.write_bytes(source)


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} <bdAddr.h> <bdArray.h>",
            file=sys.stderr,
        )
        return 2

    addr_path, array_path = map(Path, sys.argv[1:])
    update_addr(addr_path)
    update_array(array_path)
    print(
        "Verified platform socket declarations in bdAddr.h and explicit "
        "<new> dependency in bdArray.h."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"DemonWare direct-header fix failed: {error}", file=sys.stderr)
        raise SystemExit(1)
