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
        if separator:
            values[key.split(":", 1)[0]] = value
    return values


def verify_android_arm64_cache(cache_path: Path) -> dict[str, str]:
    values = read_cache(cache_path)

    # CMAKE_SYSTEM_NAME is not guaranteed to be persisted in CMakeCache.txt
    # by every NDK/CMake version. If present, it must identify Android.
    system = values.get("CMAKE_SYSTEM_NAME", "")
    if system and system != "Android":
        raise ValueError(f"expected CMAKE_SYSTEM_NAME=Android, got {system!r}")

    abi = values.get("CMAKE_ANDROID_ARCH_ABI") or values.get("ANDROID_ABI", "")
    if abi != "arm64-v8a":
        raise ValueError(f"expected Android ABI arm64-v8a, got {abi!r}")

    toolchain_value = values.get("CMAKE_TOOLCHAIN_FILE", "")
    if not toolchain_value:
        raise ValueError("CMAKE_TOOLCHAIN_FILE is missing from the CMake cache")

    toolchain = Path(toolchain_value).resolve()
    expected_suffix = Path("build/cmake/android.toolchain.cmake")
    if toolchain.name != expected_suffix.name or toolchain.parent.name != "cmake" or toolchain.parent.parent.name != "build":
        raise ValueError(f"unexpected Android NDK toolchain path: {toolchain}")

    ndk = toolchain.parents[2]
    if not (ndk / "source.properties").is_file():
        raise ValueError(f"toolchain parent does not contain an Android NDK: {ndk}")

    cached_ndk = values.get("CMAKE_ANDROID_NDK") or values.get("ANDROID_NDK")
    if cached_ndk and Path(cached_ndk).resolve() != ndk.resolve():
        raise ValueError(
            "CMake NDK and toolchain paths disagree: "
            f"{Path(cached_ndk).resolve()} != {ndk.resolve()}"
        )

    return {
        "system": system or "Android (verified by NDK toolchain)",
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
