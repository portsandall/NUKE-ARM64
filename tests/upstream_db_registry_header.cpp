#include <cgame/cg_effects_load_obj.h>

#include <type_traits>

static_assert(sizeof(XAssetHeader) == sizeof(void *),
              "XAssetHeader must remain a native pointer-sized union");
static_assert(sizeof(FxImpactTable) == 2 * sizeof(void *),
              "FxImpactTable pointer layout changed");
static_assert(std::is_same_v<decltype(FxImpactTable::table), FxImpactEntry *>,
              "FxImpactTable must retain its impact-table pointer");
static_assert(
    std::is_same_v<decltype(DB_GetMaterialAtIndex(0)), XAssetPoolEntry<Material> *>,
    "DB_GetMaterialAtIndex must retain its material-pool pointer");
static_assert(
    std::is_same_v<decltype(DB_GetMaterialIndex(static_cast<const Material *>(nullptr))), int>,
    "DB_GetMaterialIndex must retain its const Material pointer parameter");

int nuke_upstream_db_registry_header_probe()
{
    FxImpactTable table{};
    return table.name == nullptr && table.table == nullptr ? 0 : 1;
}
