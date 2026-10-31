#include <universal/com_stringtable.h>

#include <cstddef>
#include <type_traits>

static_assert(sizeof(void *) == 8, "Android target must use 64-bit pointers");
static_assert(sizeof(int) == 4, "engine int fields must remain 32-bit");
static_assert(std::is_standard_layout_v<StringTableCell>);
static_assert(std::is_standard_layout_v<StringTable>);
static_assert(sizeof(StringTableCell) == 16);
static_assert(offsetof(StringTableCell, string) == 0);
static_assert(offsetof(StringTableCell, hash) == 8);
static_assert(sizeof(StringTable) == 32);
static_assert(offsetof(StringTable, name) == 0);
static_assert(offsetof(StringTable, columnCount) == 8);
static_assert(offsetof(StringTable, rowCount) == 12);
static_assert(offsetof(StringTable, values) == 16);
static_assert(offsetof(StringTable, cellIndex) == 24);

int main()
{
    StringTable table{};
    StringTableCell cell{};
    return table.values == nullptr && cell.hash == 0 ? 0 : 1;
}
