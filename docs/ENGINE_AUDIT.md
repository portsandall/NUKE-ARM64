# NUKE-ARM64 native engine audit

Audit date: 2026-10-30  
Pinned upstream: [SwagSoftware/KisakBlack](https://github.com/SwagSoftware/KisakBlack) @ `306bb14a8e052a6244bd1df4e4df7d8504c04ef4`.

## Verified build boundary

Latest verified `main` commit: `02689976a7e9c884771e2cb765692f06c17c08a2` ([engine audit refresh](https://github.com/portsandall/NUKE-ARM64/commit/02689976a7e9c884771e2cb765692f06c17c08a2), 2026-10-29 12:27:52 UTC). The latest runtime/portability code commit remains `05cdc9c7e86721dd37a3e382e9c61b1caa383135`.

- [ARM64 bootstrap run 471 / ID 40873466225](https://github.com/portsandall/NUKE-ARM64/actions/runs/40873466225): all three jobs passed — host tests `123446189002`, upstream patch/component checks `123446189156`, Android AArch64 smoke build `123446189252`. Host CTest passed 3/3.
- [Angle/vector + file-access regression run 201 / ID 40873466094](https://github.com/portsandall/NUKE-ARM64/actions/runs/40873466094), job `123446188207`: CTest passed 2/2 (`upstream-angle-vectors-roundtrip`, `upstream-fileaccess-open`).
- The upstream-patch job log confirms the real `tl/base/tl_thread.h` read/write mutex regression ran on the Linux host with ThreadSanitizer and a 60-second timeout, using four reader threads and two writer threads. The protected value/complement pair is non-atomic so the mutex must provide synchronization. The same test cross-compiled with Android NDK Clang; `llvm-readelf` reported ELF64/AArch64.
- The workflow also compiles or links patched bitarray/atomic/threading compatibility tests and selected upstream Base64, angle/vector, extracted quaternion, and file-access code. The Android file-access test links with `-Wl,--no-undefined` and passes ELF64/AArch64 checks.
- Artifacts from run 471: [Android smoke binaries, artifact `12896877400`](https://github.com/portsandall/NUKE-ARM64/actions/runs/40873466225/artifacts/12896877400), 145,934 bytes, SHA-256 `54c42ff222407ff4596486c55adb3ad3f39e6a231440dc2f70ae7b901dde9a9c`; [upstream regression bundle, artifact `12897775221`](https://github.com/portsandall/NUKE-ARM64/actions/runs/40873466225/artifacts/12897775221), 152,865 bytes, SHA-256 `837fbee375f2930ae9daf0e156c0fd808fa947ebdb35871f51c36a27ff208d4c`.

The threading regression ran under ThreadSanitizer on the Linux host. Its Android counterpart was cross-compiled and architecture-checked, not executed on physical Android hardware. These are portability/regression targets, not a complete engine or playable APK.

The CI builds real upstream `src/universal/base64.cpp`, `src/universal/com_math_anglevectors.cpp`, a limited extracted `AxisToQuat`/`ikAxisToQuat` subset, and `src/universal/com_fileaccess.cpp`. The file-access harness tests failed-open diagnostics and successful opens on the host. The extracted quaternion subset is not the full `com_math.cpp` translation unit.

The existing workflow configures this repository's small `NUKE_ARM64` CMake project and separately compiles selected upstream translation units. It does **not** configure or link the upstream KisakBlack root target. Green smoke-build checks therefore do not establish that the whole engine configures or links for Android.

## First actionable blockers

1. **Android upstream build configuration / platform isolation:** the pinned upstream root [`CMakeLists.txt`](https://github.com/SwagSoftware/KisakBlack/blob/306bb14a8e052a6244bd1df4e4df7d8504c04ef4/CMakeLists.txt) applies MSVC-specific flags such as `/MT`, `/MP`, `/W3`, `/permissive`, and `/arch:IA32`, uses DirectX SDK paths, links Windows libraries (including D3D, WinMM, WinSock and XInput libraries), and applies `/machine:x86`. These settings are not a usable Android NDK build configuration. CI has not attempted the upstream root build, so this is a source-confirmed blocker, not a claimed observed build failure. First create a platform-gated Android target and isolate or replace unavailable Win32/DirectX services; add dependencies explicitly rather than importing the entire Windows target.
2. **Physics numerical portability:** the pinned [`src/physics/phys_gjk.cpp`](https://github.com/SwagSoftware/KisakBlack/blob/306bb14a8e052a6244bd1df4e4df7d8504c04ef4/src/physics/phys_gjk.cpp) rejects configurations without its expected x87 floating-point mode. The comments associate extended intermediate precision with mitigating repeated GJK maximum-iteration warnings. AArch64 has no x87. Do not remove the guard until an AArch64-compatible numerical path passes collision regression cases.
3. **Full engine dependency graph:** no dependency-complete Black Ops multiplayer/gameplay target is built or linked. Existing targets are platform probes and focused portability/regression targets.
4. **LP64 audit:** no engine-wide audit of pointer/integer conversions, structure layouts, or Windows type assumptions exists.
5. **Graphics and map loading:** no native Android renderer or real `mp_nuked` map/asset-loading path is integrated. The platform probe's map name is only a scope assertion.
6. **Gameplay and multiplayer:** no playable engine, spawn/collision validation, host/join flow, or network session is implemented.
7. **Performance:** no gameplay-level frame-time, memory, GPU, or network measurements exist.

## Next acceptance gate

Create a small, explicit Android NDK target that links a dependency-complete upstream subsystem without replacing exercised behavior with stubs. First remove the root build's unconditional Windows/MSVC/DirectX assumptions from that target and make its dependencies explicit. For a physics target, resolve the x87-dependent GJK path with collision regression coverage before claiming success; then link the subsystem and verify AArch64 object/ELF architecture. Do not count a probe, a stub-only test, or an extracted helper as a gameplay-port milestone.

Before distributing upstream-derived binaries or source, confirm the applicable license and redistribution rights. Do not replace authentic Black Ops behavior with generic FPS components while describing it as the original port.
