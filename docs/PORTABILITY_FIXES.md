# Portability patch 0001 — bitarray varargs

Upstream source: `SwagSoftware/KisakBlack` commit `306bb14a8e052a6244bd1df4e4df7d8504c04ef4`.

Issue: `src/qcommon/bitarray.h` incorrectly declares a `char* argList` then calls `va_copy(argList, va)` and `va_arg(argList, ...)`. On AArch64 `va_list` is not a `char*`, and the copied list is never ended. This is an invalid use of variadic arguments.

Fix: consume arguments from the actual `va_list va`, remove the `char*` surrogate and close the list with `va_end(va)` once the `~0u` sentinel has been observed. Patch is stored in `patches/0001-fix-aarch64-bitarray-varargs.patch`; original upstream sources stay in a separate clone.

Local verification on Termux AArch64: `clang++ -std=c++17 -fms-extensions -fsyntax-only -Isrc` with a probe including `qcommon/bitarray.h` and instantiating `bitarray<128>(1u,63u,127u,~0u)` succeeded. `git diff --check` succeeded. This confirms syntax/instantiation only, not runtime behavior or gameplay compilation.

Next unresolved error: `src/physics/phys_local.h` directly imports `Windows.h` for Interlocked primitives and Windows fences. Requires a carefully audited cross-platform atomic implementation with preserved memory ordering; merely guarding the include is insufficient.

Apply from upstream checkout: `git apply /path/to/NUKE-ARM64/patches/0001-fix-aarch64-bitarray-varargs.patch`.
