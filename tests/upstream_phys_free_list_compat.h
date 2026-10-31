#pragma once

#include <cstring>
#include <mutex>

namespace nuke_port {

// AArch64 cannot pack a full pointer and a 32-bit ABA tag into the original
// 64-bit IA-32 freelist word. Protect the pointer/tag pair while retaining
// the native pointer in each free slot.
inline std::mutex &phys_free_list_mutex()
{
    static std::mutex mutex;
    return mutex;
}

inline void phys_free_list_push(void **head, unsigned int *tag, void *slot)
{
    if (!head || !tag || !slot)
        return;

    std::lock_guard<std::mutex> lock(phys_free_list_mutex());
    std::memcpy(slot, head, sizeof(*head));
    *head = slot;
    ++*tag;
}

inline void *phys_free_list_pop(void **head, unsigned int *tag)
{
    if (!head || !tag)
        return nullptr;

    std::lock_guard<std::mutex> lock(phys_free_list_mutex());
    void *slot = *head;
    if (!slot)
        return nullptr;

    void *next = nullptr;
    std::memcpy(&next, slot, sizeof(next));
    *head = next;
    ++*tag;
    return slot;
}

} // namespace nuke_port
