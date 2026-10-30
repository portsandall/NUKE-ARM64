#include <DemonWare/bdCore/bdContainers/bdBitBuffer.h>
#include <DemonWare/bdCore/bdContainers/bdByteBuffer.h>
#include <universal/dvar.h>
#include <universal/q_shared.h>

static_assert(sizeof(__int32) == 4, "__int32 must remain 32-bit");
static_assert(sizeof(__int64) == 8, "__int64 must remain 64-bit");
static_assert(sizeof(unsigned __int8) == 1, "unsigned __int8 must remain 8-bit");
static_assert(sizeof(unsigned __int64) == 8, "unsigned __int64 must remain 64-bit");

struct __declspec(align(16)) NukeMsAlignmentProbe {
    unsigned char value;
};
static_assert(alignof(NukeMsAlignmentProbe) == 16,
              "__declspec(align(16)) must be honored");

static_assert(sizeof(DvarValue) == 16, "DvarValue layout changed");
static_assert(sizeof(DvarLimits) == 16, "DvarLimits layout changed");
static_assert(alignof(dvar_s) == 8, "dvar_s must remain 8-byte aligned");
static_assert(alignof(bdBitBuffer) >= 4, "bdBitBuffer alignment regressed");
static_assert(alignof(bdByteBuffer) >= 2, "bdByteBuffer alignment regressed");

// Include the native-pointer physics-node layout regression in the existing
// host and Android MSVC-extension compile probe.
#include "upstream_chull_layout.cpp"
