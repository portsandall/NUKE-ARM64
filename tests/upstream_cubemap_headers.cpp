#include <CubeMapGenLib/CBBoxInt32.h>

static_assert(sizeof(int32) == 4, "CubeMapGen int32 must remain 32-bit");
static_assert(sizeof(uint64) == 8, "CubeMapGen uint64 must remain 64-bit");
static_assert(sizeof(CBBoxInt32) == 24, "CubeMapGen bounding-box layout changed");

int main()
{
    CBBoxInt32 box;
    box.m_minCoord[0] = 0;
    box.m_maxCoord[0] = 1;
    return 0;
}
