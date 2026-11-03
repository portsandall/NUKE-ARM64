# NUKE-ARM64 native engine audit

Audit snapshot: 2026-11-03 00:39 UTC (10:39 Brisbane)  
Pinned upstream: [SwagSoftware/KisakBlack](https://github.com/SwagSoftware/KisakBlack) @ `306bb14a8e052a6244bd1df4e4df7d8504c04ef4`.

## Current review — 2026-11-03 00:39 UTC

### Repository and CI

- Default branch main remains at f778c1f (2026-10-30). Its latest main pushes passed: ARM64 bootstrap run [#558](https://github.com/portsandall/NUKE-ARM64/actions/runs/40979382826) and angle/vector regression run [#288](https://github.com/portsandall/NUKE-ARM64/actions/runs/40979382603).
- PR [#65](https://github.com/portsandall/NUKE-ARM64/pull/65) remains open on ci/diagnose-kisakblack-android-root-20261030 at b6bc71f3 (2026-11-02); it contains 182 commits and changes 88 files.
- Latest PR ARM64 bootstrap run [#861](https://github.com/portsandall/NUKE-ARM64/actions/runs/41366144792): all three jobs passed — Android AArch64, host tests, and upstream portability checks. Latest angle/vector regression [#621](https://github.com/portsandall/NUKE-ARM64/actions/runs/41366144667) also passed.
- The full-engine root build is intentionally non-blocking inside the green upstream job. Its diagnostic command records ROOT_BUILD_EXIT=1 and still allows the job to succeed. A green workflow is not a full-engine build.

### Latest full-engine Android result — 2026-11-02

- Android NDK root CMake configure: ROOT_CONFIGURE_EXIT=0.
- Full KisakBlack target: ROOT_BUILD_EXIT=1; first failed object is src/DynEntity/DynEntity_client.cpp.o at [26/1064].
- Compiler blockers reproduced: SndDriverGlobals is 104 bytes versus the 52-byte serialized assertion; centity_s is 856 versus 808; playerState_s is 10,152 versus 9,892; DynEntity_client.cpp narrows constraint pointers at lines 1113/1127 and the Phys_ObjCreate pointer at line 1306 to int.
- Raw log artifact: [kisakblack-android-root-diagnostic, artifact 13107585963](https://github.com/portsandall/NUKE-ARM64/actions/runs/41366144792/artifacts/13107585963).
- The earlier Material_RegisterHandle, incomplete clientState_s and Windows.h errors are absent from this run. This is genuine include-boundary progress; the first observed build failure has moved to LP64 layout and pointer-token semantics.

### Newly verified component

- PR head b6bc71f3 adds include/nuke/physics_handle_table.h and tests/physics_handle_table.cpp. The isolated handle-table regression is included in host CTest, and its Android AArch64 executable is built and architecture-checked. It is not yet connected to the engine PhysConstraint or Phys_ObjCreate / Phys_GetUserData call sites, so the remaining pointer-narrowing errors are unresolved.
- Latest upstream SwagSoftware/KisakBlack commit remains 306bb14a8e052a6244bd1df4e4df7d8504c04ef4, dated 2026-10-02 13:01 UTC. No newer upstream commits or Android/AArch64 work were found through 2026-11-03.

### Next smallest high-value change

Implement a fixed-width 52-byte SndDriverGlobals serialized record, separate from its LP64 runtime representation. Add field-offset/size tests and loader-conversion coverage for both immediate and delayed stream loading before changing production loading code; delayed staging must outlive Load_DelayStream. Do not relax the assertion or simply accept the 104-byte native layout.

After that, integrate the already-tested PhysicsHandleTable at both constraint-pointer and Phys_ObjCreate / Phys_GetUserData conversion boundaries, with explicit lifetime and physics-lock rules. Preserve the 168-byte PhysConstraint parser layout. The centity_s and playerState_s layouts still need field/offset, serialization and network-consumer audits.

---


## Previous repository and CI snapshot — 2026-11-01 (superseded by current review above)

- Default branch `main`: `f778c1f4345588d2991942afed62f0483e72469e` (`2026-10-30`).
- Open full-engine diagnostic PR: [#65](https://github.com/portsandall/NUKE-ARM64/pull/65), branch `ci/diagnose-kisakblack-android-root-20261030`, current head `7678a5119ecdcad0049e2325bd1b49aebbb80610`.
- Latest inspected ARM64 bootstrap: [run #857 / ID 41289200540](https://github.com/portsandall/NUKE-ARM64/actions/runs/41289200540), all three jobs passed:
  - Android AArch64: job `124796720853`.
  - Host tests: job `124796721089`.
  - Upstream portability and full-engine diagnostic: job `124796721039`.
- Latest inspected angle/vector regression: [run #617 / ID 41289200531](https://github.com/portsandall/NUKE-ARM64/actions/runs/41289200531), passed.
- The full `KisakBlack` root build is a deliberately non-blocking diagnostic step. Green workflow jobs do **not** mean that the complete engine compiled.

## Previous full-engine Android diagnostic — 2026-11-01 (superseded by current review above)

Run [#857 / ID 41289200540](https://github.com/portsandall/NUKE-ARM64/actions/runs/41289200540) reports:

- Android NDK root CMake configure: `ROOT_CONFIGURE_EXIT=0`.
- Full `KisakBlack` target build: `ROOT_BUILD_EXIT=1`.
- First failed Ninja object: `src/DynEntity/DynEntity_client.cpp.o` at step `[26/1064]`.
- Raw diagnostic artifact: [kisakblack-android-root-diagnostic, artifact 13076745720](https://github.com/portsandall/NUKE-ARM64/actions/runs/41289200540/artifacts/13076745720).

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

- `SndDriverGlobals` is read as a fixed 52-byte asset record: `Load_SndDriverGlobals` calls `Load_Stream(..., 52)`, and `DB_SizeofXAsset_SndDriverGlobals_` returns 52. A correct LP64 design needs a fixed-width serialized representation and a separate native runtime representation/conversion. `Load_Stream` can defer copies into `g_streamDelayArray` for some stream positions, so any serialized staging storage must outlive `Load_DelayStream`; a stack temporary is not safe.
- `PhysConstraint::constraintHandle` is a runtime pointer token stored in an `int`, but `PhysConstraintsLoadFile` uses a fixed 168-byte element stride, a 2,696-byte allocation, and hard-coded byte offsets. Widening this field in place would invalidate that parser layout. Use a stable 32-bit handle table or separate the fixed-layout config record from runtime pointer state.
- `Phys_ObjCreate` returns `PhysObjUserData *`; the current 32-bit code narrows it to `int`, and `Phys_GetUserData(int)` converts that integer directly back to a pointer. This needs a consistent pointer-safe physics-handle design across all callers, not a local cast suppression.
- The earlier `Material_RegisterHandle`, incomplete `clientState_s`, and `Windows.h` diagnostics are absent from this run's compiler-error list. That is progress in the include-boundary transformations, not proof that the full source tree is platform-clean.

## Verified focused components

The successful upstream-patch job compiles/tests a growing subset of the pinned source on host and/or Android AArch64, including Base64, angle/vector and extracted quaternion code, file access, threading, DemonWare reference/mutex/buffer helpers, sound DSP declarations, and selected physics, database, renderer-independent declarations and LP64 layouts. Android objects are checked as ELF64/AArch64; host regressions execute on the CI runner.

The upstream job's full-engine diagnostic, summary generation, and artifact uploads all completed. These checks are not a complete engine build and are not physical-device runtime tests. No playable APK is produced by this repository's default branch.

Artifacts from run #857:
- Full-engine diagnostic: `13076745720`.
- Upstream regression bundle: `13076995148`.
- Android smoke binaries: `13076745676`.

## Blockers, in required priority

1. **Compilability:** root CMake configuration passes, but the complete engine target still fails in its first observed gameplay translation unit.
2. **Platform isolation:** current transformations remove several Windows/D3D transitive includes and Windows-only CMake dependencies; remaining renderer, material and platform services still need real native boundaries.
3. **LP64:** the three structure-layout mismatches and two classes of pointer-to-int storage must be fixed according to serialization/runtime semantics, not by packing or blind widening. GJK's x87 assumptions also remain a separate AArch64 numerical-portability gate.
4. **Graphics bootstrap:** no integrated native Android renderer in the KisakBlack engine.
5. **Map loading:** no real `mp_nuked` asset loading, collision or spawn path. The repository's map identifier is only a scope guard.
6. **Multiplayer:** no playable session creation/joining, server/client gameplay or network spawn validation.
7. **Performance:** no representative game frame-time, memory, GPU or network benchmarks.

## Previous next acceptance gate — 2026-11-01 (superseded by current review above)

Start with a fixed-width 52-byte `SndDriverGlobals` serialized-record type and a separate LP64 runtime representation. Add offset/size tests for the serialized record and a loader-conversion test that exercises both immediate and delayed stream loading before changing the production loader. The staging record must remain valid until delayed data has been copied. In a separate patch, design a pointer-safe physics-handle abstraction; do not widen `PhysConstraint` in place because its parser relies on fixed byte offsets and element stride.

Upstream history was checked through 2026-11-01: `SwagSoftware/KisakBlack` still points to `306bb14a8e052a6244bd1df4e4df7d8504c04ef4` (2026-10-02). No newer Android/AArch64-specific upstream change was found.

Before distributing upstream-derived binaries or source, confirm applicable licensing and redistribution rights. The repository does not distribute proprietary Black Ops assets.