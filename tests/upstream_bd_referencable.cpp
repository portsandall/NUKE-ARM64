#include <DemonWare/bdCore/bdReference/bdReferencable.h>

#include <new>

struct TestReference : bdReferencable {
    bool* destroyed;

    explicit TestReference(bool* destroyed_flag) : destroyed(destroyed_flag) {}
    ~TestReference() override { *destroyed = true; }
};

int main() {
    alignas(TestReference) unsigned char storage[sizeof(TestReference)];
    bool destroyed = false;
    TestReference* object = new (storage) TestReference(&destroyed);
    object->m_refCount = 0u;

    bdReference<TestReference> first;
    bdReference<TestReference> second;
    first.m_ptr = nullptr;
    second.m_ptr = nullptr;

    first = object;
    if (object->m_refCount != 1u) {
        return 1;
    }

    second = first;
    if (object->m_refCount != 2u) {
        return 2;
    }

    first = static_cast<TestReference*>(nullptr);
    if (object->m_refCount != 1u) {
        return 3;
    }

    second = static_cast<TestReference*>(nullptr);
    return destroyed ? 0 : 4;
}
