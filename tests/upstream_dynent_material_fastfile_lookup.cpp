#include <database/db_material_fastfile.h>

#include <cstddef>

struct Material
{
    int marker;
};

static Material registeredMaterial{0x4e554b45};
static XAssetType capturedType = ASSET_TYPE_COUNT;
static char *capturedName = nullptr;
static bool capturedErrorIfMissing = false;
static int capturedWaitTime = 0;

XAssetHeader __cdecl DB_FindXAssetHeader(
    XAssetType type,
    char *name,
    bool errorIfMissing,
    int waitTime)
{
    capturedType = type;
    capturedName = name;
    capturedErrorIfMissing = errorIfMissing;
    capturedWaitTime = waitTime;
    return XAssetHeader(&registeredMaterial);
}

int main()
{
    static_assert(sizeof(XAssetHeader) == sizeof(void *));
    constexpr const char requestedName[] = "rope_constraint_material";

    Material *material = DB_FindFastFileMaterial(requestedName);

    return material == &registeredMaterial
            && capturedType == ASSET_TYPE_MATERIAL
            && capturedName == const_cast<char *>(requestedName)
            && capturedErrorIfMissing
            && capturedWaitTime == -1
        ? 0
        : 1;
}
