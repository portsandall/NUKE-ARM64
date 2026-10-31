# NUKE-ARM64 native engine audit

Audit date: 2026-10-31  
Pinned upstream: [SwagSoftware/KisakBlack](https://github.com/SwagSoftware/KisakBlack) @ `306bb14a8e052a6244bd1df4e4df7d8504c04ef4`.

## Latest verified boundary

Latest verified focused iteration: [`eaf9bbb1`](https://github.com/portsandall/NUKE-ARM64/commit/eaf9bbb1ac62dd97041567ea9ecda85b79be8e0a), on PR branch `ci/diagnose-kisakblack-android-root-20261030`.

- [ARM64 bootstrap run 41151027148](https://github.com/portsandall/NUKE-ARM64/actions/runs/41151027148): **all three jobs passed** — host tests, upstream patch/component checks, and Android AArch64 smoke build.
- [Angle/vector regression run 41151027119](https://github.com/portsandall/NUKE-ARM64/actions/runs/41151027119): **passed**.
- Added `tests/port_stringtable_lp64.py` and `tests/upstream_stringtable_lp64.cpp`. The CI transform replaces the pinned source's 32-bit-only `sizeof(StringTable) == 20` assertion with pointer-width-aware ILP32/LP64 sizes and explicit field-offset checks. Host execution and Android AArch64 compilation both passed. The active workflow and reusable template remain byte-identical.
- The transform touches only the disposable pinned-upstream checkout used by CI; it does not modify the KisakBlack repository.

## Full-engine Android diagnostic

The new non-blocking root-target diagnostic establishes a useful boundary:

- Android NDK CMake configure: `ROOT_CONFIGURE_EXIT=0`.
- Full `KisakBlack` target build: `ROOT_BUILD_EXIT=1`.
- [Diagnostic artifact from run 41151027148](https://github.com/portsandall/NUKE-ARM64/actions/runs/41151027148/artifacts/13022479567).

The StringTable size assertion no longer appears in the latest root-build errors. Remaining first-wave failures include:

- `DynEntity_load_obj.cpp`: `Material_RegisterHandle` is undeclared after D3D renderer headers are decoupled.
- LP64 size assertions still fail for `SndDriverGlobals`, `NitrousVehicle`, `centity_s`, `playerState_s`, and `weaponInfo_s`.
- `demo_common.h`: `clientState_s` is incomplete at a by-value field.
- `gfx_d3d/r_init.h`: the Windows-only renderer header still pulls in `Windows.h`.

The root configure succeeding is progress, but the full target is still not compiled or linked. The diagnostic job is intentionally non-blocking and uploads the first compiler output rather than masking the failure.

## Verified build scope

The workflow compiles the platform probe and selected upstream portability components, including Base64, angle/vector code, an extracted quaternion-conversion subset, file access, threading, DemonWare reference counting/mutexes, selected physics layouts, MSVC-style header probes, and the new StringTable LP64 layout test. Android outputs are cross-compiled and checked as ELF64/AArch64; host regressions run on the CI host. These are not a complete game build and are not physical-device runtime tests.

## Priority blockers

1. **Compilability / platform isolation:** the patched upstream root now configures for Android, but the `KisakBlack` target still fails to compile. The remaining renderer/D3D include path and missing material API declaration need explicit platform boundaries.
2. **LP64:** the StringTable runtime layout is now pointer-width-aware and tested. Other 32-bit size assertions still fail; audit each type's pointer fields, offsets, serialization and network use before changing expected sizes. Do not pack structures or widen integers blindly.
3. **Physics numerical portability:** pinned `src/physics/phys_gjk.cpp` expects x87 floating-point behavior. AArch64 has no x87. Do not remove or bypass the guard until an AArch64 numerical implementation passes collision/GJK regression cases.
4. **Graphics bootstrap:** no native Android renderer is integrated into the upstream engine.
5. **Map loading:** no real `mp_nuked` asset, collision, or spawn path is implemented. The map name in the portability probe is only a scope assertion.
6. **Multiplayer:** no playable engine, session creation/joining, spawn validation or network gameplay.
7. **Performance:** no representative in-game frame-time, memory, GPU or network benchmarks.

## Next acceptance gate

Take the smallest remaining LP64 runtime structure, starting with `SndDriverGlobals`, and replace its 32-bit-only size assumption with explicit pointer-width-aware size and offset checks. Compile the real header on host and Android before proceeding to the larger gameplay structures. In parallel, keep the missing material API and Windows renderer header isolated as separate platform-boundary tasks.

Before distributing upstream-derived binaries or source, confirm applicable licensing and redistribution rights. Do not describe generic FPS code or a procedural blockout as the original Black Ops port.
