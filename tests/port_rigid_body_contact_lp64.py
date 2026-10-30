#!/usr/bin/env python3
"""Port the runtime rigid-body contact free-list layout to native LP64.

The contact object and its free-list wrapper contain native pointers. Keep the
original IA-32 sizes, but use native sizeof/alignment for every contact-list
allocation, validation, and free operation in the pinned CI checkout.
"""
from __future__ import annotations

import sys
from pathlib import Path

CONTACT = "phys_free_list<rigid_body_constraint_contact>"
TI = f"{CONTACT}::T_internal"
ALIGN = f"{CONTACT}::allocation_alignment"
SIZE = f"sizeof({TI})"


def replace_count(source: str, old: str, new: str, expected: int, label: str) -> str:
    old_count = source.count(old)
    new_count = source.count(new)
    if old_count == expected and new_count == 0:
        source = source.replace(old, new)
        print(f"Updated {label} ({expected})")
    elif old_count == 0 and new_count == expected:
        print(f"Already updated {label} ({expected})")
    else:
        raise RuntimeError(
            f"{label}: expected {expected} original or transformed occurrences; "
            f"found original={old_count}, transformed={new_count}"
        )
    return source


def replace_one(source: str, old: str, new: str, label: str) -> str:
    return replace_count(source, old, new, 1, label)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <KisakBlack checkout>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1])
    paths = {
        "rigid_body": root / "src/physics/rigid_body.h",
        "phys_local": root / "src/physics/phys_local.h",
        "physics_system": root / "src/physics/physics_system.cpp",
        "physics_system_internal": root / "src/physics/physics_system_internal.cpp",
        "contact_impl": root / "tl/physics/rbc_def_contact.cpp",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise RuntimeError("required contact allocator source files are missing: " + ", ".join(missing))

    # The contact node itself grows from 44 to 88 bytes because its lists,
    # AVL links, and pair key contain native pointers.
    text = paths["rigid_body"].read_text(encoding="utf-8")
    text = replace_one(
        text,
        "static_assert(sizeof(rigid_body_constraint_contact) == 0x2C);",
        """static_assert(
    sizeof(rigid_body_constraint_contact) == (sizeof(void *) == 8 ? 0x58 : 0x2C),
    "rigid_body_constraint_contact contains native pointers");""",
        "contact object size assertion",
    )
    paths["rigid_body"].write_text(text, encoding="utf-8")

    # The generic free-list wrapper must request the actual alignment of T_internal.
    text = paths["phys_local"].read_text(encoding="utf-8")
    marker = "template <typename T>\nstruct phys_free_list\n{"
    if marker not in text:
        raise RuntimeError("phys_free_list template marker not found")
    prefix, tail = text.split(marker, 1)
    member = "        int m_ptr_list_index;\n    };"
    member_with_alignment = member + """

    static constexpr unsigned int allocation_alignment =
        sizeof(T_internal) % 16 == 0 ? 16u :
        (alignof(T_internal) > 4 ? alignof(T_internal) : 4u);
"""
    tail = replace_one(tail, member, member_with_alignment, "free-list alignment constant")
    tail = replace_count(
        tail,
        "sizeof(T_internal) % 16 == 0 ? 16 : 4",
        "allocation_alignment",
        4,
        "generic free-list allocate/validate/free alignment",
    )
    text = prefix + marker + tail
    paths["phys_local"].write_text(text, encoding="utf-8")

    # Keep the contact destroy path consistent with the generic allocator.
    text = paths["physics_system"].read_text(encoding="utf-8")
    start = text.find("void __cdecl phys_sys::destroy(rigid_body_constraint_contact *const rbc)")
    end = text.find("void __cdecl phys_sys::destroy(rigid_body_constraint_point", start)
    if start < 0 or end < 0:
        raise RuntimeError("contact destroy function boundaries not found")
    block = text[start:end]
    block = replace_one(
        block,
        "static_assert(sizeof(TI) == 0x38);",
        'static_assert(sizeof(TI) == (sizeof(void *) == 8 ? 0x70 : 0x38));',
        "contact free-list wrapper size assertion",
    )
    block = replace_one(
        block,
        "PMM_VALIDATE((char *)ti, sizeof(TI), 4u);",
        f"PMM_VALIDATE((char *)ti, sizeof(TI), {ALIGN});",
        "contact destroy validation alignment",
    )
    text = text[:start] + block + text[end:]

    replacements = (
        ("PMM_VALIDATE((char *)v73, 0x38u, 4u);",
         f"PMM_VALIDATE((char *)v73, {SIZE}, {ALIGN});", 2,
         "contact list validation through v73"),
        ("PMM_VALIDATE((char *)v75, 0x38u, 4u);",
         f"PMM_VALIDATE((char *)v75, {SIZE}, {ALIGN});", 1,
         "contact list validation through v75"),
        ("PMM_FREE((unsigned __int8 *)v78, 0x38u, 4u);",
         f"PMM_FREE((unsigned __int8 *)v78, {SIZE}, {ALIGN});", 2,
         "contact list free through v78"),
        ("PMM_FREE((unsigned __int8 *)v80, 0x38u, 4u);",
         f"PMM_FREE((unsigned __int8 *)v80, {SIZE}, {ALIGN});", 1,
         "contact list free through v80"),
        ("PMM_ALLOC(0x38u, 4u);",
         f"PMM_ALLOC({SIZE}, {ALIGN});", 1,
         "contact list allocation"),
    )
    for old, new, count, label in replacements:
        text = replace_count(text, old, new, count, label)
    paths["physics_system"].write_text(text, encoding="utf-8")

    # The internal cleanup path has one more hand-written contact free.
    text = paths["physics_system_internal"].read_text(encoding="utf-8")
    text = replace_one(
        text,
        "PMM_VALIDATE((char *)&v10[-1], 0x38u, 4u);",
        f"PMM_VALIDATE((char *)&v10[-1], {SIZE}, {ALIGN});",
        "internal contact cleanup validation",
    )
    text = replace_one(
        text,
        "PMM_FREE((unsigned __int8 *)v12, 0x38u, 4u);",
        f"PMM_FREE((unsigned __int8 *)v12, {SIZE}, {ALIGN});",
        "internal contact cleanup free",
    )
    paths["physics_system_internal"].write_text(text, encoding="utf-8")

    text = paths["contact_impl"].read_text(encoding="utf-8")
    text = replace_one(
        text,
        'static_assert(sizeof(TI) == 0x38, "size mismatch");',
        'static_assert(sizeof(TI) == (sizeof(void *) == 8 ? 0x70 : 0x38), "size mismatch");',
        "contact verification wrapper size assertion",
    )
    text = replace_one(
        text,
        "PMM_VALIDATE((char *)ti, sizeof(TI), 4u);",
        f"PMM_VALIDATE((char *)ti, sizeof(TI), {ALIGN});",
        "contact verification alignment",
    )
    paths["contact_impl"].write_text(text, encoding="utf-8")

    # Fail closed if any of the audited contact allocation metadata remains.
    checks = {
        "rigid_body": (
            "sizeof(rigid_body_constraint_contact) == (sizeof(void *) == 8 ? 0x58 : 0x2C)",
        ),
        "phys_local": (
            "static constexpr unsigned int allocation_alignment",
            "PMM_ALLOC(sizeof(T_internal), allocation_alignment)",
            "PMM_FREE((unsigned __int8 *)data, sizeof(T_internal), allocation_alignment)",
            "PMM_VALIDATE((char *)ti, sizeof(T_internal), allocation_alignment)",
        ),
        "physics_system": (
            f"PMM_ALLOC({SIZE}, {ALIGN});",
            f"PMM_VALIDATE((char *)v73, {SIZE}, {ALIGN});",
            f"PMM_VALIDATE((char *)v75, {SIZE}, {ALIGN});",
            f"PMM_FREE((unsigned __int8 *)v78, {SIZE}, {ALIGN});",
            f"PMM_FREE((unsigned __int8 *)v80, {SIZE}, {ALIGN});",
        ),
        "physics_system_internal": (
            f"PMM_VALIDATE((char *)&v10[-1], {SIZE}, {ALIGN});",
            f"PMM_FREE((unsigned __int8 *)v12, {SIZE}, {ALIGN});",
        ),
        "contact_impl": (
            f"PMM_VALIDATE((char *)ti, sizeof(TI), {ALIGN});",
        ),
    }
    for name, needles in checks.items():
        current = paths[name].read_text(encoding="utf-8")
        for needle in needles:
            if needle not in current:
                raise RuntimeError(f"{name}: transformed contact metadata missing: {needle}")
    print("Verified native contact object/free-list sizes and matching PMM allocation, validation, and free metadata.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Rigid-body contact LP64 port failed: {error}", file=sys.stderr)
        raise SystemExit(1)
