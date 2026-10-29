# NUKE-ARM64 native engine audit

Audit date: 2026-10-29  
Pinned upstream: [SwagSoftware/KisakBlack](https://github.com/SwagSoftware/KisakBlack) @ `306bb14a8e052a6244bd1df4e4df7d8504c04ef4`.

## Verified build boundary

Latest verified `main` commit: `05cdc9c7e86721dd37a3e382e9c61b1caa383135` ([ThreadSanitizer-backed mutex regression](https://github.com/portsandall/NUKE-ARM64/commit/05cdc9c7e86721dd37a3e382e9c61b1caa383135), 2026-10-29 11:36:24 UTC).

- [ARM64 bootstrap run 467 / ID 40866685592](https://github.com/portsandall/NUKE-ARM64/actions/runs/40866685592): all three jobs passed — host tests `123423103437`, upstream patch/component checks `123423103830`, and Android AArch64 smoke build `123423103976`. Host CTest passed 3/3.
- [Angle/vector + file-access regression run 197 / ID 40866685593](https://github.com/portsandall/NUKE-ARM64/actions/runs/40866685593), job `123423103260`: CTest passed 2/2 (`upstream-angle-vectors-roundtrip`, `upstream-fileaccess-open`).
- The upstream-patch job log confirms that the actual `tl/base/tl_thread.h` read/write mutex regression ran on the Linux host with ThreadSanitizer, a 60-second timeout, four reader threads and two writer threads. Its protected value/complement pair is non-atomic, so the mutex must supply synchronization. The same test cross-compiled with Android NDK Clang; `llvm-readelf` reported ELF64/AArch64.
- The same workflow compiled or linked the patched bitarray/atomic/threading compatibility tests and selected upstream Base64, angle/vector, extracted quaternion and file-access code. The Android file-access executable was linked with `-Wl,--no-undefined` and passed ELF64/AArch64 checks.
- Artifacts from run 467: [Android smoke binaries, artifact `12893588572`](https://github.com/portsandall/NUKE-ARM64/actions/runs/40866685592/artifacts/12893588572), 145,934 bytes, SHA-256 `73373377b42ecbff1b29ff2004a2bf7fdc2ecab5a441a43ac02865477e854f1c`; [upstream regression bundle, artifact `12894166517`](https://github.com/portsandall/NUKE-ARM64/actions/runs/40866685592/artifacts/12894166517), 152,865 bytes, SHA-256 `b31eec79d24fec5fca2a31706fe31307889c69fedf7e0dbed01527344f12faf5`.

The threading regression ran under ThreadSanitizer on the Linux host. Its Android counterpart was cross-compiled and architecture-checked, not executed on a physical Android device. These are portability/regression targets, not a complete engine or playable APK.

The CI also builds the real upstream `src/universal/base64.cpp`, `src/universal/com_math_anglevectors.cpp`, a limited extracted `AxisToQuat`/`ikAxisToQuat` subset, and `src/universal/com_fileaccess.cpp`. The file-access harness tests failed-open reporting and a successful open on the host. The extracted quaternion subset is not the full `com_math.cpp` translation unit.

These are useful portability gates, but they do **not** compile a Black Ops multiplayer/gameplay translation unit, link the complete engine, integrate an Android renderer, or produce a playable APK. Host runtime tests do not prove Android runtime behavior.

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
