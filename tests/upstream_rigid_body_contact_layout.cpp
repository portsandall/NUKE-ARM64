#include <type_traits>
#include <physics/rigid_body.h>

using contact_list = phys_free_list<rigid_body_constraint_contact>;
using contact_slot = contact_list::T_internal;

static_assert(sizeof(void *) == 8, "This regression targets LP64");
static_assert(sizeof(rigid_body_constraint_contact) == 0x58,
              "rigid_body_constraint_contact LP64 layout changed");
static_assert(alignof(rigid_body_constraint_contact) == 8,
              "rigid_body_constraint_contact LP64 alignment changed");
static_assert(sizeof(contact_slot) == 0x70,
              "contact free-list wrapper LP64 size changed");
static_assert(alignof(contact_slot) == 8,
              "contact free-list wrapper LP64 alignment changed");
static_assert(contact_list::allocation_alignment == 16,
              "contact free-list allocation preserves the existing 16-byte PMM size-class policy");
static_assert(sizeof(contact_slot) % contact_list::allocation_alignment == 0,
              "contact slot size must be a multiple of its allocation alignment");
static_assert(std::is_same_v<decltype(phys_simple_link_list<contact_point_info>::m_first),
                             contact_point_info *>);
static_assert(std::is_same_v<decltype(rigid_body_pair_key::m_b1), rigid_body *>);
static_assert(std::is_same_v<decltype(rigid_body_pair_key::m_b2), rigid_body *>);

int nuke_upstream_rigid_body_contact_layout_probe()
{
    return static_cast<int>(sizeof(rigid_body_constraint_contact) +
                            sizeof(contact_slot) +
                            contact_list::allocation_alignment);
}
