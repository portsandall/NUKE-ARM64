# NUKE-ARM64 native engine audit

Audit date: 2026-10-29  
Pinned upstream: [SwagSoftware/KisakBlack](https://github.com/SwagSoftware/KisakBlack) @ `306bb14a8e052a6244bd1df4e4df7d8504c04ef4`.

## Verified build boundary

Latest verified `main` commit: `bffdacb0a6adee4764cf71808e4350107be3c157` ([native engine audit refresh](https://github.com/portsandall/NUKE-ARM64/commit/bffdacb0a6adee4764cf71808e4350107be3c157), 2026-10-29 02:12:56 UTC).

- [ARM64 bootstrap run 446 / ID 40805028089](https://github.com/portsandall/NUKE-ARM64/actions/runs/40805028089): all three jobs passed — host tests `123221799223`, upstream patch/component checks `123221799451`, and Android AArch64 smoke build `123221799455`. Host CTest passed 3/3.
- [Angle/vector + file-access regression run 176 / ID 40805028305](https://github.com/portsandall/NUKE-ARM64/actions/runs/40805028305), job `123221801162`: CTest passed 2/2 (`upstream-angle-vectors-roundtrip`, `upstream-fileaccess-open`).
- Logs at 2026-10-29 02:13 UTC confirm the actual upstream `src/universal/com_fileaccess.cpp` and focused harness were compiled and linked with Android NDK Clang for AArch64 using `-Wl,--no-undefined`; `llvm-readelf` confirmed ELF64/AArch64. The host file-access and angle/vector regression cases passed. The same bootstrap also ran the patched bitarray, atomic, threading, and Base64 portability checks.
- Artifacts from run 446: [upstream regression bundle, artifact `12868185568`](https://github.com/portsandall/NUKE-ARM64/actions/runs/40805028089/artifacts/12868185568), 148,305 bytes, SHA-256 `f02c67f825a03cd14a2ba6df45b33aaad5644ca12b1c715f39c31a489a7945cd`; [Android smoke binaries, artifact `12868026562`](https://github.com/portsandall/NUKE-ARM64/actions/runs/40805028089/artifacts/12868026562), 145,934 bytes, SHA-256 `77d582e599aa954d44e408659ec5bdefa1c6c23ed161d76ec37d3e7b862fe3f1`.

The upstream-patch job compiles and tests the actual `tl/base/tl_thread.h` read/write mutex on the host (8 threads × 2,000 write-lock increments), cross-compiles the same test for Android AArch64, and checks the Android ELF header.

The CI also builds the real upstream `src/universal/base64.cpp`, `src/universal/com_math_anglevectors.cpp`, a limited extracted `AxisToQuat`/`ikAxisToQuat` subset, and `src/universal/com_fileaccess.cpp`. The file-access harness tests failed-open reporting and a successful open on the host; its Android executable is cross-compiled and architecture-checked, not run on-device.

These are useful portability gates, but they do **not** compile a Black Ops multiplayer/gameplay translation unit, link the complete engine, integrate an Android renderer, or produce a playable APK. The extracted quaternion subset is not the full `com_math.cpp` translation unit. Host runtime tests do not prove Android runtime behavior.

## Remaining high-priority blockers

1. **Full engine integration:** there is no complete Android AArch64 engine target or dependency graph. Current targets are probes and focused upstream translation-unit/regression targets.
2. **Platform isolation:** upstream still has Windows entry points/services, WinSock and Windows SDK assumptions, DirectX-oriented configuration, and MSVC/x86 options. The current shims are not a complete platform layer.
3. **Physics portability:** the pinned `src/physics/phys_gjk.cpp` rejects non-x87 configurations. AArch64 has no x87; do not remove the guard without a numerically validated alternative and collision regression tests.
4. **LP64 audit:** no engine-wide audit of pointer/integer conversions, structure layouts, or Windows type assumptions exists.
5. **Graphics and map loading:** no native Android renderer or real `mp_nuked` map/asset-loading path is integrated. The platform probe's map name is only a scope guard.
6. **Gameplay and multiplayer:** no playable engine, spawn/collision validation, host/join flow, or network session is implemented.
7. **Performance:** no gameplay-level frame-time, memory, GPU, or network measurements exist.

## Next acceptance gate

Move beyond isolated utility/platform-service translation units: configure an Android NDK target for a dependency-complete physics or gameplay subsystem, with dependencies explicit and no stub replacing exercised behavior. First resolve the x87-dependent GJK numerical path with collision regression coverage, then link that subsystem and verify the resulting AArch64 object/ELF architecture. Do not count a probe, a stub-only test, or an extracted helper as a gameplay-port milestone.

Before distributing upstream-derived binaries or source, confirm the applicable license and redistribution rights. Do not replace authentic Black Ops behavior with generic FPS components while describing it as the original port.
