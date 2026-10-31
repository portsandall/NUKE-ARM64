#include <cstddef>
#include <qcommon/com_bsp_load_obj.h>

static_assert(sizeof(void *) == 8, "This regression is intended for LP64 targets");
static_assert(sizeof(ComPrimaryLight) == 224, "ComPrimaryLight LP64 size changed");
static_assert(alignof(ComPrimaryLight) == 8, "ComPrimaryLight LP64 alignment changed");
static_assert(offsetof(ComPrimaryLight, defName) == 216, "ComPrimaryLight pointer offset changed");

// Serialized BSP records retain their fixed-width disk layouts.
static_assert(sizeof(DiskPrimaryLight) == 0x10C, "DiskPrimaryLight disk layout changed");
static_assert(sizeof(DiskPrimaryLight_Version16) == 0x60, "Version-16 disk layout changed");

int nuke_com_primary_light_layout_probe()
{
    return static_cast<int>(sizeof(ComPrimaryLight) + sizeof(DiskPrimaryLight));
}
