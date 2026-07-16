#pragma once

#include <stdint.h>

typedef struct {
    uint8_t raw_state;
    uint8_t filtered_state;
    uint8_t candidate_state;
    uint8_t stable_samples_required;
    uint8_t candidate_count;
    uint32_t last_transition_ms;
    uint32_t transition_count;
} OpenRf1DigitalFilter;

void openrf1_digital_filter_init(
    OpenRf1DigitalFilter *filter,
    uint8_t initial_raw_state,
    uint8_t stable_samples_required,
    uint32_t now_ms
);
uint8_t openrf1_digital_filter_update(OpenRf1DigitalFilter *filter, uint8_t raw_state, uint32_t now_ms);
