#define NUKE_BROAD_PHASE_MEMORY_LAYOUT_ONLY 1
#include <physics/phys_broad_phase.h>

#include <cstddef>
#include <type_traits>

static_assert(sizeof(void *) == 8, "This regression targets LP64");
static_assert(sizeof(broad_phase_memory) == 0x1958,
              "broad_phase_memory must be 6488 bytes on LP64");
static_assert(alignof(broad_phase_memory) >= alignof(void *),
              "broad_phase_memory must satisfy native pointer alignment");
static_assert(sizeof(broad_phase_memory) % alignof(void *) == 0,
              "broad_phase_memory size must preserve pointer alignment");
static_assert(std::is_same_v<decltype(broad_phase_memory::g_list_bpb),
                             broad_phase_base *>);
static_assert(std::is_same_v<
              decltype(broad_phase_memory::g_broad_phase_terrain_query_callback),
              broad_phase_terrain_query_callback *>);

int nuke_upstream_broad_phase_memory_layout_probe()
{
    return static_cast<int>(sizeof(broad_phase_memory));
}
