#include "scheduler.h"

void openrf1_task_init(
    OpenRf1Task *task,
    OpenRf1TaskCallback callback,
    void *context,
    uint32_t period_ms,
    uint32_t first_run_ms,
    uint8_t enabled
) {
    if (task == 0) {
        return;
    }
    task->callback = callback;
    task->context = context;
    task->period_ms = period_ms;
    task->next_run_ms = first_run_ms;
    task->run_count = 0u;
    task->enabled = enabled;
}

bool openrf1_task_due(const OpenRf1Task *task, uint32_t now_ms) {
    if (task == 0 || task->enabled == 0u || task->callback == 0 || task->period_ms == 0u) {
        return false;
    }
    return (int32_t)(now_ms - task->next_run_ms) >= 0;
}

bool openrf1_task_service(OpenRf1Task *task, uint32_t now_ms) {
    if (!openrf1_task_due(task, now_ms)) {
        return false;
    }
    task->callback(task->context, now_ms);
    task->next_run_ms = now_ms + task->period_ms;
    ++task->run_count;
    return true;
}

void openrf1_scheduler_service(OpenRf1Task *tasks, size_t task_count, uint32_t now_ms) {
    if (tasks == 0) {
        return;
    }
    for (size_t index = 0u; index < task_count; ++index) {
        (void)openrf1_task_service(&tasks[index], now_ms);
    }
}
