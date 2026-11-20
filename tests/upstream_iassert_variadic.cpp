#include <universal/assertive.h>

// This is a compile-only regression for both historical call signatures.
// The four-argument form is used by the AVL tree in phys_local.h.
void nuke_upstream_iassert_variadic_probe(bool predicate) {
    iassert(predicate);
    iassert(predicate, "phys_avl_tree.h", 103, "cur_item + 1 - the_stack < 32");
}
