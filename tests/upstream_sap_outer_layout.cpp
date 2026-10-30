#include <physics/phys_broad_phase.h>

#include <cstddef>
#include <type_traits>

using Sap = axis_aligned_sweep_and_prune;

static_assert(sizeof(void *) == 8, "This regression targets LP64");
static_assert(sizeof(Sap) == 72,
              "outer sweep-and-prune object must be 72 bytes on LP64");
static_assert(alignof(Sap) == 8,
              "outer sweep-and-prune object must retain native pointer alignment");
static_assert(sizeof(Sap::axis_element) == 32,
              "nested axis elements must retain native LP64 layout");
static_assert(sizeof(Sap::sap_node) == 208,
              "nested sweep nodes must retain native LP64 layout");
static_assert(sizeof(Sap::active_pair) == 32,
              "active pairs must retain native LP64 layout");
static_assert(std::is_same_v<decltype(Sap::m_x_list), Sap::axis_element *>);
static_assert(std::is_same_v<decltype(Sap::m_list_bpi_bpi), Sap::active_pair *>);

int nuke_upstream_sap_outer_layout_probe()
{
    return static_cast<int>(sizeof(Sap) + alignof(Sap));
}
