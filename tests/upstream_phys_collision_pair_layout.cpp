#include <type_traits>
#include <physics/phys_local.h>
#include "upstream-phys-collision-pair-layout-fixture.hpp"

static_assert(sizeof(void *) == 8, "This regression targets LP64");
static_assert(sizeof(phys_collision_pair) == 40,
              "phys_collision_pair LP64 layout changed");
static_assert(alignof(phys_collision_pair) == 8,
              "phys_collision_pair LP64 alignment changed");
static_assert(std::is_base_of_v<phys_link_list_base<phys_collision_pair>,
                                phys_collision_pair>);
static_assert(std::is_same_v<decltype(phys_collision_pair::m_bpi1),
                             broad_phase_info *>);
static_assert(std::is_same_v<decltype(phys_collision_pair::m_bpi2),
                             broad_phase_info *>);
static_assert(std::is_same_v<decltype(phys_collision_pair::m_gjk_ci),
                             phys_gjk_cache_info *>);

int nuke_upstream_phys_collision_pair_layout_probe()
{
    return static_cast<int>(sizeof(phys_collision_pair));
}
