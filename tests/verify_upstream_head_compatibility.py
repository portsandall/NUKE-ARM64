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
