#!/usr/bin/env python3
"""Port the outer sweep-and-prune object layout and allocation alignment to LP64.

This is intentionally limited to the outer axis_aligned_sweep_and_prune
object. The nested sap_node/active_pair allocation and pointer-traversal work
is separate and remains visible in the full-engine audit.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit(
        "usage: port_sap_outer_layout_lp64.py <phys_broad_phase.h> <phys_broad_phase.cpp>"
    )

header_path = Path(sys.argv[1])
source_path = Path(sys.argv[2])
header = header_path.read_text(encoding="utf-8")
source = source_path.read_text(encoding="utf-8")

old_assert = "static_assert(sizeof(axis_aligned_sweep_and_prune) == 40);"
new_assert = """static_assert(sizeof(axis_aligned_sweep_and_prune) ==
              (sizeof(void *) == 8 ? 72 : 40),
              "axis_aligned_sweep_and_prune must follow native pointer width");"""

old_allocation = (
    "g_axis_aligned_sweep_and_prune = "
    "(axis_aligned_sweep_and_prune *)PMM_PERM_ALLOCATE("
    "sizeof(axis_aligned_sweep_and_prune), 4);"
)
new_allocation = (
    "g_axis_aligned_sweep_and_prune = "
    "(axis_aligned_sweep_and_prune *)PMM_PERM_ALLOCATE("
    "sizeof(axis_aligned_sweep_and_prune), alignof(axis_aligned_sweep_and_prune));"
)

if header.count(old_assert) != 1:
    raise SystemExit(
        f"expected exactly one outer SAP size assertion, found {header.count(old_assert)}"
    )
if source.count(old_allocation) != 1:
    raise SystemExit(
        "expected exactly one outer SAP allocation with four-byte alignment, "
        f"found {source.count(old_allocation)}"
    )

patched_header = header.replace(old_assert, new_assert, 1)
patched_source = source.replace(old_allocation, new_allocation, 1)

if old_assert in patched_header or old_allocation in patched_source:
    raise SystemExit("legacy outer SAP layout/allocation assumption remains")
if "alignof(axis_aligned_sweep_and_prune)" not in patched_source:
    raise SystemExit("native outer SAP allocation alignment was not installed")

header_path.write_text(patched_header, encoding="utf-8")
source_path.write_text(patched_source, encoding="utf-8")
print("Updated outer SAP size assertion for IA-32/LP64 (40/72 bytes).")
print("Updated permanent outer SAP allocation to alignof(axis_aligned_sweep_and_prune).")
print("Nested sap_node/active_pair storage and pointer traversal were not modified.")
