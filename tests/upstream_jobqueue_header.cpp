#include <type_traits>
#include <tl/jobqueue/jobqueue_all.h>

using jobqueue_thread_id = decltype(tlAtomicMutex::ThreadId);
using shared_jobqueue_thread_id = decltype(tlSharedAtomicMutex::ThreadId);
using jobqueue_node = jqAtomicQueueType::NodeType;

static_assert(sizeof(void *) == 8, "This regression targets LP64");
static_assert(sizeof(jobqueue_thread_id) == 8,
              "job-queue owner thread ID must remain 64-bit");
static_assert(std::is_same_v<std::remove_volatile_t<jobqueue_thread_id>, __int64>,
              "job-queue owner thread ID must retain signed 64-bit semantics");
static_assert(sizeof(shared_jobqueue_thread_id) == 8,
              "shared job-queue owner thread ID must remain 64-bit");

static_assert(sizeof(jqBatch) == 152,
              "jqBatch LP64 layout must include all native pointers");
static_assert(alignof(jqBatch) == 8,
              "jqBatch LP64 alignment must satisfy its pointer members");
static_assert(offsetof(jqBatch, Input) == 8);
static_assert(offsetof(jqBatch, Output) == 16);
static_assert(offsetof(jqBatch, Module) == 24);
static_assert(offsetof(jqBatch, GroupID) == 32);
static_assert(offsetof(jqBatch, ConditionalAddress) == 40);
static_assert(offsetof(jqBatch, ConditionalValue) == 48);
static_assert(offsetof(jqBatch, ParamData) == 52);

static_assert(sizeof(jobqueue_node) == 160,
              "queue node size must track the LP64 batch payload");
static_assert(alignof(jobqueue_node) == 8,
              "queue node must satisfy native pointer alignment");
static_assert(sizeof(jqBatchGroup) == 8,
              "job-queue batch counters must retain their 64-bit storage");
static_assert(alignof(jqBatchGroup) == 8,
              "job-queue batch counters must remain 8-byte aligned");
static_assert(offsetof(jqBatchPool, group) % 8 == 0,
              "job-queue pool group must remain naturally aligned");

int nuke_upstream_jobqueue_header_probe()
{
    return static_cast<int>(sizeof(jobqueue_thread_id) +
                            sizeof(shared_jobqueue_thread_id) +
                            sizeof(jqBatch) +
                            sizeof(jobqueue_node) +
                            sizeof(jqBatchGroup));
}
