# NUKE-ARM64 native engine audit

Audit date: 2026-10-29  
Pinned upstream: [SwagSoftware/KisakBlack](https://github.com/SwagSoftware/KisakBlack) @ `306bb14a8e052a6244bd1df4e4df7d8504c04ef4`.

## Verified build boundary

The default-branch CI is green at `8e752850a264bd4d8e895227ceddabd1cb992065`:

- [ARM64 bootstrap](https://github.com/portsandall/NUKE-ARM64/actions/runs/40787094166): host tests pass; Android NDK builds `nuke-platform-probe` and `nuke-atomic-test`, then checks ELF64/AArch64.
- [Angle/vector regression](https://github.com/portsandall/NUKE-ARM64/actions/runs/40787094221): portability patches apply; bitarray, atomic and threading shim regressions compile for host and Android; the full `base64.cpp` and `com_math_anglevectors.cpp` translation units compile; a limited extracted `AxisToQuat`/`ikAxisToQuat` subset is compiled and linked for host and Android.

These checks are useful portability evidence, but they do **not** compile a Black Ops multiplayer/gameplay translation unit, link the complete engine, or produce an APK. The extracted quaternion subset is a focused regression harness, not the full `com_math.cpp` translation unit. Host runtime tests do not prove Android runtime behavior.

## Remaining high-priority blockers

1. **Compilability:** the full upstream engine is not a CMake target in this port. Existing checks compile probes, compatibility tests and selected math/utility code only.
2. **Platform isolation:** upstream still depends on Windows entry points and services, WinSock/Windows SDK assumptions, DirectX-oriented build configuration and MSVC/x86 options. The portability shims are not a complete platform layer.
3. **LP64:** Android outputs are checked as ELF64/AArch64 and the platform probe checks ABI properties. There is no engine-wide audit of pointer/integer conversions, structure layouts or Windows type assumptions.
4. **Graphics bootstrap:** no native Android renderer is integrated into this native-engine branch.
5. **Map loading:** `mp_nuked` is a scope guard in the platform probe, not implemented map support. Original map parsing, material/asset loading, collision and spawn validation remain absent.
6. **Multiplayer:** no playable engine, host/join flow or network session is implemented.
7. **Performance:** no gameplay-level frame-time, memory, GPU or network measurements exist yet.

## Next acceptance gate

Compile at least one real, non-math KisakBlack gameplay or platform-service translation unit with Android Clang targeting `aarch64-linux-android26`. Keep its dependencies explicit, apply portability patches in CI, and verify the resulting object/ELF architecture. Prefer a small source unit with limited Win32/DirectX dependencies. Do not count a probe, a stub-only test, or an extracted helper as a gameplay-port milestone.

Before distributing any upstream-derived binaries or source, confirm the applicable license and redistribution rights. Do not replace authentic Black Ops behavior with generic FPS components while describing it as the original port.
