#!/usr/bin/env python3
"""Fail closed unless a CMake cache proves an Android arm64-v8a NDK configure."""

from pathlib import Path
import sys


def read_cache(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise ValueError(f"CMake cache does not exist: {path}")

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        key, separator, value = line.partition("=")
        if not separator:
            continue
        name = key.split(":", 1)[0]
        values[name] = value
    return values


def verify_android_arm64_cache(cache_path: Path) -> dict[str, str]:
    values = read_cache(cache_path)

    system = values.get("CMAKE_SYSTEM_NAME", "")
    abi = values.get("CMAKE_ANDROID_ARCH_ABI", "")
    ndk_value = values.get("CMAKE_ANDROID_NDK", "")
    toolchain_value = values.get("CMAKE_TOOLCHAIN_FILE", "")

    if system != "Android":
        raise ValueError(f"expected CMAKE_SYSTEM_NAME=Android, got {system!r}")
    if abi != "arm64-v8a":
        raise ValueError(f"expected CMAKE_ANDROID_ARCH_ABI=arm64-v8a, got {abi!r}")
    if not ndk_value:
        raise ValueError("CMAKE_ANDROID_NDK is missing from the CMake cache")
    if not toolchain_value:
        raise ValueError("CMAKE_TOOLCHAIN_FILE is missing from the CMake cache")

    ndk = Path(ndk_value).resolve()
    toolchain = Path(toolchain_value).resolve()
    expected_toolchain = (ndk / "build/cmake/android.toolchain.cmake").resolve()

    if not ndk.is_dir():
        raise ValueError(f"Android NDK directory does not exist: {ndk}")
    if not expected_toolchain.is_file():
        raise ValueError(f"Android NDK toolchain does not exist: {expected_toolchain}")
    if toolchain != expected_toolchain:
        raise ValueError(
            "CMake toolchain does not belong to CMAKE_ANDROID_NDK: "
            f"{toolchain} != {expected_toolchain}"
        )

    return {
        "system": system,
        "abi": abi,
        "ndk": str(ndk),
        "toolchain": str(toolchain),
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} CMakeCache.txt", file=sys.stderr)
        return 2
    try:
        result = verify_android_arm64_cache(Path(argv[1]))
    except (OSError, ValueError) as error:
        print(f"Android CMake cache verification failed: {error}", file=sys.stderr)
        return 1

    print(
        "Verified Android CMake target: "
        f"system={result['system']} abi={result['abi']} "
        f"ndk={result['ndk']} toolchain={result['toolchain']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
