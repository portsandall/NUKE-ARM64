#pragma once

#include <cstddef>
#include <cstdint>
#include <type_traits>

namespace nuke::db {

// Fixed 32-bit FastFile record. Pointer-valued members are opaque DB tokens,
// not native addresses. Keep this separate from the LP64 runtime object until
// the loader has an explicit token-resolution/conversion path.
struct SndDriverGlobalsRecord32 {
    std::uint32_t name_token;
    std::uint32_t group_count;
    std::uint32_t groups_token;
    std::uint32_t curve_count;
    std::uint32_t curves_token;
    std::uint32_t pan_count;
    std::uint32_t pans_token;
    std::uint32_t snapshot_group_count;
    std::uint32_t snapshot_groups_token;
    std::uint32_t context_count;
    std::uint32_t contexts_token;
    std::uint32_t master_count;
    std::uint32_t masters_token;
};

static_assert(std::is_standard_layout<SndDriverGlobalsRecord32>::value,
              "SndDriverGlobals disk record must remain standard-layout");
static_assert(std::is_trivially_copyable<SndDriverGlobalsRecord32>::value,
              "SndDriverGlobals disk record must remain byte-copyable");
static_assert(sizeof(SndDriverGlobalsRecord32) == 52,
              "SndDriverGlobals FastFile record is exactly 52 bytes");
static_assert(alignof(SndDriverGlobalsRecord32) == alignof(std::uint32_t),
              "SndDriverGlobals disk record uses 32-bit alignment");

static_assert(offsetof(SndDriverGlobalsRecord32, name_token) == 0);
static_assert(offsetof(SndDriverGlobalsRecord32, group_count) == 4);
static_assert(offsetof(SndDriverGlobalsRecord32, groups_token) == 8);
static_assert(offsetof(SndDriverGlobalsRecord32, curve_count) == 12);
static_assert(offsetof(SndDriverGlobalsRecord32, curves_token) == 16);
static_assert(offsetof(SndDriverGlobalsRecord32, pan_count) == 20);
static_assert(offsetof(SndDriverGlobalsRecord32, pans_token) == 24);
static_assert(offsetof(SndDriverGlobalsRecord32, snapshot_group_count) == 28);
static_assert(offsetof(SndDriverGlobalsRecord32, snapshot_groups_token) == 32);
static_assert(offsetof(SndDriverGlobalsRecord32, context_count) == 36);
static_assert(offsetof(SndDriverGlobalsRecord32, contexts_token) == 40);
static_assert(offsetof(SndDriverGlobalsRecord32, master_count) == 44);
static_assert(offsetof(SndDriverGlobalsRecord32, masters_token) == 48);

} // namespace nuke::db
