#include "upstream-auto-activate-layout-fixture.hpp"
#include <type_traits>

static_assert(sizeof(void *) == 8, "This regression targets LP64");
static_assert(std::is_polymorphic_v<phys_auto_activate_callback>);
static_assert(std::is_base_of_v<phys_auto_activate_callback, destructible_ent_aa>);
static_assert(std::is_base_of_v<phys_auto_activate_callback, dynamic_ent_aa>);

static_assert(sizeof(phys_auto_activate_callback) == 8,
              "AArch64 callback vptr must be pointer-sized");
static_assert(sizeof(destructible_ent_aa) == 24,
              "destructible_ent_aa LP64 layout changed");
static_assert(sizeof(dynamic_ent_aa) == 24,
              "dynamic_ent_aa LP64 layout changed");
static_assert(alignof(destructible_ent_aa) == 8,
              "destructible_ent_aa LP64 alignment changed");
static_assert(alignof(dynamic_ent_aa) == 8,
              "dynamic_ent_aa LP64 alignment changed");

int nuke_upstream_auto_activate_layout_probe()
{
    return static_cast<int>(sizeof(destructible_ent_aa) + sizeof(dynamic_ent_aa));
}
