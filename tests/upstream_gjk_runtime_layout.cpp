#include <physics/phys_colgeom.h>

static_assert(sizeof(void *) == 8, "This regression targets LP64");
static_assert(sizeof(gjk_aabb_t) == 144, "gjk_aabb_t LP64 layout changed");
static_assert(sizeof(gjk_obb_t) == 176, "gjk_obb_t LP64 layout changed");
static_assert(sizeof(gjk_brush_t) == 112, "gjk_brush_t LP64 layout changed");
static_assert(sizeof(gjk_partition_t) == 128, "gjk_partition_t LP64 layout changed");
static_assert(sizeof(gjk_double_sphere_t) == 160, "gjk_double_sphere_t LP64 layout changed");
static_assert(sizeof(gjk_cylinder_t) == 176, "gjk_cylinder_t LP64 layout changed");
static_assert(sizeof(gjk_polygon_cylinder_t) == 144, "gjk_polygon_cylinder_t LP64 layout changed");

static_assert(alignof(gjk_aabb_t) == 16, "gjk_aabb_t alignment changed");
static_assert(alignof(gjk_partition_t) == 16, "gjk_partition_t alignment changed");

int nuke_upstream_gjk_runtime_layout_probe()
{
    return static_cast<int>(sizeof(gjk_aabb_t) + sizeof(gjk_obb_t) +
                            sizeof(gjk_brush_t) + sizeof(gjk_partition_t) +
                            sizeof(gjk_double_sphere_t) + sizeof(gjk_cylinder_t) +
                            sizeof(gjk_polygon_cylinder_t));
}
