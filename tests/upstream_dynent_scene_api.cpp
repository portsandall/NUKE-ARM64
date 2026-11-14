#include <gfx_d3d/r_dynent_scene_api.h>

#include <cstddef>
#include <type_traits>

using GetBrushModelFn = GfxBrushModel *(__cdecl *)(unsigned int);
using LinkDynEntFn = void (__cdecl *)(unsigned int, DynEntityDrawType, float *, float *);
using UnlinkDynEntFn = void (__cdecl *)(unsigned int, DynEntityDrawType);

static_assert(sizeof(std::underlying_type_t<DynEntityDrawType>) == 4,
              "DynEntityDrawType must retain its 32-bit ABI");
static_assert(sizeof(GfxBrushModelWritable) == 0x1C,
              "GfxBrushModelWritable layout changed");
static_assert(sizeof(GfxBrushModel) == 0x3C,
              "GfxBrushModel layout changed");
static_assert(offsetof(GfxBrushModel, writable) == 0x00,
              "GfxBrushModel writable offset changed");
static_assert(offsetof(GfxBrushModel, bounds) == 0x1C,
              "GfxBrushModel bounds offset changed");
static_assert(offsetof(GfxBrushModel, surfaceCount) == 0x34,
              "GfxBrushModel surfaceCount offset changed");
static_assert(offsetof(GfxBrushModel, startSurfIndex) == 0x38,
              "GfxBrushModel startSurfIndex offset changed");
static_assert(std::is_same_v<decltype(&R_GetBrushModel), GetBrushModelFn>,
              "R_GetBrushModel declaration changed");
static_assert(std::is_same_v<decltype(&R_LinkDynEnt), LinkDynEntFn>,
              "R_LinkDynEnt declaration changed");
static_assert(std::is_same_v<decltype(&R_UnlinkDynEnt), UnlinkDynEntFn>,
              "R_UnlinkDynEnt declaration changed");

int nuke_upstream_dynent_scene_api_probe()
{
    return 0;
}
