#!/usr/bin/env python3
"""Extract patched upstream quaternion converters for focused regression tests.

The full com_math.cpp and ik_math.cpp translation units import engine-wide
services. This test compiles the exact patched AxisToQuat and ikAxisToQuat
bodies plus their shared vector-length helper.
"""
from pathlib import Path
import re
import sys

source_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
upstream_root = source_path.parents[2]
ik_source_path = upstream_root / "src" / "ik" / "ik_math.cpp"

# Upstream contains legacy Windows-1252 comments; latin-1 preserves bytes.
source = source_path.read_text(encoding="latin-1")
ik_source = ik_source_path.read_text(encoding="latin-1")


def extract(text: str, start_signature: str, end_signature: str) -> str:
    start = text.find(start_signature)
    if start < 0:
        raise SystemExit(f"missing upstream function: {start_signature}")
    end = text.find(end_signature, start)
    if end < 0:
        raise SystemExit(f"missing upstream function terminator: {end_signature}")
    return text[start:end].strip()


def validate_matrix_indexing(function: str, name: str) -> None:
    brace = function.find("{")
    if brace < 0:
        raise SystemExit(f"missing function body: {name}")
    body = function[brace + 1:]
    # The parameter is a pointer to three-float rows. Any (*mat)[0..8]
    # access is flattened indexing and can cross a row boundary.
    if re.search(r"\(\*mat\)\s*\[\s*[0-8]\s*\]", body):
        raise SystemExit(f"{name} still contains flattened matrix indexing")
    if "__PAIR64__" in function or "LODWORD" in function:
        raise SystemExit(f"{name} still contains architecture-specific packed assignments")


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
