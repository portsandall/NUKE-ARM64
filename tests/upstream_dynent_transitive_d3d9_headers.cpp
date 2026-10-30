#include <physics/rope.h>
#include <xanim/xanim.h>
#include <universal/com_memory.h>

#include <type_traits>

static_assert(std::is_same_v<decltype(VisualRope::material), const Material *>,
              "VisualRope material must remain a Material pointer");
static_assert(std::is_same_v<decltype(VisualRope::drawSurf), GfxDrawSurf *>,
              "VisualRope drawSurf must remain a GfxDrawSurf pointer");
static_assert(std::is_same_v<decltype(rope_t::m_material), const Material *>,
              "rope_t material must remain a Material pointer");
static_assert(std::is_same_v<decltype(XSurface::vb0), IDirect3DVertexBuffer9 *>,
              "XSurface vertex buffer pointer ABI changed");
static_assert(std::is_same_v<decltype(XSurface::indexBuffer), IDirect3DIndexBuffer9 *>,
              "XSurface index buffer pointer ABI changed");
static_assert(sizeof(IDirect3DVertexBuffer9 *) == sizeof(void *),
              "D3D vertex buffer pointer must retain native pointer width");
static_assert(sizeof(IDirect3DIndexBuffer9 *) == sizeof(void *),
              "D3D index buffer pointer must retain native pointer width");
static_assert(std::is_enum_v<XAssetType>,
              "com_memory declarations must retain XAssetType");
static_assert(sizeof(XAssetHeader) > 0,
              "com_memory declarations must retain XAssetHeader");

int nuke_upstream_dynent_transitive_d3d9_probe()
{
    return 0;
}
