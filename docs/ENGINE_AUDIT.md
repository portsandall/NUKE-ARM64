# First blocker: upstream Windows/x86 build system

Audit target: SwagSoftware/KisakBlack @ 306bb14a8e052a6244bd1df4e4df7d8504c04ef4.

The upstream Windows/DirectX-oriented CMake configuration cannot be sent unchanged to the Android NDK. The first engineering task is to map the source tree and separate engine and gameplay translation units from DirectX rendering, Win32 entrypoints, WinSock, Windows SDK and x86 ABI assumptions.

Do NOT silently replace authentic Black Ops gameplay with generic FPS components. Before importing upstream code, verify redistribution license, third-party dependencies and whether the required game source is actually available.

Next acceptance test: compile at least one real KisakBlack multiplayer translation unit with Android Clang targeting aarch64, with third-party dependencies isolated and reproducible CI diagnostics. The current `nuke-platform-probe` is only infrastructure and does NOT satisfy that test.
