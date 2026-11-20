#include <qcommon/shader_constant_set_types.h>

#include <cstddef>
#include <type_traits>

static_assert(std::is_standard_layout_v<ShaderConstantSet>);
static_assert(sizeof(ShaderConstantSet) == 0x78);
static_assert(alignof(ShaderConstantSet) == alignof(float));
static_assert(offsetof(ShaderConstantSet, value) == 0x00);
static_assert(offsetof(ShaderConstantSet, constantSource) == 0x70);
static_assert(offsetof(ShaderConstantSet, used) == 0x77);
static_assert(std::is_same_v<decltype(ShaderConstantSet::value), float[7][4]>);
static_assert(std::is_same_v<decltype(ShaderConstantSet::constantSource), unsigned char[7]>);
static_assert(std::is_same_v<decltype(ShaderConstantSet::used), unsigned char>);

int nuke_shader_constant_set_data_header_regression()
{
    ShaderConstantSet data{};
    data.used = 1;
    return data.used == 1 ? 0 : 1;
}
