#include <type_traits>
#include <tl/jobqueue/jobqueue_all.h>

using jobqueue_thread_id = decltype(tlAtomicMutex::ThreadId);
using shared_jobqueue_thread_id = decltype(tlSharedAtomicMutex::ThreadId);

static_assert(sizeof(jobqueue_thread_id) == 8,
              "job-queue owner thread ID must remain 64-bit");
static_assert(std::is_same_v<std::remove_volatile_t<jobqueue_thread_id>, __int64>,
              "job-queue owner thread ID must retain signed 64-bit semantics");
static_assert(sizeof(shared_jobqueue_thread_id) == 8,
              "shared job-queue owner thread ID must remain 64-bit");
static_assert(sizeof(jqBatchGroup) == 8,
              "job-queue batch counters must retain their 64-bit storage");
static_assert(alignof(jqBatchGroup) == 8,
              "job-queue batch counters must remain 8-byte aligned");

int nuke_upstream_jobqueue_header_probe()
{
    return static_cast<int>(sizeof(jobqueue_thread_id) +
                            sizeof(shared_jobqueue_thread_id) +
                            sizeof(jqBatchGroup));
}
