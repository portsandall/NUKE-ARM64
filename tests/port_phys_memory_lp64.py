#!/usr/bin/env python3
"""Port KisakBlack's physics linear allocator to native LP64 pointer semantics.

The pinned code treated char* buffer addresses as 32-bit integers, returned an
int from the allocator, hard-coded a 24-byte slot-pool allocation, and cleared
only 0x100 bytes of a 64-bucket pointer hash table. This edits only the
disposable pinned upstream checkout used by CI.
"""
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(data: bytes, old: bytes, new: bytes, label: str, count: int = 1) -> bytes:
    found = data.count(old)
    if found != count:
        raise RuntimeError(f"{label}: expected {count} original occurrence(s), found {found}")
    return data.replace(old, new, count)


def transform_header(path: Path) -> None:
    data = path.read_bytes()
    data = replace_once(
        data,
        b"static_assert(sizeof(phys_slot_pool) == 0x18);",
        b"""static_assert(sizeof(phys_slot_pool) ==
              (sizeof(void *) == 8 ? 0x28 : 0x18),
              "phys_slot_pool uses native-pointer runtime storage");""",
        "phys_slot_pool size assertion",
    )
    data = replace_once(
        data,
        b"    int allocate(unsigned int size, unsigned int alignment);",
        b"    char *allocate(unsigned int size, unsigned int alignment);",
        "phys_memory_manager allocate return type",
    )
    data = replace_once(
        data,
        b"static_assert(sizeof(phys_memory_manager) == 0x3D0);",
        b"""static_assert(sizeof(phys_memory_manager) ==
              (sizeof(void *) == 8 ? 0x6A0 : 0x3D0),
              "phys_memory_manager uses native-pointer runtime storage");""",
        "phys_memory_manager size assertion",
    )
    path.write_bytes(data)


