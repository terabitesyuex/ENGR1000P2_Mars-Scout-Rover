#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef void (*OpenRf1TaskCallback)(void *context, uint32_t now_ms);

typedef struct {
    OpenRf1TaskCallback callback;
    void *context;
    uint32_t period_ms;
    uint32_t next_run_ms;
    uint32_t run_count;
    uint8_t enabled;
} OpenRf1Task;

void openrf1_task_init(
    OpenRf1Task *task,
    OpenRf1TaskCallback callback,
    void *context,
    uint32_t period_ms,
    uint32_t first_run_ms,
    uint8_t enabled
);
bool openrf1_task_due(const OpenRf1Task *task, uint32_t now_ms);
bool openrf1_task_service(OpenRf1Task *task, uint32_t now_ms);
void openrf1_scheduler_service(OpenRf1Task *tasks, size_t task_count, uint32_t now_ms);
