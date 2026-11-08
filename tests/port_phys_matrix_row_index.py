#!/usr/bin/env python3
"""Fix row indexing in KisakBlack's 3x3/4x3 physics matrix adapters.

The original code indexes beyond the first float[3] subarray (for example
&(*axis)[6]). The parameters are pointers to rows, so use axis[1], axis[2],
etc. This is applied only to the pinned disposable upstream checkout.
"""
from __future__ import annotations

import sys
from pathlib import Path


OLD_AXIS = """inline void __cdecl Phys_AxisToNitrousMat(float (*axis)[3], phys_mat44 *outMat)
{
    Phys_Vec3ToNitrousVec((float *)axis, &outMat->x);
    Phys_Vec3ToNitrousVec(&(*axis)[3], &outMat->y);
    Phys_Vec3ToNitrousVec(&(*axis)[6], &outMat->z);
}"""

NEW_AXIS = """inline void __cdecl Phys_AxisToNitrousMat(float (*axis)[3], phys_mat44 *outMat)
{
    Phys_Vec3ToNitrousVec(axis[0], &outMat->x);
    Phys_Vec3ToNitrousVec(axis[1], &outMat->y);
    Phys_Vec3ToNitrousVec(axis[2], &outMat->z);
}"""

OLD_MAT4 = """void __cdecl Phys_Mat4ToNitrousMat(float (*inMat)[3], phys_mat44 *outMat)
{
    Phys_Vec3ToNitrousVec((float *)inMat, &outMat->x);
    Phys_Vec3ToNitrousVec(&(*inMat)[3], &outMat->y);
    Phys_Vec3ToNitrousVec(&(*inMat)[6], &outMat->z);
    Phys_Vec3ToNitrousVec(&(*inMat)[9], &outMat->w);
}"""

NEW_MAT4 = """void __cdecl Phys_Mat4ToNitrousMat(float (*inMat)[3], phys_mat44 *outMat)
{
    Phys_Vec3ToNitrousVec(inMat[0], &outMat->x);
    Phys_Vec3ToNitrousVec(inMat[1], &outMat->y);
    Phys_Vec3ToNitrousVec(inMat[2], &outMat->z);
    Phys_Vec3ToNitrousVec(inMat[3], &outMat->w);
}"""

OLD_REVERSE = """void __cdecl Phys_NitrousMat44ToVec33(const phys_mat44 *inMat, float (*outAxis)[3])
{
    assert_mat44_initialized(*inMat);

    (*outAxis)[0] = inMat->x.x;
    (*outAxis)[1] = inMat->x.y;
    (*outAxis)[2] = inMat->x.z;
    (*outAxis)[3] = inMat->y.x;
    (*outAxis)[4] = inMat->y.y;
    (*outAxis)[5] = inMat->y.z;
    (*outAxis)[6] = inMat->z.x;
    (*outAxis)[7] = inMat->z.y;
    (*outAxis)[8] = inMat->z.z;
}"""

NEW_REVERSE = """void __cdecl Phys_NitrousMat44ToVec33(const phys_mat44 *inMat, float (*outAxis)[3])
{
    assert_mat44_initialized(*inMat);

    outAxis[0][0] = inMat->x.x;
    outAxis[0][1] = inMat->x.y;
    outAxis[0][2] = inMat->x.z;
    outAxis[1][0] = inMat->y.x;
    outAxis[1][1] = inMat->y.y;
    outAxis[1][2] = inMat->y.z;
    outAxis[2][0] = inMat->z.x;
    outAxis[2][1] = inMat->z.y;
    outAxis[2][2] = inMat->z.z;
}"""


def replace_exact(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one original function, found {count}")
    return source.replace(old, new, 1)


def extract_function(source: str, signature: str) -> str:
    if source.count(signature) != 1:
        raise RuntimeError(f"expected exactly one function signature: {signature}")
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for pos in range(brace, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[start:pos + 1]
    raise RuntimeError(f"unterminated function: {signature}")


def main() -> int:
    if len(sys.argv) != 5:
        print(
            f"usage: {Path(sys.argv[0]).name} <phys_local.h> <nitrous_vehicle.cpp> "
            "<test-template.cpp> <generated-test.cpp>",
            file=sys.stderr,
        )
        return 2

    header_path, vehicle_path, template_path, generated_path = map(Path, sys.argv[1:])
    header = header_path.read_text(encoding="utf-8")
    vehicle = vehicle_path.read_text(encoding="utf-8")

    # Validate every original before writing either source file.
    if header.count(OLD_AXIS) != 1:
        raise RuntimeError("phys_local.h: expected exactly one original Phys_AxisToNitrousMat")
    if vehicle.count(OLD_MAT4) != 1:
        raise RuntimeError("nitrous_vehicle.cpp: expected exactly one original Phys_Mat4ToNitrousMat")
    if vehicle.count(OLD_REVERSE) != 1:
        raise RuntimeError("nitrous_vehicle.cpp: expected exactly one original Phys_NitrousMat44ToVec33")

    updated_header = replace_exact(header, OLD_AXIS, NEW_AXIS, "Phys_AxisToNitrousMat")
    updated_vehicle = replace_exact(vehicle, OLD_MAT4, NEW_MAT4, "Phys_Mat4ToNitrousMat")
    updated_vehicle = replace_exact(updated_vehicle, OLD_REVERSE, NEW_REVERSE, "Phys_NitrousMat44ToVec33")

    axis_function = extract_function(updated_header, "inline void __cdecl Phys_AxisToNitrousMat")
    mat4_function = extract_function(updated_vehicle, "void __cdecl Phys_Mat4ToNitrousMat")
    reverse_function = extract_function(updated_vehicle, "void __cdecl Phys_NitrousMat44ToVec33")

    template = template_path.read_text(encoding="utf-8")
    markers = {
        "/* PHYS_AXIS_TO_NITROUS_MAT */": axis_function,
        "/* PHYS_MAT4_TO_NITROUS_MAT */": mat4_function,
        "/* PHYS_NITROUS_MAT44_TO_VEC33 */": reverse_function,
    }
    for marker, function in markers.items():
        if template.count(marker) != 1:
            raise RuntimeError(f"test template must contain exactly one {marker}")
        template = template.replace(marker, function, 1)
    if "/* PHYS_" in template:
        raise RuntimeError("unexpanded physics function marker remains in generated test")

    # Write only after all source and fixture checks have passed.
    header_path.write_text(updated_header, encoding="utf-8")
    vehicle_path.write_text(updated_vehicle, encoding="utf-8")
    generated_path.parent.mkdir(parents=True, exist_ok=True)
    generated_path.write_text(template, encoding="utf-8")
    print(
        "Patched three physics matrix adapters to use explicit row indexing; "
        "generated a regression from the transformed upstream functions."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"physics matrix row-index transform failed: {error}", file=sys.stderr)
        raise SystemExit(1)
