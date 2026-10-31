# NUKE-ARM64 native engine audit

Audit date: 2026-11-01  
Pinned upstream: [SwagSoftware/KisakBlack](https://github.com/SwagSoftware/KisakBlack) @ `306bb14a8e052a6244bd1df4e4df7d8504c04ef4`.

## Repository and CI boundary

- Default branch `main`: `f778c1f4345588d2991942afed62f0483e72469e` (`2026-10-30`).
- Open full-engine diagnostic PR: [#65](https://github.com/portsandall/NUKE-ARM64/pull/65), head `bbdfe2e1752ebd1392782d640d4fb4f7029bd1e1` on `ci/diagnose-kisakblack-android-root-20261030`.
- [ARM64 bootstrap run 41249265199](https://github.com/portsandall/NUKE-ARM64/actions/runs/41249265199): all three workflow jobs passed (Android smoke, host tests, upstream patch checks).
- [Angle/vector regression run 41249265254](https://github.com/portsandall/NUKE-ARM64/actions/runs/41249265254): passed.
- The full `KisakBlack` root build is a deliberately non-blocking diagnostic step. Therefore, a green workflow does **not** mean that the complete engine compiled.

## Latest full-engine Android diagnostic

Run 41249265199 reports:

- Android NDK root CMake configure: `ROOT_CONFIGURE_EXIT=0`.
- Full `KisakBlack` target build: `ROOT_BUILD_EXIT=1`.
- First failed Ninja object: `src/DynEntity/DynEntity_client.cpp.o`.
- Raw diagnostic artifact: [kisakblack-android-root-diagnostic](https://github.com/portsandall/NUKE-ARM64/actions/runs/41249265199/artifacts/13060333530).

Compiler errors in the captured first-wave build:

| Source | Android AArch64 result | Meaning |
|---|---:|---|
| `src/sound/snd.h:498` | `SndDriverGlobals`: 104 bytes, assertion expects 52 | Pointer-bearing runtime layout conflicts with the 32-bit asset record |
| `src/bgame/bg_local.h:341` | `centity_s`: 856 bytes, assertion expects 808 | 48-byte layout drift; fields and consumers need auditing |
| `src/bgame/bg_local.h:731` | `playerState_s`: 10,152 bytes, assertion expects 9,892 | 260-byte layout drift; network/demo serialization and field offsets need auditing |
| `src/DynEntity/DynEntity_client.cpp:1113,1127` | Constraint object pointers cast to `int` | Pointer truncation in the runtime constraint handle |
| `src/DynEntity/DynEntity_client.cpp:1306` | `Phys_ObjCreate` pointer cast to `int` | Pointer-sized physics user-data pointer is being stored in a 32-bit handle |

### Important layout findings

Do not fix these by changing static assertions to whatever size AArch64 produces.

- `SndDriverGlobals` is read as a fixed 52-byte asset record: `Load_SndDriverGlobals` calls `Load_Stream(..., 52)`, and `DB_SizeofXAsset_SndDriverGlobals_` returns 52. A correct LP64 design needs an explicit fixed-width serialized representation and a native runtime representation/conversion; simply accepting 104 bytes would break the asset stream.
- `PhysConstraint::constraintHandle` is a runtime pointer token stored in an `int`, but `PhysConstraintsLoadFile` uses a fixed 168-byte element stride, a 2,696-byte allocation, and hard-coded byte offsets. Widening this field in place would invalidate that parser layout. Use a stable 32-bit handle table or separate the fixed-layout config record from runtime pointer state.
- `Phys_ObjCreate` returns `PhysObjUserData *`; the current 32-bit code narrows it to `int`, and `Phys_GetUserData(int)` converts that integer directly back to a pointer. This needs a consistent pointer-safe physics-handle design across all callers, not a local cast suppression.
- The earlier `Material_RegisterHandle`, incomplete `clientState_s`, and `Windows.h` diagnostics are absent from this run's compiler-error list. That is progress in the include-boundary transformations, not proof that the full source tree is platform-clean.

## Verified focused components

The successful upstream-patch job compiles/tests a growing subset of the pinned source on host and/or Android AArch64, including Base64, angle/vector and extracted quaternion code, file access, threading, DemonWare reference/mutex/buffer helpers, and selected physics, database, renderer-independent declarations and LP64 layouts. Android objects are checked as ELF64/AArch64; host regressions execute on the CI runner.

These checks are not a complete engine build and are not physical-device runtime tests. No playable APK is produced by this repository's default branch.

## Blockers, in required priority

1. **Compilability:** root CMake configuration passes, but the complete engine target still fails in its first observed gameplay translation unit.
2. **Platform isolation:** current transformations remove several Windows/D3D transitive includes and Windows-only CMake dependencies; remaining renderer, material and platform services still need real native boundaries.
3. **LP64:** the three structure-layout mismatches and two classes of pointer-to-int storage must be fixed according to serialization/runtime semantics, not by packing or blind widening. GJK's x87 assumptions also remain a separate AArch64 numerical-portability gate.
4. **Graphics bootstrap:** no integrated native Android renderer in the KisakBlack engine.
5. **Map loading:** no real `mp_nuked` asset loading, collision or spawn path. The repository's map identifier is only a scope guard.
6. **Multiplayer:** no playable session creation/joining, server/client gameplay or network spawn validation.
7. **Performance:** no representative game frame-time, memory, GPU or network benchmarks.

## Next acceptance gate

Start with an explicit 52-byte `SndDriverGlobals` serialized-record type and a separate LP64 runtime representation. Add offset/size tests for the serialized record and a loader conversion test before changing the production loader. In a separate patch, design a pointer-safe physics-handle abstraction; do not widen `PhysConstraint` in place because its parser relies on fixed byte offsets and element stride.

The new CI diagnostic summarizer is being added to publish a concise Markdown error list alongside the raw root-build log. Its own workflow verification is pending at this audit revision.

Before distributing upstream-derived binaries or source, confirm applicable licensing and redistribution rights. The repository does not distribute proprietary Black Ops assets.
