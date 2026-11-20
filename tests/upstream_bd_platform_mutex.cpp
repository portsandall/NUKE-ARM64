#include <DemonWare/bdPlatform/bdPlatformThread/bdPlatformMutex.h>

int main()
{
    MutexHandle handle = bdPlatformMutex::createMutex();
    if (handle == nullptr)
        return 1;

    bdPlatformMutex::lock(handle);
    bdPlatformMutex::lock(handle);
    bdPlatformMutex::unlock(handle);
    bdPlatformMutex::unlock(handle);
    bdPlatformMutex::destroy(handle);

    return handle == nullptr ? 0 : 2;
}
