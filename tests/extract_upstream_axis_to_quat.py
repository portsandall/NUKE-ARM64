#!/usr/bin/env python3
"""Extract patched upstream quaternion converters for focused regression tests.

The full com_math.cpp and ik_math.cpp translation units import engine-wide
services. This test compiles the exact patched AxisToQuat and ikAxisToQuat
bodies plus their shared vector-length helper.
"""
from pathlib import Path
import re
import sys


def extract(text: str, start_signature: str, end_signature: str) -> str:
    start = text.find(start_signature)
    if start < 0:
        raise SystemExit(f"missing upstream function: {start_signature}")
    end = text.find(end_signature, start)
    if end < 0:
        raise SystemExit(f"missing upstream function terminator: {end_signature}")
    return text[start:end].strip()


def strip_outer_parentheses(token: str) -> str:
    """Remove balanced parentheses that wrap the entire index expression."""
    token = token.strip()
    while len(token) >= 2 and token[0] == "(" and token[-1] == ")":
        depth = 0
        wraps_entire_expression = True
        for index, char in enumerate(token):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0 and index != len(token) - 1:
                    wraps_entire_expression = False
                    break
        if not wraps_entire_expression or depth != 0:
            break
        token = token[1:-1].strip()
    return token


def parse_cpp_integer_literal(token: str) -> int:
    """Parse a simple signed C/C++ integer literal, including base and suffix."""
    token = strip_outer_parentheses(token)
    token = re.sub(r"[uUlL]+$", "", token)
    sign = -1 if token.startswith("-") else 1
    if token[:1] in ("+", "-"):
        token = token[1:]
    if token.lower().startswith(("0x", "0b")):
        value = int(token, 0)
    elif len(token) > 1 and token.startswith("0"):
        value = int(token, 8)
    else:
        value = int(token, 10)
    return sign * value


def read_bracket_expression(text: str, open_index: int, name: str):
    """Read one balanced C++ bracket expression, including nested brackets."""
    if open_index >= len(text) or text[open_index] != "[":
        raise SystemExit(f"{name} contains malformed matrix indexing")
    depth = 0
    for index in range(open_index, len(text)):
        if text[index] == "[":
            depth += 1
        elif text[index] == "]":
            depth -= 1
            if depth == 0:
                return text[open_index + 1:index], index
    raise SystemExit(f"{name} contains an unterminated matrix index")


def validate_matrix_indexing(function: str, name: str) -> None:
    brace = function.find("{")
    if brace < 0:
        raise SystemExit(f"missing function body: {name}")
    body = function[brace + 1:]

    # Keep the converters explicit about the 3x3 row layout. Reject every
    # flattened (*mat)[N] expression, including indexes above the old [0..8]
    # range, so a future edit cannot evade this portability guard.
    if re.search(r"\(\s*\*\s*mat\s*\)\s*\[", body):
        raise SystemExit(f"{name} still contains flattened matrix indexing")

    # Walk bracket expressions instead of using [^]] regex groups: nested
    # expressions such as mat[indices[3]][0] must be recognized and rejected
    # as non-literal, not silently skipped by the validator.
    access = re.compile(r"\bmat\s*\[")
    position = 0
    while match := access.search(body, position):
        row_open = body.find("[", match.start(), match.end())
        row, row_close = read_bracket_expression(body, row_open, name)
        column_open = row_close + 1
        while column_open < len(body) and body[column_open].isspace():
            column_open += 1
        if column_open >= len(body) or body[column_open] != "[":
            raise SystemExit(f"{name} contains non-2D matrix access mat[{row}]")
        column, column_close = read_bracket_expression(body, column_open, name)

        # These converters only need constant row/column indexes. Require a
        # literal (optionally parenthesized) so computed expressions cannot
        # bypass the bounds check.
        integer = r"[+-]?(?:0[xX][0-9a-fA-F]+|0[bB][01]+|0[0-7]*|[1-9][0-9]*)(?:[uUlL]*)"
        row_literal = strip_outer_parentheses(row)
        column_literal = strip_outer_parentheses(column)
        if not re.fullmatch(integer, row_literal) or not re.fullmatch(integer, column_literal):
            raise SystemExit(
                f"{name} contains non-literal matrix index mat[{row}][{column}]"
            )
        row_index = parse_cpp_integer_literal(row_literal)
        column_index = parse_cpp_integer_literal(column_literal)
        if not 0 <= row_index < 3 or not 0 <= column_index < 3:
            raise SystemExit(
                f"{name} contains out-of-range matrix index mat[{row}][{column}]"
            )
        position = column_close + 1

    if "__PAIR64__" in function or "LODWORD" in function:
        raise SystemExit(f"{name} still contains architecture-specific packed assignments")


def main(argv=None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 2:
        raise SystemExit("usage: extract_upstream_axis_to_quat.py <com_math.cpp> <output.cpp>")

    source_path = Path(argv[0])
    output_path = Path(argv[1])
    upstream_root = source_path.parents[2]
    ik_source_path = upstream_root / "src" / "ik" / "ik_math.cpp"

    # Upstream contains legacy Windows-1252 comments; latin-1 preserves bytes.
    source = source_path.read_text(encoding="latin-1")
    ik_source = ik_source_path.read_text(encoding="latin-1")

    vec4_length_sq = extract(
        source,
        "float __cdecl Vec4LengthSq(",
        "\nbool __cdecl Vec4IsNormalized(",
    )
    axis_to_quat = extract(
        source,
        "void __cdecl AxisToQuat(",
        "\nvoid __cdecl QuatLerp(",
    )
    ik_axis_to_quat = extract(
        ik_source,
        "void __cdecl ikAxisToQuat(",
        "\nvoid __cdecl ikMat44Set(",
    )

    validate_matrix_indexing(axis_to_quat, "AxisToQuat")
    validate_matrix_indexing(ik_axis_to_quat, "ikAxisToQuat")

    prefix = """#include <math.h>
#ifndef __cdecl
#define __cdecl
#endif
#define __debugbreak() ((void)0)
bool __cdecl Assert_MyHandler(const char *, int, int, const char *, ...) {
    return true;
}
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        prefix + vec4_length_sq + "\n\n" + axis_to_quat + "\n\n" + ik_axis_to_quat + "\n",
        encoding="utf-8",
    )
    print(f"extracted patched AxisToQuat and ikAxisToQuat to {output_path}")


if __name__ == "__main__":
    main()
