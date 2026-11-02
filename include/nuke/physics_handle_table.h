#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>
#include <mutex>
#include <unordered_map>

namespace nuke_port {

// Non-owning registry for native physics pointers represented by the engine's
// existing positive 32-bit ID fields. Zero remains the invalid/null sentinel.
// IDs are monotonic and never reused, so a stale ID cannot name a later object.
//
// The table mutex protects only the maps. Callers must hold the engine's
// physics-lifetime lock across resolve_object() and use of the returned
// pointer, and must unregister an object before destroying it.
template <typename T>
class PhysicsHandleTable final {
public:
    using Handle = std::int32_t;
    static constexpr Handle kInvalidHandle = 0;

    static_assert(sizeof(Handle) == sizeof(int),
                  "physics handles must fit the engine's 32-bit int fields");
    static_assert(sizeof(int) == 4,
                  "KisakBlack physics IDs require a 32-bit int");

    PhysicsHandleTable() = default;
    PhysicsHandleTable(const PhysicsHandleTable&) = delete;
    PhysicsHandleTable& operator=(const PhysicsHandleTable&) = delete;
    PhysicsHandleTable(PhysicsHandleTable&&) = delete;
    PhysicsHandleTable& operator=(PhysicsHandleTable&&) = delete;

    Handle register_object(T* object)
    {
        if (object == nullptr) {
            return kInvalidHandle;
        }

        std::lock_guard<std::mutex> lock(mutex_);

        const auto existing = handles_by_object_.find(object);
        if (existing != handles_by_object_.end()) {
            return existing->second;
        }

        if (next_handle_ == 0U) {
            return kInvalidHandle;
        }

        const Handle handle = static_cast<Handle>(next_handle_);
        const auto object_entry = objects_by_handle_.emplace(handle, object);
        if (!object_entry.second) {
            return kInvalidHandle;
        }

        try {
            const auto handle_entry = handles_by_object_.emplace(object, handle);
            if (!handle_entry.second) {
                objects_by_handle_.erase(object_entry.first);
                return handle_entry.first->second;
            }
        } catch (...) {
            objects_by_handle_.erase(object_entry.first);
            throw;
        }

        const auto max_handle =
            static_cast<std::uint32_t>(std::numeric_limits<Handle>::max());
        if (next_handle_ == max_handle) {
            next_handle_ = 0U;
        } else {
            ++next_handle_;
        }

        return handle;
    }

    T* resolve_object(Handle handle) const
    {
        if (handle <= kInvalidHandle) {
            return nullptr;
        }

        std::lock_guard<std::mutex> lock(mutex_);
        const auto entry = objects_by_handle_.find(handle);
        return entry == objects_by_handle_.end() ? nullptr : entry->second;
    }

    T* unregister_object(Handle handle)
    {
        if (handle <= kInvalidHandle) {
            return nullptr;
        }

        std::lock_guard<std::mutex> lock(mutex_);
        const auto entry = objects_by_handle_.find(handle);
        if (entry == objects_by_handle_.end()) {
            return nullptr;
        }

        T* const object = entry->second;
        const auto reverse_entry = handles_by_object_.find(object);
        if (reverse_entry != handles_by_object_.end() &&
            reverse_entry->second == handle) {
            handles_by_object_.erase(reverse_entry);
        }
        objects_by_handle_.erase(entry);
        return object;
    }

    std::size_t size() const
    {
        std::lock_guard<std::mutex> lock(mutex_);
        return objects_by_handle_.size();
    }

private:
    mutable std::mutex mutex_;
    std::unordered_map<Handle, T*> objects_by_handle_;
    std::unordered_map<T*, Handle> handles_by_object_;
    std::uint32_t next_handle_{1U};
};

} // namespace nuke_port
