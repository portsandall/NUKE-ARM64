#include <physics/phys_gjk.h>

#include <cstddef>
#include <type_traits>

using GjkCacheNode =
    phys_heap_gjk_cache_system_avl_tree::phys_gjk_cache_info_internal;

static_assert(sizeof(void *) == 8, "This regression targets Android LP64");
static_assert(sizeof(GjkCacheNode) == 0xA0,
              "GJK cache node must use the native-pointer LP64 layout");
static_assert(alignof(GjkCacheNode) >= alignof(void *),
              "GJK cache node must preserve native pointer alignment");
static_assert(sizeof(GjkCacheNode) % 16 == 0,
              "GJK cache node must retain its 16-byte PMM allocation granularity");
static_assert(std::is_pointer_v<decltype(GjkCacheNode::m_next_gjk_ci)>,
              "GJK cache linked-list link must remain a native pointer");

int nuke_upstream_gjk_cache_layout_probe()
{
    return static_cast<int>(sizeof(GjkCacheNode));
}
