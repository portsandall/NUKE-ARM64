#!/usr/bin/env python3
"""Make the runtime broad_phase_memory size assertion LP64-aware.

The separate sweep-and-prune assertion is guarded only so this focused
broad_phase_memory header probe can compile. The full-engine diagnostic does
not define NUKE_BROAD_PHASE_MEMORY_LAYOUT_ONLY, so the sweep-and-prune
assertion remains active and continues to expose its independent ABI defect.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: port_broad_phase_memory_layout_lp64.py <phys_broad_phase.h>")

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")

old_memory = "static_assert(sizeof(broad_phase_memory) == 0xCD8);"
new_memory = """static_assert(sizeof(broad_phase_memory) ==
              (sizeof(void *) == 8 ? 0x1958 : 0xCD8),
              "broad_phase_memory must follow native pointer width");"""

old_sap = "static_assert(sizeof(axis_aligned_sweep_and_prune) == 40);"
new_sap = """#if !defined(NUKE_BROAD_PHASE_MEMORY_LAYOUT_ONLY)
static_assert(sizeof(axis_aligned_sweep_and_prune) == 40);
#endif"""

if source.count(old_memory) != 1:
    raise SystemExit(
        f"expected one broad_phase_memory assertion, found {source.count(old_memory)}"
    )
if source.count(old_sap) != 1:
    raise SystemExit(
        f"expected one sweep-and-prune assertion, found {source.count(old_sap)}"
    )

source = source.replace(old_memory, new_memory, 1)
source = source.replace(old_sap, new_sap, 1)

if old_memory in source:
    raise SystemExit("legacy broad_phase_memory assertion remains")
if "#if !defined(NUKE_BROAD_PHASE_MEMORY_LAYOUT_ONLY)" not in source:
    raise SystemExit("focused layout-probe guard was not installed")

path.write_text(source, encoding="utf-8")
print("Updated broad_phase_memory size assertion for LP64 (0xCD8/0x1958).")
print("Kept the sweep-and-prune assertion active in the root diagnostic.")
