#include <cstdint>
#include <cstring>
#include <database/db_stream_load.h>
#include <database/db_stream_pointer_relocation.h>
#include <type_traits>

using PointerConversionSignature = void (*)(void *);
static_assert(
    std::is_same<decltype(&DB_ConvertOffsetToPointer), PointerConversionSignature>::value,
    "DB_ConvertOffsetToPointer must accept the address of a native pointer slot");

int main()
{
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

    if constexpr (sizeof(void *) == 8)
    {
        std::uint32_t highWord = 0;
        std::memcpy(&highWord, slot + sizeof(std::uint32_t), sizeof(highWord));
        const std::uint32_t expectedHighWord = static_cast<std::uint32_t>(
            reinterpret_cast<std::uintptr_t>(resolvedPointer) >> 32);
        if (highWord != expectedHighWord)
            return 4;
    }

    return 0;
}
