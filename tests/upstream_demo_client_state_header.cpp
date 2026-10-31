#include <demo/demo_common.h>

#include <type_traits>

static_assert(sizeof(clientState_s) == 0xD0);

using demo_client_array_t =
    std::remove_reference_t<decltype(((demoMain *)nullptr)->client)>;

static_assert(std::is_array_v<demo_client_array_t>);
static_assert(std::extent_v<demo_client_array_t> == 32);
static_assert(std::is_same_v<std::remove_extent_t<demo_client_array_t>, clientState_s>);

int main()
{
    return 0;
}
