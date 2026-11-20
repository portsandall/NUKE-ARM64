#include "nuke/physics_handle_table.h"

#include <array>
#include <cstdio>
#include <thread>
#include <unordered_set>
#include <vector>

namespace {

struct TestObject {
    int value{};
};

bool check(bool condition, const char* expression, int line)
{
    if (!condition) {
        std::fprintf(stderr, "line %d: check failed: %s\n", line, expression);
    }
    return condition;
}

#define CHECK(expression) \
    do { \
        if (!check((expression), #expression, __LINE__)) { \
            return 1; \
        } \
    } while (false)

} // namespace

int main()
{
    using Table = nuke_port::PhysicsHandleTable<TestObject>;
    using Handle = Table::Handle;

    Table table;
    TestObject shared{7};
    constexpr std::size_t kDuplicateWorkers = 8;
    std::array<Handle, kDuplicateWorkers> duplicate_handles{};
    std::vector<std::thread> workers;
    workers.reserve(kDuplicateWorkers);

    for (std::size_t i = 0; i < kDuplicateWorkers; ++i) {
        workers.emplace_back([&table, &shared, &duplicate_handles, i]() {
            duplicate_handles[i] = table.register_object(&shared);
        });
    }
    for (auto& worker : workers) {
        worker.join();
    }
    workers.clear();

    CHECK(duplicate_handles[0] > 0);
    for (const Handle handle : duplicate_handles) {
        CHECK(handle == duplicate_handles[0]);
    }
    const Handle first_handle = duplicate_handles[0];
    CHECK(table.size() == 1U);
    CHECK(table.resolve_object(first_handle) == &shared);
    CHECK(table.resolve_object(Table::kInvalidHandle) == nullptr);
    CHECK(table.resolve_object(static_cast<Handle>(-1)) == nullptr);
    CHECK(table.register_object(nullptr) == Table::kInvalidHandle);

    constexpr std::size_t kWorkers = 4;
    constexpr std::size_t kObjectsPerWorker = 64;
    constexpr std::size_t kObjectCount = kWorkers * kObjectsPerWorker;
    std::array<TestObject, kObjectCount> objects{};
    std::array<Handle, kObjectCount> handles{};

    for (std::size_t worker_index = 0; worker_index < kWorkers; ++worker_index) {
        workers.emplace_back([&table, &objects, &handles, worker_index]() {
            const std::size_t begin = worker_index * kObjectsPerWorker;
            const std::size_t end = begin + kObjectsPerWorker;
            for (std::size_t i = begin; i < end; ++i) {
                objects[i].value = static_cast<int>(i);
                handles[i] = table.register_object(&objects[i]);
            }
        });
    }
    for (auto& worker : workers) {
        worker.join();
    }

    CHECK(table.size() == kObjectCount + 1U);
    std::unordered_set<Handle> unique_handles;
    unique_handles.reserve(kObjectCount);
    for (std::size_t i = 0; i < kObjectCount; ++i) {
        CHECK(handles[i] > 0);
        CHECK(handles[i] != first_handle);
        CHECK(unique_handles.insert(handles[i]).second);
        CHECK(table.resolve_object(handles[i]) == &objects[i]);
    }

    CHECK(table.unregister_object(first_handle) == &shared);
    CHECK(table.resolve_object(first_handle) == nullptr);
    CHECK(table.unregister_object(first_handle) == nullptr);
    const Handle replacement_handle = table.register_object(&shared);
    CHECK(replacement_handle > first_handle);
    CHECK(replacement_handle != first_handle);
    CHECK(table.resolve_object(replacement_handle) == &shared);

    for (std::size_t i = 0; i < kObjectCount; ++i) {
        CHECK(table.unregister_object(handles[i]) == &objects[i]);
        CHECK(table.resolve_object(handles[i]) == nullptr);
    }
    CHECK(table.unregister_object(static_cast<Handle>(-1)) == nullptr);
    CHECK(table.unregister_object(replacement_handle) == &shared);
    CHECK(table.size() == 0U);

    return 0;
}
