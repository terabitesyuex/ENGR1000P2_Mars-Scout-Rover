#pragma once

#include <stdint.h>

typedef struct {
    uint8_t raw_level;
    uint8_t debounced_level;
    uint8_t candidate_level;
    uint8_t candidate_count;
    uint32_t candidate_started_ms;
    uint8_t baseline_level;
    uint8_t baseline_candidate_level;
    uint8_t baseline_candidate_count;
    uint8_t baseline_ready;
    uint8_t landmark_active;
    uint8_t event_pending;
    uint32_t landmark_count;
    uint32_t last_landmark_timestamp_ms;
} DemoHallInput;

void demo_hall_input_init(DemoHallInput *input, uint8_t initial_level);
void demo_hall_input_update(DemoHallInput *input, uint8_t raw_level, uint32_t now_ms);
void demo_hall_input_clear_pending_event(DemoHallInput *input);
