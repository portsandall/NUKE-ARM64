#!/usr/bin/env python3
"""Extract the pinned upstream AxisToQuat and its tiny vector helper for focused tests.

The full com_math.cpp translation unit imports engine-wide services. This test
compiles the exact patched function bodies while providing only the assertion
hook and vector-length helper needed to isolate the conversion algorithm.
"""
from pathlib import Path
import re
import sys

source_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
# Upstream contains legacy Windows-1252 comments; latin-1 preserves bytes
# while the extracted ASCII function bodies remain lossless.
source = source_path.read_text(encoding="latin-1")


def extract(start_signature: str, end_signature: str) -> str:
    start = source.find(start_signature)
    if start < 0:
        raise SystemExit(f"missing upstream function: {start_signature}")
    end = source.find(end_signature, start)
    if end < 0:
        raise SystemExit(f"missing upstream function terminator: {end_signature}")
    return source[start:end].strip()


vec4_length_sq = extract(
    "float __cdecl Vec4LengthSq(",
    "\nbool __cdecl Vec4IsNormalized(",
)
axis_to_quat = extract(
    "void __cdecl AxisToQuat(",
    "\nvoid __cdecl QuatLerp(",
)

# The source parameter is a pointer to rows of three floats. Reject the old
# flattened accesses rather than silently testing the unpatched implementation.
if re.search(r"\(\*mat\)\s*\[\s*[3-8]\s*\]", axis_to_quat):
    raise SystemExit("AxisToQuat still contains an out-of-row matrix index")
if "__PAIR64__" in axis_to_quat or "LODWORD" in axis_to_quat:
    raise SystemExit("AxisToQuat still contains architecture-specific packed assignments")

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
output_path.write_text(prefix + vec4_length_sq + "\n\n" + axis_to_quat + "\n", encoding="utf-8")
print(f"extracted patched AxisToQuat from {source_path} to {output_path}")