def transform_source(path: Path) -> None:
    data = path.read_bytes()
    data = replace_once(
        data,
        b"""#include <Windows.h> // interlockedexchange
#include <new>
#include <universal/q_shared.h>
""",
        b"""#if defined(_WIN32)
#include <Windows.h> // interlockedexchange
#endif
#include <cstdint>
#include <limits>
#include <new>
#include <nuke/phys_buffer_allocator_compat.h>
#include <nuke/phys_free_list_compat.h>
#include <universal/q_shared.h>
""",
        "platform headers",
    )

    start_marker = b"int phys_memory_manager::allocate(unsigned int size, unsigned int alignment)\n{"
    end_marker = b"\nphys_slot_pool *phys_memory_manager::allocate_slot_pool()"
    if data.count(start_marker) != 1 or data.count(end_marker) != 1:
        raise RuntimeError("linear allocator function anchors changed")
    start = data.index(start_marker)
    end = data.index(end_marker, start)
    replacement = b"""char *phys_memory_manager::allocate(unsigned int size, unsigned int alignment)
{
    return nuke_port::allocate_aligned_buffer(
        &this->m_buffer_cur,
        this->m_buffer_end,
        static_cast<std::size_t>(size),
        static_cast<std::size_t>(alignment));
}
"""
    data = data[:start] + replacement + data[end + 1:]

    data = replace_once(
        data,
        b"    int v6; // eax",
        b"    char *v6; // allocated slot-pool storage",
        "slot-pool fallback pointer",
    )
    data = replace_once(
        data,
        b"        v6 = this->allocate(24, 8);",
        b"        v6 = this->allocate(sizeof(phys_slot_pool), alignof(phys_slot_pool));",
        "slot-pool fallback allocation size",
    )
    data = replace_once(
        data,
        b"memset(&this->m_slot_pool_map, 0, 0x100u);",
        b"memset(&this->m_slot_pool_map, 0, sizeof(this->m_slot_pool_map));",
        "hash-table initialization size",
        count=2,
    )

    data = replace_once(
        data,
        b"ei->m_allocation_owner = (void *)0xFEDCBA98;",
        b"ei->m_allocation_owner = reinterpret_cast<void *>(static_cast<std::uintptr_t>(0xFEDCBA98u));",
        "LP64 allocation-owner sentinel initialization",
    )
    data = replace_once(
        data,
        b"""    if ((phys_slot_pool *)_InterlockedCompareExchange(
        (volatile unsigned __int32 *)&ei->m_allocation_owner,
        0xFEDCBA98,
        (signed __int32)this) != this
""",
        b"""    void *const allocation_sentinel =
        reinterpret_cast<void *>(static_cast<std::uintptr_t>(0xFEDCBA98u));
    if (InterlockedCompareExchangePointer(
        reinterpret_cast<void * volatile *>(&ei->m_allocation_owner),
        allocation_sentinel,
        this) != this
""",
        "LP64 allocation-owner atomic claim",
    )
    data = replace_once(
        data,
        b"""    _InterlockedExchangeAdd((volatile long *)&this->m_allocated_slot_count, 1u);""",
        b"""    _InterlockedExchangeAdd((volatile unsigned int *)&this->m_allocated_slot_count, 1u);""",
        "32-bit allocated-slot counter increment",
    )
    data = replace_once(
        data,
        b"""    if ((phys_slot_pool *)_InterlockedCompareExchange(
        (volatile unsigned __int32 *)&ei->m_allocation_owner,
        (signed __int32)this,
        0xFEDCBA98) != (phys_slot_pool *)0xFEDCBA98
""",
        b"""    void *const allocation_sentinel =
        reinterpret_cast<void *>(static_cast<std::uintptr_t>(0xFEDCBA98u));
    if (InterlockedCompareExchangePointer(
        reinterpret_cast<void * volatile *>(&ei->m_allocation_owner),
        this,
        allocation_sentinel) != allocation_sentinel
""",
        "LP64 allocation-owner atomic release",
    )
    data = replace_once(
        data,
        b"""    _InterlockedExchangeAdd((volatile long *)&this->m_allocated_slot_count, (unsigned long)-1);""",
        b"""    _InterlockedExchangeAdd((volatile unsigned int *)&this->m_allocated_slot_count, 0xFFFFFFFFu);""",
        "32-bit allocated-slot counter decrement",
    )
    data = replace_once(
        data,
        b"""    if ((unsigned int)ei->m_allocation_owner != 0xFEDCBA98""",
        b"""    if (ei->m_allocation_owner != reinterpret_cast<void *>(static_cast<std::uintptr_t>(0xFEDCBA98u))""",
        "LP64 allocation-owner validation",
    )

    init_start = b"void __cdecl phys_memory_manager_init(void *const memory_buffer, int memory_buffer_size)\n{"
    init_end = b"\nvoid phys_slot_pool::extra_info_init(char *slot)"
    if data.count(init_start) != 1 or data.count(init_end) != 1:
        raise RuntimeError("phys_memory_manager_init anchors changed")
    first = data.index(init_start)
    last = data.index(init_end, first)
    init_replacement = b"""void __cdecl phys_memory_manager_init(void *const memory_buffer, int memory_buffer_size)
{
    if (g_phys_memory_buffer)
    {
        if (_tlAssert("source/phys_mem_new.cpp", 237, "g_phys_memory_buffer == NULL", ""))
            __debugbreak();
        return;
    }
    if (g_phys_memory_buffer_size)
    {
        if (_tlAssert("source/phys_mem_new.cpp", 238, "g_phys_memory_buffer_size == 0", ""))
            __debugbreak();
        return;
    }
    if (g_phys_memory_manager)
    {
        if (_tlAssert("source/phys_mem_new.cpp", 239, "g_phys_memory_manager == NULL", ""))
            __debugbreak();
        return;
    }
    if (!memory_buffer || memory_buffer_size <= 0)
    {
        if (_tlAssert("source/phys_mem_new.cpp", 242, "memory_buffer != NULL && memory_buffer_size > 0", ""))
            __debugbreak();
        return;
    }

    const std::uintptr_t base = reinterpret_cast<std::uintptr_t>(memory_buffer);
    const std::uintptr_t bytes = static_cast<std::uintptr_t>(memory_buffer_size);
    const std::uintptr_t max_address =
        std::numeric_limits<std::uintptr_t>::max();
    if (base > max_address - bytes || base > max_address - std::uintptr_t{7})
    {
        if (_tlAssert("source/phys_mem_new.cpp", 247, "physics memory buffer address does not overflow", ""))
            __debugbreak();
        return;
    }

    const std::uintptr_t end = base + bytes;
    const std::uintptr_t manager_address =
        (base + std::uintptr_t{7}) & ~std::uintptr_t{7};
    if (manager_address > end ||
        sizeof(phys_memory_manager) > end - manager_address)
    {
        if (_tlAssert("source/phys_mem_new.cpp", 255, "physics memory buffer can hold phys_memory_manager", ""))
            __debugbreak();
        return;
    }

    const std::uintptr_t allocator_buffer_address =
        manager_address + sizeof(phys_memory_manager);
    const std::uintptr_t allocator_buffer_size = end - allocator_buffer_address;
    if (allocator_buffer_size >
        static_cast<std::uintptr_t>(std::numeric_limits<int>::max()))
    {
        if (_tlAssert("source/phys_mem_new.cpp", 264, "physics allocator buffer size fits int", ""))
            __debugbreak();
        return;
    }

    g_phys_memory_buffer = memory_buffer;
    g_phys_memory_buffer_size = memory_buffer_size;
    g_phys_memory_manager =
        reinterpret_cast<phys_memory_manager *>(manager_address);

    new (reinterpret_cast<void *>(manager_address)) phys_memory_manager(
        reinterpret_cast<char *>(allocator_buffer_address),
        static_cast<int>(allocator_buffer_size));
}
"""
    data = data[:first] + init_replacement + data[last + 1:]

    data = replace_once(
        data,
        b"""    signed __int64 cur, next;

    if (!slot && _tlAssert("source/phys_mem_new.cpp", 445, "slot", "no support for freeing NULL slots."))
        __debugbreak();

    this->extra_info_free(slot);

    while (1)
    {
        cur = *(volatile signed __int64 *)&this->m_first_free_slot;
        *(unsigned int *)slot = LODWORD(cur); // link slot->next = current head
        next = __SPAIR64__(HIDWORD(cur) + 1, (unsigned int)slot);
        if (_InterlockedCompareExchange64(
            (volatile signed __int64 *)&this->m_first_free_slot,
            next,
            cur) == cur)
            break;
        // CAS failed, retry
    }
""",
        b"""    if (!slot && _tlAssert("source/phys_mem_new.cpp", 445, "slot", "no support for freeing NULL slots."))
        __debugbreak();

    this->extra_info_free(slot);

    auto *free_list = const_cast<tagged_void_pointer_t *>(&this->m_first_free_slot);
    nuke_port::phys_free_list_push(&free_list->m_ptr, &free_list->m_tag, slot);
""",
        "LP64 free-slot native-pointer list insertion",
    )

    data = replace_once(
        data,
        b"""    signed __int64 cur, next;
    char *v3;

    while (1)
    {
        cur = *(volatile signed __int64 *)&this->m_first_free_slot;
        v3 = (char *)LODWORD(cur);
        if (!v3)
            break; // free list empty, fall through to fresh alloc

        next = __SPAIR64__(HIDWORD(cur) + 1, *(unsigned int *)v3);
        if (_InterlockedCompareExchange64(
            (volatile signed __int64 *)&this->m_first_free_slot,
            next,
            cur) == cur)
        {
            this->extra_info_allocate(v3);
            return v3;
        }
        // CAS failed, retry
    }

""",
        b"""    auto *free_list = const_cast<tagged_void_pointer_t *>(&this->m_first_free_slot);
    char *v3 = static_cast<char *>(
        nuke_port::phys_free_list_pop(&free_list->m_ptr, &free_list->m_tag));
    if (v3)
    {
        this->extra_info_allocate(v3);
        return v3;
    }

""",
        "LP64 free-slot native-pointer list removal",
    )
    path.write_bytes(data)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <KisakBlack checkout>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1])
    header = root / "src/physics/phys_mem_new.h"
    source = root / "src/physics/phys_mem_new.cpp"
    if not header.is_file() or not source.is_file():
        raise RuntimeError("pinned physics memory-manager source files are missing")

    helper_source = Path(__file__).with_name("upstream_phys_buffer_allocator.h")
    helper_target = root / "src/nuke/phys_buffer_allocator_compat.h"
    helper_target.parent.mkdir(parents=True, exist_ok=True)
    helper = helper_source.read_bytes()
    if helper_target.exists() and helper_target.read_bytes() != helper:
        raise RuntimeError("existing phys_buffer_allocator_compat.h differs from tested helper")
    helper_target.write_bytes(helper)

    free_list_helper_source = Path(__file__).with_name("upstream_phys_free_list_compat.h")
    free_list_helper_target = root / "src/nuke/phys_free_list_compat.h"
    free_list_helper = free_list_helper_source.read_bytes()
    if free_list_helper_target.exists() and free_list_helper_target.read_bytes() != free_list_helper:
        raise RuntimeError("existing phys_free_list_compat.h differs from tested helper")
    free_list_helper_target.write_bytes(free_list_helper)

    transform_header(header)
    transform_source(source)

    header_after = header.read_bytes()
    source_after = source.read_bytes()
    for marker in (
        b"sizeof(void *) == 8 ? 0x28 : 0x18",
        b"sizeof(void *) == 8 ? 0x6A0 : 0x3D0",
        b"char *allocate(unsigned int size, unsigned int alignment);",
    ):
        if marker not in header_after:
            raise RuntimeError(f"transformed header missing {marker!r}")
    for marker in (
        b"nuke_port::allocate_aligned_buffer",
        b"sizeof(this->m_slot_pool_map)",
        b"reinterpret_cast<std::uintptr_t>(memory_buffer)",
        b"sizeof(phys_slot_pool), alignof(phys_slot_pool)",
        b"InterlockedCompareExchangePointer(",
        b"volatile unsigned int *)&this->m_allocated_slot_count",
        b"nuke_port::phys_free_list_push(",
        b"nuke_port::phys_free_list_pop(",
    ):
        if marker not in source_after:
            raise RuntimeError(f"transformed source missing {marker!r}")
    if source_after.count(b"InterlockedCompareExchangePointer(") != 2:
        raise RuntimeError("both allocation-owner transitions must use pointer-width atomic compare/exchange")
    if b"(volatile long *)&this->m_allocated_slot_count" in source_after:
        raise RuntimeError("LP64 long width must not be used for the 32-bit slot counter")
    free_start = source_after.index(b"void phys_slot_pool::free_slot(unsigned __int8 *slot)")
    free_end = source_after.index(b"char * phys_slot_pool::allocate_slot()", free_start)
    free_function = source_after[free_start:free_end]
    free_active_start = free_function.index(b"#else")
    free_active_end = free_function.index(b"#endif", free_active_start)
    free_active = free_function[free_active_start:free_active_end]
    if any(marker in free_active for marker in (
        b"__SPAIR64__", b"LODWORD(cur)", b"(unsigned int)slot",
        b"*(unsigned int *)slot",
    )):
        raise RuntimeError("LP64 free-slot path still packs pointers into 32-bit halves")

    allocate_start = free_end
    allocate_else = source_after.index(b"#else // aislop", allocate_start)
    allocate_end = source_after.index(b"#endif", allocate_else)
    allocate_active = source_after[allocate_else:allocate_end]
    if b"__SPAIR64__" in allocate_active or b"LODWORD(cur)" in allocate_active:
        raise RuntimeError("LP64 allocate-slot path still truncates free-list pointers")

    constructor = source_after[source_after.index(b"phys_memory_manager::phys_memory_manager"):]
    if b"0x100u" in constructor:
        raise RuntimeError("fixed-size hash-table clearing remains in constructor")

    print("Ported phys_memory_manager allocation to native pointer-width compare/exchange.")
    print("Verified IA-32 and LP64 slot-pool and manager layout assertions.")
    print("Verified fallback allocations use sizeof/alignof(phys_slot_pool).")
    print("Verified the complete 64-bucket pointer hash table is initialized.")
    print("Verified memory-buffer alignment and bounds use uintptr_t.")
    print("Replaced packed 32-bit free-list halves with locked native-pointer links.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"physics allocator LP64 port failed: {error}", file=sys.stderr)
        raise SystemExit(1)
