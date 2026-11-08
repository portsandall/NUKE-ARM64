## Current review — 2026-11-08

### Repository and upstream state

- Default branch `main` remains at `f778c1f4345588d2991942afed62f0483e72469e` (2026-10-30).
- PR [#65](https://github.com/portsandall/NUKE-ARM64/pull/65) remains open, mergeable and unmerged; its branch is ahead of `main` with no commits behind. Latest implementation commit: [`22c58d6`](https://github.com/portsandall/NUKE-ARM64/commit/22c58d68ea8d84469c896ec71c5a91165666baec). This review's follow-on commit is documentation-only.
- Latest upstream history search still returns `SwagSoftware/KisakBlack@306bb14a8e052a6244bd1df4e4df7d8504c04ef4` (2026-10-02); no newer upstream commit was found.

### Focused iteration completed

The full-engine compiler log from the previous run exposed an out-of-bounds row-index warning in the physics matrix adapters. The pointer parameters are pointers to `float[3]` rows, but the original code indexed beyond the first row with expressions such as `&(*axis)[6]`.

Commit [`22c58d6`](https://github.com/portsandall/NUKE-ARM64/commit/22c58d68ea8d84469c896ec71c5a91165666baec) adds a fail-closed transformation for the disposable pinned upstream checkout:

- `Phys_AxisToNitrousMat`: explicit rows `axis[0..2]`.
- `Phys_Mat4ToNitrousMat`: explicit rows `inMat[0..3]`.
- `Phys_NitrousMat44ToVec33`: explicit `outAxis[row][column]` writes.

The regression fixture is generated from the transformed upstream function bodies, then checks 3x3 conversion, 4x3 conversion and reverse conversion. The host and Android builds compile it with `-Warray-bounds -Werror=array-bounds`. This is a CI-only transformation/regression; it does not change the pinned upstream repository or implement the Android renderer.

### Verification

- ARM64 bootstrap [run #884 / ID 42431023560](https://github.com/portsandall/NUKE-ARM64/actions/runs/42431023560): all three jobs passed — `host-tests`, `android-arm64`, and `upstream-patch-check`.
- Host CTest: 5/5 passed.
- Android NDK smoke binaries compiled/linked and passed ELF64/AArch64 checks.
- Upstream step 28, “Compile and run physics matrix row-index regression on host and Android”, passed; output: `physics matrix row adapters: 3x3, 4x3 and reverse conversion passed`.
- Angle/vector regression [PR run #644 / ID 42431023530](https://github.com/portsandall/NUKE-ARM64/actions/runs/42431023530): passed.
- Artifacts: upstream regression bundle [13597701358](https://github.com/portsandall/NUKE-ARM64/actions/runs/42431023560); full-engine diagnostic [13597472559](https://github.com/portsandall/NUKE-ARM64/actions/runs/42431023560); Android smoke binaries [13596723816](https://github.com/portsandall/NUKE-ARM64/actions/runs/42431023560).

### Full-engine diagnostic remains red inside a green workflow

- Android NDK root configure: `ROOT_CONFIGURE_EXIT=0`.
- Complete KisakBlack build: `ROOT_BUILD_EXIT=1`; first failed object remains `src/DynEntity/DynEntity_client.cpp.o`, Ninja step [26/1064].
- The previous `phys_local.h:1850` array-bounds warning is absent after the row-index transform.
- Remaining hard errors are unchanged:
  - `SndDriverGlobals`: 104-byte LP64 runtime object versus 52-byte serialized assertion.
  - `centity_s`: 856 versus 808 bytes.
  - `playerState_s`: 10,152 versus 9,892 bytes.
  - Pointer-to-`int` narrowing at `DynEntity_client.cpp:1113,1127,1306`.
- The root diagnostic remains non-blocking. Green workflow status does not mean the full engine compiled or linked.

### Next smallest high-value production change

Implement the real `Load_SndDriverGlobals` conversion: read the fixed-width 52-byte FastFile record, resolve XString/array tokens, populate the native LP64 runtime structure, and preserve staging memory across deferred `Load_DelayStream` copies. Do not relax the 52-byte assertion or memcpy the disk record into the 104-byte runtime object.

Then integrate `PhysicsHandleTable` at every constraint/ragdoll/physics-user-data conversion boundary, preserving fixed parser layouts. Audit `centity_s` and `playerState_s` field offsets and serialization/network consumers.

Graphics bootstrap, real `mp_nuked` asset/collision/spawn loading, multiplayer sessions and gameplay performance measurements remain unimplemented. No linked game executable or playable APK is claimed.

---

## Current review — 2026-11-07 00:07 UTC (10:07 Brisbane)

### Repository and upstream state

- Default branch `main` remains at `f778c1f4345588d2991942afed62f0483e72469e` (2026-10-30).
- PR [#65](https://github.com/portsandall/NUKE-ARM64/pull/65) remains open and unmerged. Its engineering branch is 191 commits ahead of `main` and has no commits behind it.
- Latest production/test commit remains [`18b6f56`](https://github.com/portsandall/NUKE-ARM64/commit/18b6f564f799d0633577ea0d0689812a706b9010) (2026-11-06 00:39:52 UTC). At review start, the latest branch commit was audit-only [`6d80668`](https://github.com/portsandall/NUKE-ARM64/commit/6d806684c96987b68215d9cdd3a39c6b41b75eff) (00:41:55 UTC). This review's audit update is [`0305252`](https://github.com/portsandall/NUKE-ARM64/commit/03052522f02bff454bb6e28b8b4f23336b09f72b). No newer production-code commit was found.
- Pinned upstream remains `SwagSoftware/KisakBlack@306bb14a8e052a6244bd1df4e4df7d8504c04ef4` (2026-10-02). No newer upstream commit was returned by repository commit search.

### Latest verified GitHub Actions result

- ARM64 bootstrap [run #878](https://github.com/portsandall/NUKE-ARM64/actions/runs/42138721671): all three jobs passed — `host-tests`, `android-arm64`, and `upstream-patch-check`.
- Host job passed diagnostic-summary tests, workflow/template parity, CMake build and CTest.
- Android job configured with the NDK, compiled/linked smoke binaries and passed ELF64/AArch64 verification.
- Upstream job passed the focused portability/layout regressions, including fixed-width `SndDriverGlobalsRecord32` and FastFile pointer relocation.
- The upstream job's final full-engine diagnostic step completed but reported `ROOT_BUILD_EXIT=1`; its non-blocking status is why the workflow remains green.

### Additional blocker detail from the raw #878 job log

The complete Android root configure passed (`ROOT_CONFIGURE_EXIT=0`), but the engine stopped at `src/DynEntity/DynEntity_client.cpp.o`, Ninja step [26/1064].

The first-wave hard errors remain:
- `SndDriverGlobals`: 104-byte native LP64 type versus the 52-byte FastFile record assertion.
- `centity_s`: 856 bytes versus 808 expected.
- `playerState_s`: 10,152 bytes versus 9,892 expected.
- Pointer-to-`int` narrowing at `DynEntity_client.cpp:1113,1127,1306`.

The raw log also exposes warning-only integer-to-pointer casts that broaden the physics handle integration surface:
- `ragdoll.h:206` (`RagdollBody*`).
- `DynEntity_client.cpp:907,919` (constraint destruction).
- `DynEntity_client.cpp:1048,1189,1310` (`PhysObjUserData*`).

Diagnostic artifact: [13467570026](https://github.com/portsandall/NUKE-ARM64/actions/runs/42138721671/artifacts/13467570026), SHA-256 `a26cb5c643856849feca637d056c4cbc76b6bf1b64273f461badfc592c7876d2`.

### Today's iteration and next production gate

- Re-fetched the PR branch audit and source, compared it with `main`, inspected all three #878 jobs and extracted the full-engine compiler diagnostics. No production source change was made during this review.
- Next smallest production change remains the `Load_SndDriverGlobals` LP64 conversion: consume the 52-byte fixed-width record, resolve its XString/array tokens, and populate the native runtime object while preserving delayed-stream staging lifetime. Do not relax the assertion or memcpy the disk record into the 104-byte runtime type.
- Then integrate `PhysicsHandleTable` across every constraint, ragdoll and `PhysObjUserData` conversion site identified above. Preserve fixed parser/network layouts; audit `centity_s` and `playerState_s` offsets and consumers rather than changing assertions to native sizes.
- Graphics bootstrap, real `mp_nuked` asset/collision/spawn loading, multiplayer sessions and gameplay performance measurements remain unimplemented. No linked game executable or playable APK is claimed.

---

# NUKE-ARM64 native engine audit

Audit snapshot: 2026-11-03 00:39 UTC (10:39 Brisbane)  
Pinned upstream: [SwagSoftware/KisakBlack](https://github.com/SwagSoftware/KisakBlack) @ `306bb14a8e052a6244bd1df4e4df7d8504c04ef4`.

## Current review — 2026-11-06 00:41 UTC (10:41 Brisbane)

### Repository and latest verified iteration

- Default branch `main` remains at `f778c1f4345588d2991942afed62f0483e72469e` (2026-10-30). PR [#65](https://github.com/portsandall/NUKE-ARM64/pull/65) remains open and unmerged; head is `18b6f564f799d0633577ea0d0689812a706b9010`.
- New focused test commit [`18b6f56`](https://github.com/portsandall/NUKE-ARM64/commit/18b6f564f799d0633577ea0d0689812a706b9010) adds regression cases proving FastFile offset resolution rejects a null block table, a zero-length block table, and a selected block with a null data pointer before pointer arithmetic.
- The source file was refetched after the commit and the new cases were confirmed present.

### CI verification for the new commit

- ARM64 bootstrap [run #876](https://github.com/portsandall/NUKE-ARM64/actions/runs/42138473060): all three jobs passed — `host-tests`, `android-arm64`, and `upstream-patch-check`.
- Host CTest: 5/5 passed.
- Android NDK smoke targets compiled and linked; ELF checks confirmed ELF64/AArch64.
- Upstream-patch step 27, “Compile and run native database pointer relocation regression on host and Android”, passed.
- Angle/vector regression [run #636](https://github.com/portsandall/NUKE-ARM64/actions/runs/42138473109) passed.
- The new test commit changes test coverage only; it does not change production engine code.

### Latest full-engine Android diagnostic — 2026-11-06

- Android NDK root configure: `ROOT_CONFIGURE_EXIT=0`.
- Full KisakBlack target: `ROOT_BUILD_EXIT=1`; first failed object remains `src/DynEntity/DynEntity_client.cpp.o`, Ninja step [26/1064].
- Current first-wave errors remain:
  - `SndDriverGlobals`: 104-byte LP64 runtime type versus the 52-byte FastFile record assertion.
  - `centity_s`: 856 bytes versus 808.
  - `playerState_s`: 10,152 bytes versus 9,892.
  - Pointer-to-`int` narrowing in `DynEntity_client.cpp:1113,1127,1306`.
- Raw diagnostic artifact: [artifact 13466671804](https://github.com/portsandall/NUKE-ARM64/actions/runs/42138473060/artifacts/13466671804).
- The diagnostic remains non-blocking; the green workflow is not a successful full-engine build.

### Upstream and next production gate

- `SwagSoftware/KisakBlack` remains pinned at `306bb14a8e052a6244bd1df4e4df7d8504c04ef4` (2026-10-02); no newer upstream commit was found.
- Next production change remains the LP64 `Load_SndDriverGlobals` conversion: load the 52-byte fixed-width record into storage that survives any deferred `Load_DelayStream` copy, then explicitly populate the native runtime structure and preserve XString/array-token semantics. Do not copy the record directly into the pointer-bearing LP64 object or merely relax its assertion.
- After that, integrate `PhysicsHandleTable` into the real constraint and physics user-data call sites. Keep `PhysConstraint`'s 168-byte parser layout intact.
- Graphics bootstrap, Nuketown asset/collision/spawn loading, multiplayer sessions, and performance measurements remain unimplemented.


## Current review — 2026-11-05

### Repository and CI

- Default branch `main` remains at `f778c1f4345588d2991942afed62f0483e72469e` (2026-10-30). PR [#65](https://github.com/portsandall/NUKE-ARM64/pull/65) remains open on `ci/diagnose-kisakblack-android-root-20261030`; latest implementation commit is `dc2fe5efa0fc4d3017fa36ada6798ff20bb3eb86` (the subsequent audit update is documentation-only).
- Focused code commits: [`8af53e9`](https://github.com/portsandall/NUKE-ARM64/commit/8af53e9d459a4188e9508f6d866525419a6c1dc0) bounds-checks FastFile offset relocation; [`dc2fe5e`](https://github.com/portsandall/NUKE-ARM64/commit/dc2fe5efa0fc4d3017fa36ada6798ff20bb3eb86) adds host regression coverage.
- ARM64 bootstrap [run #870](https://github.com/portsandall/NUKE-ARM64/actions/runs/41937327189) passed all three jobs: `host-tests`, `upstream-patch-check`, and `android-arm64`. Angle/vector regression [run #630](https://github.com/portsandall/NUKE-ARM64/actions/runs/41937327180) passed.
- The new native database pointer-relocation regression passed on the host and compiled for Android AArch64; the Android binary passed ELF64/AArch64 checks. It tests FastFile block indices 0, 1 and 6, final-byte and native pointer-slot bounds, null/reserved tokens, and out-of-range block indices.

### Focused LP64 iteration completed

- Extended `tests/port_db_offset_pointer_lp64.py` with a bounds-checked resolver for the FastFile token format: 3-bit stream-block index plus 29-bit byte offset. It rejects null/reserved tokens, missing blocks, offsets outside a block, and pointer-alias slots that do not fit in full.
- `DB_ConvertOffsetToPointer` now resolves into a native-width pointer slot only after validating the target byte; `DB_ConvertOffsetToAlias` validates the entire native pointer slot. `DB_InsertPointer` already reserves native pointer width and alignment.
- This improves the existing generic LP64 relocation transform. It does not convert the `SndDriverGlobals` asset record or integrate the physics handle table into gameplay call sites.

### Latest full-engine Android diagnostic — 2026-11-05

- Android NDK root CMake configure: `ROOT_CONFIGURE_EXIT=0`.
- Full `KisakBlack` target: `ROOT_BUILD_EXIT=1`; first failed object remains `src/DynEntity/DynEntity_client.cpp.o` at Ninja step [26/1064].
- Reproduced blockers:
  - `SndDriverGlobals`: 104-byte LP64 runtime structure versus 52-byte serialized-layout assertion.
  - `centity_s`: 856 bytes versus 808 expected.
  - `playerState_s`: 10,152 bytes versus 9,892 expected.
  - Pointer-to-`int` narrowing at `DynEntity_client.cpp:1113,1127,1306`.
- Diagnostic artifact: [run #870 artifact 13374252611](https://github.com/portsandall/NUKE-ARM64/actions/runs/41937327189/artifacts/13374252611). The diagnostic is deliberately non-blocking; green CI does not mean the engine compiled.

### Upstream and next production gate

- `SwagSoftware/KisakBlack` remains pinned at `306bb14a8e052a6244bd1df4e4df7d8504c04ef4` (2026-10-02); no newer upstream commit was found.
- Next smallest production change: adapt `Load_SndDriverGlobals` to consume the fixed 52-byte record and populate the LP64 runtime object without changing serialized field order. The loader must handle inline-string and offset tokens and ensure any deferred `Load_DelayStream` destination remains alive until the delayed copy completes. Do not merely change the 52-byte assertion.
- Then integrate the tested `PhysicsHandleTable` at the constraint and `Phys_ObjCreate`/user-data boundaries, preserving fixed parser layouts. Audit `centity_s` and `playerState_s` offsets and all network/demo consumers before altering their layouts.

Graphics bootstrap, real `mp_nuked` asset/collision/spawn loading, multiplayer sessions, and gameplay performance benchmarks remain unimplemented. No playable APK was produced by this iteration.

## Current review — 2026-11-04 00:00 UTC

### Repository and CI

- Default branch `main` remains at `f778c1f4345588d2991942afed62f0483e72469e` (2026-10-30). The active engineering changes are on open PR [#65](https://github.com/portsandall/NUKE-ARM64/pull/65), branch `ci/diagnose-kisakblack-android-root-20261030`.
- PR head `d8b086d52f1793df52c4951078145c3a0cbec0d9` adds a standalone fixed-width `SndDriverGlobalsRecord32` schema guard and host/Android regression.
- Bootstrap run [#864](https://github.com/portsandall/NUKE-ARM64/actions/runs/41743417858) passed all three jobs: host tests, Android AArch64 smoke checks, and upstream-patch checks. Host CTest passed 5/5, including `snd-driver-globals-record32`. The dedicated upstream step also compiled the regression for Android AArch64 and completed its ELF64/AArch64 checks. Angle/vector run [#624](https://github.com/portsandall/NUKE-ARM64/actions/runs/41743417829) passed.
- Active workflow and reusable template parity passed. A green bootstrap still does not mean the complete engine compiled: the full-engine build remains a non-blocking diagnostic.

### Latest full-engine Android result — 2026-11-04

- Android NDK root CMake configure: `ROOT_CONFIGURE_EXIT=0`.
- Full KisakBlack target: `ROOT_BUILD_EXIT=1`; first failed object remains `src/DynEntity/DynEntity_client.cpp.o` at Ninja step [26/1064].
- The same first-wave LP64 blockers remain: `SndDriverGlobals` 104 bytes vs 52; `centity_s` 856 vs 808; `playerState_s` 10,152 vs 9,892; pointer-to-`int` narrowing at `DynEntity_client.cpp:1113,1127,1306`.
- Raw diagnostic: [artifact 13281224600](https://github.com/portsandall/NUKE-ARM64/actions/runs/41743417858/artifacts/13281224600). The diagnostic is deliberately non-blocking, so the overall workflow remains green.

### Newly completed focused iteration

- Added `include/nuke/snd_driver_globals_record32.h` and `tests/snd_driver_globals_record32.cpp`. The 13-word fixed-width record asserts 52-byte size, 4-byte alignment, standard-layout/trivially-copyable properties and every field offset; its test validates the ordered 32-bit words.
- Registered it in CMake/CTest and the Android workflow. CI output confirms the host regression passed, the AArch64 binary compiled and its ELF architecture checks passed. Workflow/template parity also passed.
- This is a schema/layout regression guard only. It does **not** alter `Load_SndDriverGlobals`, resolve stream tokens, or fix the current production engine assertion. No production engine loader code was changed.

### Next smallest production change

Design and implement the loader-side conversion from the 52-byte record into the native LP64 `SndDriverGlobals` runtime object. First prove the stream-token and pointer-relocation semantics, and make any intermediate record storage survive deferred `Load_DelayStream` copies; a stack temporary is unsafe. Then integrate the existing `PhysicsHandleTable` at the constraint-pointer and `Phys_ObjCreate`/`Phys_GetUserData` boundaries without changing the fixed 168-byte `PhysConstraint` parser layout. Audit `centity_s` and `playerState_s` field offsets and serialization/network consumers rather than accepting native sizes.

Upstream `SwagSoftware/KisakBlack` remains pinned at `306bb14a8e052a6244bd1df4e4df7d8504c04ef` (2026-10-02); no newer upstream commit was found.

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