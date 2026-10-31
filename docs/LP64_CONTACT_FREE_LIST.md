# LP64 rigid-body contact free-list port

Pinned source: `SwagSoftware/KisakBlack` at
`306bb14a8e052a6244bd1df4e4df7d8504c04ef4`.

The original rigid-body contact node and its `phys_free_list` wrapper encode
IA-32 sizes:

| Object/property | IA-32 | LP64 |
|---|---:|---:|
| `rigid_body_constraint_contact` | 44 bytes | 88 bytes |
| `phys_free_list<...>::T_internal` | 56 bytes | 112 bytes |
| `alignof(T_internal)` | 4 bytes | 8 bytes |
| PMM allocation alignment | 4 bytes | 16 bytes |

The LP64 wrapper needs eight-byte type alignment for its native pointers.
However, the existing generic allocator requests 16-byte alignment whenever
`sizeof(T_internal)` is a multiple of 16. The 112-byte LP64 wrapper satisfies
that size-class rule, so the contact allocation, validation, and free paths
must consistently use 16-byte PMM alignment. The regression checks both the
eight-byte C++ type alignment and the 16-byte allocator request; these are
different properties.

The Android portability transformation in
`tests/port_rigid_body_contact_lp64.py` preserves the IA-32 assertions while
using native LP64 sizes and the existing PMM alignment policy for the contact
free-list path. It updates the generic free-list alignment selection and the
explicit contact allocation, validation, and free sites in
`physics_system.cpp`, `physics_system_internal.cpp`, and
`rbc_def_contact.cpp`.

The transformation runs only against the disposable pinned upstream checkout
in CI; it does not modify `SwagSoftware/KisakBlack`.

The companion compile-time regression is
`tests/upstream_rigid_body_contact_layout.cpp`. It checks the actual upstream
declarations, the free-list wrapper size/alignment, and the allocator
granularity on the host and Android NDK targets.

This is a layout/allocation-metadata portability step, not evidence that the
physics runtime or complete game engine has been validated. The root engine
diagnostic remains the acceptance gate; the Windows job-queue implementation
is a separate outstanding platform dependency.
