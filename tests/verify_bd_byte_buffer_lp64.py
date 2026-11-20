#!/usr/bin/env python3
"""Verify the LP64 bounded-string adapter is wired into the patched upstream call site."""
from __future__ import annotations

import sys
from pathlib import Path


def function_body(source: str, signature: str) -> str:
    if source.count(signature) != 1:
        raise RuntimeError(f"expected exactly one {signature!r}")
    start = source.index(signature)
    opening = source.find("{", start + len(signature))
    if opening < 0:
        raise RuntimeError("writeString body is missing")

    depth = 0
    in_line_comment = False
    in_block_comment = False
    in_string = False
    quote = ""
    escape = False
    i = opening
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
        elif in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 1
        elif in_string:
            if escape:
                escape = False
            elif ch == "\\\\":
                escape = True
            elif ch == quote:
                in_string = False
        elif ch == "/" and nxt == "/":
            in_line_comment = True
            i += 1
        elif ch == "/" and nxt == "*":
            in_block_comment = True
            i += 1
        elif ch in ("'", '"'):
            in_string = True
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1:i]
        i += 1
    raise RuntimeError("unterminated writeString body")


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} <bdByteBuffer.cpp> <compat-header>", file=sys.stderr)
        return 2

    source = Path(sys.argv[1]).read_text(encoding="latin-1")
    header = Path(sys.argv[2]).read_text(encoding="utf-8")
    signature = "bool bdByteBuffer::writeString(char *buf, unsigned int cnt)"
    body = function_body(source, signature)

    if source.count('#include <nuke/bd_byte_buffer_compat.h>') != 1:
        raise RuntimeError("patched bdByteBuffer.cpp must include the compatibility header exactly once")

    null_guard = body.find("if (!buf)")
    adapter_call = body.find("nuke::boundedCStringLength(buf, cnt)")
    if null_guard < 0 or adapter_call < 0 or null_guard > adapter_call:
        raise RuntimeError("writeString must reject a null buffer before calling the bounded adapter")
    if body.count("nuke::boundedCStringLength(buf, cnt)") != 1:
        raise RuntimeError("writeString must call the bounded adapter exactly once")

    forbidden = (
        "v3 = (int)memchr",
        "v10 = v3 - (_DWORD)buf",
        "memchr((unsigned __int8 *)buf, 0, cnt)",
    )
    for fragment in forbidden:
        if fragment in body:
            raise RuntimeError(f"legacy pointer-narrowing expression remains: {fragment}")

    for fragment in (
        "inline std::uint32_t boundedCStringLength",
        "std::memchr(buffer, '\\0', static_cast<std::size_t>(limit))",
        "if (terminator == nullptr)",
        "return limit;",
    ):
        if fragment not in header:
            raise RuntimeError(f"compatibility header is missing required bounded-length logic: {fragment}")

    print("Verified patched bdByteBuffer::writeString uses the bounded LP64 adapter after its null guard.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"bdByteBuffer LP64 integration check failed: {error}", file=sys.stderr)
        raise SystemExit(1)
