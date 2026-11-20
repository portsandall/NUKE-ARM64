#!/usr/bin/env python3
"""Remove decompiler-era pointer-to-int returns from bdArray's fluent helpers.

The upstream bdNet.h declares the relevant clear/increaseCapacity members as
void. The local bdArray implementation returned (int)this, which only worked
on the original 32-bit address space. Make those mutators void and make the
assignment operator return bdArray& as required by normal C++ assignment
semantics. Call sites inspected in the pinned tree ignore these mutator return
values. This edits only the disposable pinned source checkout.
"""
from __future__ import annotations

import sys
from pathlib import Path

def function_span(source: str, signature: str) -> tuple[int, int, int]:
    if source.count(signature) != 1:
        raise RuntimeError(f"expected exactly one function signature {signature!r}")
    start = source.index(signature)
    opening = source.find("{", start + len(signature))
    if opening < 0:
        raise RuntimeError(f"missing function body for {signature!r}")
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
            elif ch == "\\":
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
                return start, opening, i + 1
        i += 1
    raise RuntimeError(f"unterminated function body for {signature!r}")


def rewrite_function(
    source: str,
    old_signature: str,
    new_signature: str,
    replacements: tuple[tuple[str, str, int], ...],
) -> str:
    start, opening, end = function_span(source, old_signature)
    body = source[opening + 1:end - 1]
    for old, new, expected in replacements:
        count = body.count(old)
        if count != expected:
            raise RuntimeError(
                f"{old_signature}: expected {expected} occurrences of {old!r}; found {count}"
            )
        body = body.replace(old, new)
    source = source[:start] + new_signature + source[start + len(old_signature):opening] + "{" + body + "}" + source[end:]
    return source


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <bdArray.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="latin-1")

    source = rewrite_function(
        source, "inline int clear()", "inline void clear()",
        (("return (int)this;", "return;", 1),),
    )
    source = rewrite_function(
        source, "inline int decreaseCapacity(unsigned int a2)",
        "inline void decreaseCapacity(unsigned int a2)",
        (("return (int)this;", "return;", 2),),
    )
    source = rewrite_function(
        source, "inline int increaseCapacity(unsigned int a2)",
        "inline void increaseCapacity(unsigned int a2)",
        (("return (int)this;", "return;", 1),),
    )
    source = rewrite_function(
        source, "inline int operator=(const bdArray &rhs)",
        "inline bdArray &operator=(const bdArray &rhs)",
        (
            ("return (int)this;", "return *this;", 1),
            ("return decreaseCapacity(0);", "decreaseCapacity(0);\n                return *this;", 1),
            ("return rhsSize;", "return *this;", 2),
        ),
    )

    if "(int)this" in source:
        raise RuntimeError("bdArray.h still contains a pointer-to-int return")
    if "inline void clear()" not in source:
        raise RuntimeError("clear() return type did not change to void")
    if "inline bdArray &operator=(const bdArray &rhs)" not in source:
        raise RuntimeError("assignment operator does not return bdArray&")

    path.write_text(source, encoding="latin-1")
    print(
        "Verified bdArray mutators no longer narrow this to int; "
        "operator= now returns bdArray&."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"bdArray LP64 return transform failed: {error}", file=sys.stderr)
        raise SystemExit(1)
