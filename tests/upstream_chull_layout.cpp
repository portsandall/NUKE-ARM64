#include <cstddef>
#include <physics/phys_local.h>

// The convex hull node is a runtime linked-list object containing native
// pointers. Validate both the retained 32-bit ABI and the LP64 layout.
static_assert(sizeof(void *) == 4 || sizeof(void *) == 8);
static_assert(alignof(chull_t) == alignof(void *));
static_assert(sizeof(chull_t) == (sizeof(void *) == 8 ? 0x38 : 0x20));

static_assert(offsetof(chull_t, key) == 0);
static_assert(offsetof(chull_t, nverts) == 4);
static_assert(offsetof(chull_t, verts) == 8);
static_assert(offsetof(chull_t, ninds) == (sizeof(void *) == 8 ? 16 : 12));
static_assert(offsetof(chull_t, inds) == (sizeof(void *) == 8 ? 24 : 16));
static_assert(offsetof(chull_t, next) == (sizeof(void *) == 8 ? 32 : 20));
static_assert(offsetof(chull_t, touched) == (sizeof(void *) == 8 ? 40 : 24));
static_assert(offsetof(chull_t, next_list) == (sizeof(void *) == 8 ? 48 : 28));
