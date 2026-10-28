# NUKE-ARM64

Nuketown-only Call of Duty: Black Ops (2010) multiplayer porting project targeting Android AArch64 (arm64-v8a). **Pre-alpha portability laboratory, NOT a playable game.**

## Actual status

- Repository and native 64-bit platform probe implemented, with host tests and an installed Android NDK workflow at `.github/workflows/android-arm64.yml`.
- The default-branch workflow cross-compiles `nuke-platform-probe` and `nuke-atomic-test` for Android `arm64-v8a` and verifies both as ELF64/AArch64. CI also compiles pinned KisakBlack portability components (including `base64.cpp` and `com_math_anglevectors.cpp`) and links a focused Android AArch64 regression executable containing the angle/vector source, an extracted quaternion-conversion subset from `com_math.cpp`, and `tests/upstream_angle_vectors.cpp`. The linked executable is architecture-checked; its host counterpart runs under AddressSanitizer and UndefinedBehaviorSanitizer, alongside the quaternion-source validator tests. These checks validate only selected components and do **not** build a game APK.
- The default CMake build still does not link the full engine. There is no integrated renderer, Nuketown map loading, gameplay, or networking, and no APK on `main`.
- `mp_nuked` is the only allowed map identifier in the current probe. This is a scope assertion, not proof of map support.

## Candidate engine

Upstream: https://github.com/SwagSoftware/KisakBlack ; snapshot observed `306bb14a8e052a6244bd1df4e4df7d8504c04ef4` (2026-10-02). Do not copy upstream sources until license and required permissions have been evaluated. KisakBlack currently targets Windows/x86, requiring considerable platform and rendering changes.

## Build and run probe (Termux AArch64)

```sh
pkg install cmake ninja clang
cmake -S . -B build/termux -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/termux
ctest --test-dir build/termux --output-on-failure
./build/termux/nuke-platform-probe mp_nuked
```

The installed GitHub Actions workflow validates separate `arm64-v8a` Android NDK binaries on pushes and pull requests. A Termux binary is NOT necessarily compatible with a standalone Android app.

## Scope and gates

1. Audit candidate source, licenses, data format, build dependencies and Windows API surface.
2. Bootstrap real Black Ops multiplayer engine code on AArch64 (passing reproducible CI).
3. Replace platform services, renderer and input while preserving original network protocol and gameplay when feasible.
4. Load legally supplied original Nuketown assets, rendering and collision; verify spawn locations.
5. LAN multiplayer, host/join, dedicated server tests, Android controls and packaging.
6. Profile and optimise CPU, GPU, RAM and network performance on real Android devices.

## Asset policy

No copyrighted Black Ops map, executable or proprietary game assets are distributed by this repository. End users must provide original assets they are permitted to use. A clean-room alternative is only a separate option if the original codebase cannot be legally ported.
