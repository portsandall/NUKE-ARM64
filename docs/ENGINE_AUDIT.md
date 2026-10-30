# NUKE-ARM64 native engine audit

Audit date: 2026-10-30  
Pinned upstream: [SwagSoftware/KisakBlack](https://github.com/SwagSoftware/KisakBlack) @ `306bb14a8e052a6244bd1df4e4df7d8504c04ef4`.

## Latest verified boundary

Latest verified code/workflow baseline: [`5de99e0d`](https://github.com/portsandall/NUKE-ARM64/commit/5de99e0d86b2671c5eb456c91e2b43b2ba873ed0), 2026-10-30 00:00:26 UTC.

- [ARM64 bootstrap run 535 / ID 40976878871](https://github.com/portsandall/NUKE-ARM64/actions/runs/40976878871): **all three jobs passed** — host tests, upstream patch/component checks, and Android AArch64 smoke build.
- [Angle/vector runtime regression run 535 / ID 40976878904](https://github.com/portsandall/NUKE-ARM64/actions/runs/40976878904): **passed**.
- The upstream patch job now applies patches 0001–0012, then runs [`tests/gate_upstream_windows_links.py`](https://github.com/portsandall/NUKE-ARM64/blob/main/tests/gate_upstream_windows_links.py) against the disposable pinned-upstream checkout. It deterministically places the Steam/Bink/NVAPI binary search paths and Windows import-library links behind `if(WIN32)`, asserts the exact expected library block remains in that guard, and checks that `KISAK_MP` remains a common compile definition.
- This is verified CMake source isolation plus the existing focused regression suite. The script modifies only the CI checkout of upstream; it does not alter the upstream repository.

## Verified build scope

The CI compiles the platform probe and selected portability targets, including patched bitarray/atomic/threading compatibility tests and upstream `src/universal/base64.cpp`, `src/universal/com_math_anglevectors.cpp`, a limited extracted `AxisToQuat`/`ikAxisToQuat` subset, and `src/universal/com_fileaccess.cpp`. The upstream read/write mutex regression runs on Linux under ThreadSanitizer; its Android counterpart is cross-compiled and checked as ELF64/AArch64, not executed on physical Android hardware.

The workflow **does not configure, compile, or link the complete KisakBlack root target**. Green smoke builds are not a full engine build and do not prove there is a playable APK.

## Priority blockers

1. **Compilability / platform isolation:** CMake's Windows-only MSVC flags, Win32 target properties/defines, DirectX SDK paths, vendor-library directories and Windows import libraries are now guarded in the CI patch series. This removes several configuration hazards, but the upstream root configure/link has not yet been attempted for Android. Remaining Windows APIs, runtime services, third-party dependencies and engine source assumptions still need explicit Android implementations.
2. **Physics numerical portability:** pinned `src/physics/phys_gjk.cpp` expects x87 floating-point behavior. AArch64 has no x87. Do not delete or bypass this path's guard until an AArch64 numerical implementation passes collision/GJK regression cases.
3. **LP64:** compile-time ABI checks and targeted fixes exist; no engine-wide pointer/integer conversion, structure-layout, serialization or Windows-type audit is complete.
4. **Graphics bootstrap:** no native Android game renderer is integrated into the upstream engine.
5. **Map loading:** no real `mp_nuked` asset, collision, or spawn path is implemented. The map name in the portability probe is only a scope assertion.
6. **Multiplayer:** no playable engine, session creation/joining, spawn validation or network gameplay.
7. **Performance:** no representative in-game frame-time, memory, GPU or network benchmarks.

## Next acceptance gate

Attempt the **first real Android NDK configure of the patched upstream root** in a separate diagnostic CI job. Capture the first unresolved CMake/source dependency rather than treating the current component tests as proof of engine portability. Keep that experiment non-blocking until its dependencies and expected build target are understood. Then isolate one dependency-complete gameplay/platform subsystem and require a linked ELF64/AArch64 result before moving on to native graphics or Nuketown map loading.

Before distributing upstream-derived binaries or source, confirm applicable licensing and redistribution rights. Do not describe generic FPS code or a procedural blockout as the original Black Ops port.
