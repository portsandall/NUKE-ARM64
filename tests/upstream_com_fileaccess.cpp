#include "com_fileaccess.h"
#include "assertive.h"
#include "q_shared.h"

#include <cstdarg>
#include <cstdio>
#include <cstring>

namespace
{
int assertCalls = 0;
char lastAssertion[1024] = {};
}

bool Assert_MyHandler(const char *filename, int line, int type, const char *format, ...)
{
    (void)filename;
    (void)line;
    (void)type;
    ++assertCalls;
    std::snprintf(lastAssertion, sizeof(lastAssertion), "%s", format ? format : "");
    return true;
}

char *va(const char *format, ...)
{
    static char buffer[1024];
    va_list args;
    va_start(args, format);
    std::vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    return buffer;
}

int main()
{
    // /dev/null is not a directory, so this path must fail with ENOTDIR.
    FILE *missing = FileWrapper_Open("/dev/null/NUKE-ARM64-missing", "rb");
    if (missing != nullptr)
    {
        std::fclose(missing);
        return 1;
    }
    if (assertCalls != 1)
        return 2;
    if (std::strstr(lastAssertion, "Couldn't open file:") == nullptr)
        return 3;

    FILE *existing = FileWrapper_Open("/dev/null", "rb");
    if (existing == nullptr)
        return 4;
    std::fclose(existing);
    if (assertCalls != 1)
        return 5;

    return 0;
}
