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



def parse_cpp_integer_literal(token: str) -> int:
    """Parse a simple signed C/C++ integer literal, including base and suffix."""
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

def validate_matrix_indexing(function: str, name: str) -> None:
    brace = function.find("{")
    if brace < 0:
        raise SystemExit(f"missing function body: {name}")
    body = function[brace + 1:]

    # Keep the converters explicit about the 3x3 row layout. Reject every
    # flattened (*mat)[N] expression, including indexes above the old [0..8]
    # range, so a future edit cannot evade this portability guard.
    if re.search(r"\(\s*\*\s*mat\s*\)\s*\[[^\]]+\]", body):
        raise SystemExit(f"{name} still contains flattened matrix indexing")

    # Also reject constant row/column indexes outside the 3x3 matrix.
    integer = r"[+-]?(?:0[xX][0-9a-fA-F]+|0[bB][01]+|0[0-7]*|[1-9][0-9]*)(?:[uUlL]*)"
    matrix_access = rf"\bmat\s*\[\s*({integer})\s*\]\s*\[\s*({integer})\s*\]"
    for row, column in re.findall(matrix_access, body):
        row_index = parse_cpp_integer_literal(row)
        column_index = parse_cpp_integer_literal(column)
        if not 0 <= row_index < 3 or not 0 <= column_index < 3:
            raise SystemExit(
                f"{name} contains out-of-range matrix index mat[{row}][{column}]"
            )

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
