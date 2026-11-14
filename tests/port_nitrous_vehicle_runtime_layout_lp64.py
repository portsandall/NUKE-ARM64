#!/usr/bin/env python3
"""Correct the native NitrousVehicle size assertion for LP64 builds.

NitrousVehicle is a live physics/runtime object, not a FastFile wire record.
Its 32-bit layout is 0x440 bytes; the pinned source's AArch64 diagnostic
measures 0x470 bytes because the object contains native pointers. Keep the
assertion architecture-aware instead of suppressing the layout check.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ORIGINAL = "static_assert(sizeof(NitrousVehicle) == 0x440);"
REPLACEMENT = (
    "static_assert(sizeof(NitrousVehicle) == "
    "(sizeof(void *) == 4 ? 0x440 : 0x470));"
)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <nitrous_vehicle.h>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    if source.count(ORIGINAL) != 1:
        raise RuntimeError(
            f"expected exactly one original NitrousVehicle size assertion; "
            f"found {source.count(ORIGINAL)}"
        )
    if REPLACEMENT in source:
        raise RuntimeError("LP64-aware NitrousVehicle assertion already exists")

    # Confirm this is the aligned runtime object with native pointers, not
    # an asset serialization structure whose on-disk size must remain fixed.
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)
    required = (
        r"struct\s+alignas\(16\)\s+NitrousVehicle\b",
        r"VehicleParameter\s*\*\s*m_parameter\s*;",
        r"PhysObjUserData\s*\*\s*m_phys_user_data\s*;",
        r"rigid_body_constraint_wheel\s*\*\s*m_wheels\s*\[\s*6\s*\]\s*;",
    )
    for pattern in required:
        if re.search(pattern, code) is None:
            raise RuntimeError(f"NitrousVehicle runtime-layout guard failed: {pattern}")

    updated = source.replace(ORIGINAL, REPLACEMENT, 1)
    if updated.count(REPLACEMENT) != 1 or ORIGINAL in updated:
        raise RuntimeError("NitrousVehicle LP64 assertion replacement failed")

    path.write_text(updated, encoding="utf-8")
    print(
        "Updated native NitrousVehicle size assertion: "
        "ILP32=0x440, LP64=0x470; verified aligned runtime pointer fields."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"NitrousVehicle LP64 layout transform failed: {error}", file=sys.stderr)
        raise SystemExit(1)
