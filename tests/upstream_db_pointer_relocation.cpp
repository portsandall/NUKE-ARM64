#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <database/db_stream_load.h>
#include <database/db_stream_pointer_relocation.h>
#include <type_traits>

using PointerConversionSignature = void (*)(void *);
using AliasConversionSignature = void (*)(void *);
static_assert(
    std::is_same<decltype(&DB_ConvertOffsetToPointer), PointerConversionSignature>::value,
    "DB_ConvertOffsetToPointer must accept the address of a native pointer slot");
static_assert(
    std::is_same<decltype(&DB_ConvertOffsetToAlias), AliasConversionSignature>::value,
    "DB_ConvertOffsetToAlias must accept the address of a native pointer slot");

int main()
{
    if (DB_NativePointerSlotSize() != static_cast<int>(sizeof(void *)))
        return 6;
    if (DB_NativePointerSlotAlignmentMask() != static_cast<int>(alignof(void *) - 1))
        return 7;

    alignas(void *) unsigned char reservationStorage[32] = {};
    const std::uintptr_t unalignedAddress =
        reinterpret_cast<std::uintptr_t>(reservationStorage + 1);
    const std::uintptr_t alignmentMask =
        static_cast<std::uintptr_t>(DB_NativePointerSlotAlignmentMask());
    const std::uintptr_t alignedAddress =
        (unalignedAddress + alignmentMask) & ~alignmentMask;
    auto *reservedSlot = reinterpret_cast<unsigned char *>(alignedAddress);
    if (reinterpret_cast<std::uintptr_t>(reservedSlot) % alignof(void *) != 0)
        return 8;
    if (DB_NativePointerSlotSize() != sizeof(void *))
        return 9;
    if (reservedSlot + DB_NativePointerSlotSize() > reservationStorage + sizeof(reservationStorage))
        return 10;

    alignas(void *) unsigned char slot[sizeof(void *)] = {};
    const std::uint32_t serializedOffset = 0x12345678u;
    std::memcpy(slot, &serializedOffset, sizeof(serializedOffset));

    if (DB_ReadSerializedPointerOffset32(slot) != serializedOffset)
        return 1;

    alignas(16) unsigned char targetStorage[32] = {};
    void *resolvedPointer = static_cast<void *>(targetStorage + 3);

    if constexpr (sizeof(void *) > sizeof(std::uint32_t))
    {
        const std::uintptr_t address = reinterpret_cast<std::uintptr_t>(resolvedPointer);
        if ((address >> 32) == 0)
            return 2;
    }

    DB_WriteNativePointerSlot(slot, resolvedPointer);

    void *recoveredPointer = nullptr;
    std::memcpy(&recoveredPointer, slot, sizeof(recoveredPointer));
    if (recoveredPointer != resolvedPointer)
        return 3;

    alignas(void *) unsigned char aliasSlot[sizeof(void *)] = {};
    DB_WriteNativePointerSlot(aliasSlot, resolvedPointer);
    if (DB_ReadNativePointerSlot(aliasSlot) != resolvedPointer)
        return 5;

    if constexpr (sizeof(void *) == 8)
    {
        std::uint32_t highWord = 0;
        std::memcpy(&highWord, slot + sizeof(std::uint32_t), sizeof(highWord));
        const std::uint32_t expectedHighWord = static_cast<std::uint32_t>(
            reinterpret_cast<std::uintptr_t>(resolvedPointer) >> 32);
        if (highWord != expectedHighWord)
            return 4;
    }


    struct TestBlock {
        unsigned char *data;
        unsigned int size;
    };
    std::array<std::array<unsigned char, 16>, 7> blockStorage{};
    std::array<TestBlock, 7> blocks{};
    for (std::size_t i = 0; i < blocks.size(); ++i) {
        blocks[i] = {
            blockStorage[i].data(),
            static_cast<unsigned int>(blockStorage[i].size())
        };
    }

    if (DB_ResolveStreamOffset32(1u, blocks.data(), blocks.size(), 1u) !=
        blockStorage[0].data())
        return 11;
    if (DB_ResolveStreamOffset32(2u, blocks.data(), blocks.size(), 1u) !=
        &blockStorage[0][1])
        return 12;
    constexpr std::uint32_t blockOneStart = (1u << 29) + 1u;
    if (DB_ResolveStreamOffset32(blockOneStart, blocks.data(), blocks.size(), 1u) !=
        blockStorage[1].data())
        return 13;
    constexpr std::uint32_t blockSixOffsetFour = (6u << 29) + 5u;
    if (DB_ResolveStreamOffset32(blockSixOffsetFour, blocks.data(), blocks.size(), 1u) !=
        &blockStorage[6][4])
        return 14;

    if (DB_ResolveStreamOffset32(16u, blocks.data(), blocks.size(), 1u) !=
        &blockStorage[0][15])
        return 15;
    if (DB_ResolveStreamOffset32(16u, blocks.data(), blocks.size(), 2u) != nullptr)
        return 16;
    if (DB_ResolveStreamOffset32(17u, blocks.data(), blocks.size(), 1u) != nullptr)
        return 17;
    if (DB_ResolveStreamOffset32(9u, blocks.data(), blocks.size(), sizeof(void *)) !=
        &blockStorage[0][8])
        return 18;
    if (DB_ResolveStreamOffset32(10u, blocks.data(), blocks.size(), sizeof(void *)) != nullptr)
        return 19;
    if (DB_ResolveStreamOffset32(0u, blocks.data(), blocks.size(), 1u) != nullptr)
        return 20;
    if (DB_ResolveStreamOffset32(0xFFFFFFFEu, blocks.data(), blocks.size(), 1u) != nullptr)
        return 21;
    if (DB_ResolveStreamOffset32(0xFFFFFFFFu, blocks.data(), blocks.size(), 1u) != nullptr)
        return 22;
    constexpr std::uint32_t blockSevenStart = (7u << 29) + 1u;
    if (DB_ResolveStreamOffset32(blockSevenStart, blocks.data(), blocks.size(), 1u) != nullptr)
        return 23;

    return 0;
}
