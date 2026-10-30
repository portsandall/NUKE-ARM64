#!/usr/bin/env python3
"""Provide a non-x86 SnapFloat implementation without importing x86 SSE headers.

The upstream SSE conversion rounds according to the active floating-point
rounding mode (normally round-to-nearest, ties-to-even). The portable fallback
uses nearbyint, preserves the active mode, and returns INT_MIN for NaN,
infinity, or a result outside signed 32-bit range, matching CVTSS2SI's
integer-indefinite result for invalid conversions.
"""
from __future__ import annotations

import sys
from pathlib import Path

X86 = "#if defined(__i386__) || defined(__x86_64__) || defined(_M_IX86) || defined(_M_X64)"
HELPER = """#pragma once

#include <climits>
#include <cmath>

namespace nuke_port
{
inline int snapFloatToInt(float value) noexcept
{
    if (!std::isfinite(value))
        return INT_MIN;

    const double rounded = std::nearbyint(static_cast<double>(value));
    if (rounded < static_cast<double>(INT_MIN) ||
        rounded > static_cast<double>(INT_MAX))
        return INT_MIN;

    return static_cast<int>(rounded);
}
} // namespace nuke_port
"""

def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one occurrence, found {count}")
    return source.replace(old, new, 1)

def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <common.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")

    include_old = "#include <xmmintrin.h>  // SSE"
    include_new = f"""{X86}
#include <xmmintrin.h>  // SSE
#else
#include "snapfloat_rounding.h"
#endif"""
    source = replace_once(source, include_old, include_new, "architecture-gated SSE include")

    snap_float_old = """    int i;
    i = _mm_cvtss_si32(_mm_set_ss(x));
    return  static_cast<float>(i);"""
    snap_float_new = f"""{X86}
    int i;
    i = _mm_cvtss_si32(_mm_set_ss(x));
    return static_cast<float>(i);
#else
    return static_cast<float>(nuke_port::snapFloatToInt(x));
#endif"""
    source = replace_once(source, snap_float_old, snap_float_new, "SnapFloat conversion")

    snap_int_old = """    int i;
    i = _mm_cvtss_si32(_mm_set_ss(x));
    return i;"""
    snap_int_new = f"""{X86}
    int i;
    i = _mm_cvtss_si32(_mm_set_ss(x));
    return i;
#else
    return nuke_port::snapFloatToInt(x);
#endif"""
    source = replace_once(source, snap_int_old, snap_int_new, "SnapFloatToInt conversion")

    helper = path.with_name("snapfloat_rounding.h")
    if helper.exists():
        if helper.read_text(encoding="utf-8") != HELPER:
            raise RuntimeError(f"unexpected pre-existing helper: {helper}")
    else:
        helper.write_text(HELPER, encoding="utf-8")

    path.write_text(source, encoding="utf-8")
    print("Verified x86-only SSE include and portable non-x86 SnapFloat conversion.")
    print("Portable fallback preserves the active rounding mode and guards int32 overflow.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"SnapFloat portability transform failed: {error}", file=sys.stderr)
        raise SystemExit(1)
