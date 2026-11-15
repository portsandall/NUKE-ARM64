#!/usr/bin/env python3
"""Verify the known upstream-head build-graph snapshot without modifying it."""

from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <KisakBlack checkout>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1])
    cmake_path = root / "CMakeLists.txt"
    modules_path = root / ".gitmodules"
    if not cmake_path.is_file() or not modules_path.is_file():
        print("FAIL: not a complete KisakBlack checkout", file=sys.stderr)
        return 2

    cmake = cmake_path.read_text(encoding="utf-8")
    modules = modules_path.read_text(encoding="utf-8")

    snapshot_paths = {
        "math": root / "src" / "universal" / "com_math.h",
        "ik": root / "src" / "ik" / "ik.h",
        "trace": root / "src" / "qcommon" / "cm_trace.h",
        "traverse": root / "src" / "physics" / "phys_traverse.h",
        "vehicle_source": root / "src" / "cgame" / "cg_vehicle.cpp",
        "vehicle_snapshot": root / "src" / "cgame_mp" / "cg_snapshot_mp.cpp",
        "vehicle_header": root / "src" / "game" / "g_scr_vehicle.h",
        "actor_corpse": root / "src" / "game" / "actor_corpse.cpp",
    }
    missing = [str(path.relative_to(root)) for path in snapshot_paths.values() if not path.is_file()]
    if missing:
        print("FAIL: latest upstream snapshot files missing: " + ", ".join(missing), file=sys.stderr)
        return 2
    source = {
        name: path.read_text(encoding="utf-8")
        for name, path in snapshot_paths.items()
    }

    checks = {
        "TreyBO is declared as a Git submodule": (
            '[submodule "TreyBO"]' in modules
            and "path = TreyBO" in modules
            and "url = https://github.com/SwagSoftware/TreyBO" in modules
        ),
        "root CMake requires and adds TreyBO": (
            'TreyBO/CMakeLists.txt' in cmake
            and "add_subdirectory(TreyBO)" in cmake
            and "target_link_libraries(KisakBlack PUBLIC treybo)" in cmake
        ),
        "legacy DemonWare tree is absent": not (root / "DemonWare").exists(),
        "legacy Live tree is absent": not (root / "src" / "live").exists(),
        "Windows compile definition remains": (
            "target_compile_definitions(KisakBlack PUBLIC" in cmake
            and "\n    WIN32\n" in cmake
        ),
        "MSVC runtime and x86 linker assumptions remain": (
            "/MT" in cmake and "/machine:x86" in cmake
        ),
        "DirectX x86 path and D3D9 link remain": (
            "Lib/x86" in cmake and "d3d9.lib" in cmake
        ),
        "Steam, Bink and NVAPI link assumptions remain": all(
            token in cmake
            for token in ("steam_api.lib", "binkw32.lib", "nvapi.lib")
        ),
        "float4 keeps the retail 4-byte alignment": (
            "union float4" in source["math"]
            and "union alignas(16) float4" not in source["math"]
            and "static_assert(alignof(hybrid_vector) == 4);" in source["math"]
        ),
        "IKState keeps its 0xE60 size assertion": (
            "static_assert(sizeof(IKState) == 0xE60);" in source["ik"]
        ),
        "trace and collision visitor keep retail size assertions": (
            "static_assert(sizeof(trace_t) == 0x38);" in source["trace"]
            and "static_assert(sizeof(colgeom_visitor_t) == 0x70);" in source["traverse"]
        ),
        "vehicle cache allocation and free use the declared type size": (
            "MT_Alloc(sizeof(vehicle_cache_t)" in source["vehicle_source"]
            and "sizeof(vehicle_cache_t)" in source["vehicle_snapshot"]
            and "static_assert(sizeof(vehicle_cache_t) == 0x788);" in source["vehicle_header"]
        ),
        "actor corpse references use typed entnum fields": (
            ".entnum" in source["actor_corpse"]
            and "1504 *" not in source["actor_corpse"]
        ),
    }

    failed = []
    for label, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
        if not passed:
            failed.append(label)

    if failed:
        print(f"Upstream snapshot drift: {len(failed)} check(s) require review.")
        return 1

    print("Upstream-head snapshot verified; this is an inventory check, not an Android build.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
