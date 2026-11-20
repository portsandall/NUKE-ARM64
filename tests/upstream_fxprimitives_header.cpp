#include <gfx_d3d/fxprimitives.h>

#include <type_traits>

static_assert(sizeof(Material*) == sizeof(void*),
              "Material pointer must retain the native pointer width");
static_assert(std::is_same_v<decltype(FxSpriteInfo::material), Material*>,
              "FxSpriteInfo must retain its Material pointer field");
static_assert(std::is_same_v<decltype(FxElemMarkVisuals::materials), Material*[2]>,
              "FxElemMarkVisuals must retain its two Material pointer fields");

int nuke_upstream_fxprimitives_header_probe()
{
    FxSpriteInfo sprite{};
    FxElemMarkVisuals marks{};
    return sprite.material == nullptr && marks.materials[0] == nullptr ? 0 : 1;
}
