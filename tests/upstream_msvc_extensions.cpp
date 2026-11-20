#include <DemonWare/bdCore/bdContainers/bdBitBuffer.h>
#include <DemonWare/bdCore/bdContainers/bdByteBuffer.h>
#include <universal/dvar.h>
#include <universal/q_shared.h>

static_assert(sizeof(__int32) == 4, "__int32 must remain 32-bit");
static_assert(sizeof(__int64) == 8, "__int64 must remain 64-bit");
static_assert(sizeof(unsigned __int8) == 1, "unsigned __int8 must remain 8-bit");
static_assert(sizeof(unsigned __int64) == 8, "unsigned __int64 must remain 64-bit");

struct __declspec(align(16)) NukeMsAlignmentProbe {
    unsigned char value;
};
static_assert(alignof(NukeMsAlignmentProbe) == 16,
              "__declspec(align(16)) must be honored");

static_assert(sizeof(DvarValue) == 16, "DvarValue layout changed");
static_assert(sizeof(DvarLimits) == 16, "DvarLimits layout changed");
static_assert(alignof(dvar_s) == 8, "dvar_s must remain 8-byte aligned");
static_assert(alignof(bdBitBuffer) >= 4, "bdBitBuffer alignment regressed");
static_assert(alignof(bdByteBuffer) >= 2, "bdByteBuffer alignment regressed");

// Include the native-pointer physics-node layout regression in the existing
// host and Android MSVC-extension compile probe.
#include "upstream_chull_layout.cpp"

#include <cstddef>
#include <physics/phys_mem_new.h>

static_assert(sizeof(phys_slot_pool) == (sizeof(void *) == 8 ? 40 : 24),
              "phys_slot_pool pointer-width layout changed");
static_assert(offsetof(phys_slot_pool, m_map_key) ==
                  (sizeof(void *) == 8 ? 16 : 8),
              "phys_slot_pool::m_map_key offset changed");
static_assert(offsetof(phys_slot_pool, m_hash_next) ==
                  (sizeof(void *) == 8 ? 24 : 12),
              "phys_slot_pool::m_hash_next offset changed");
static_assert(offsetof(phys_slot_pool, m_total_slot_count) ==
                  (sizeof(void *) == 8 ? 32 : 16),
              "phys_slot_pool::m_total_slot_count offset changed");
static_assert(offsetof(phys_slot_pool, m_allocated_slot_count) ==
                  (sizeof(void *) == 8 ? 36 : 20),
              "phys_slot_pool::m_allocated_slot_count offset changed");
static_assert(sizeof(phys_memory_manager) ==
                  (sizeof(void *) == 8 ? 1696 : 976),
              "phys_memory_manager pointer-width layout changed");
static_assert(sizeof(((phys_memory_manager *)nullptr)->m_slot_pool_map.m_hash_table) ==
                  64 * sizeof(phys_slot_pool *),
              "all 64 hash buckets must use native pointers");
static_assert(sizeof(((phys_memory_manager *)nullptr)->m_list_preallocated_slot_pools) ==
                  28 * sizeof(phys_slot_pool),
              "preallocated slot-pool storage must match native slot-pool size");
