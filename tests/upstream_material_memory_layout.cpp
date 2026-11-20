#include <cstddef>
#include <gfx_d3d/r_material_memory.h>

constexpr std::size_t expected_size =
    ((sizeof(void *) + sizeof(int) + alignof(void *) - 1) / alignof(void *))
    * alignof(void *);

static_assert(offsetof(MaterialMemory, material) == 0,
              "MaterialMemory material pointer offset changed");
static_assert(offsetof(MaterialMemory, memory) == sizeof(void *),
              "MaterialMemory integer field offset changed");
static_assert(alignof(MaterialMemory) == alignof(void *),
              "MaterialMemory must retain native pointer alignment");
static_assert(sizeof(MaterialMemory) == expected_size,
              "MaterialMemory native runtime size changed");

int nuke_material_memory_layout_probe()
{
    return static_cast<int>(sizeof(MaterialMemory));
}
