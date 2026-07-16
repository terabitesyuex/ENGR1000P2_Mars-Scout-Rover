#include "digital_filter.h"

void openrf1_digital_filter_init(
    OpenRf1DigitalFilter *filter,
    uint8_t initial_raw_state,
    uint8_t stable_samples_required,
    uint32_t now_ms
) {
    if (filter == 0) {
        return;
    }
    uint8_t normalized = (uint8_t)(initial_raw_state != 0u);
    filter->raw_state = normalized;
    filter->filtered_state = normalized;
    filter->candidate_state = normalized;
    filter->stable_samples_required = stable_samples_required == 0u ? 1u : stable_samples_required;
    filter->candidate_count = 0u;
    filter->last_transition_ms = now_ms;
    filter->transition_count = 0u;
}

uint8_t openrf1_digital_filter_update(OpenRf1DigitalFilter *filter, uint8_t raw_state, uint32_t now_ms) {
    if (filter == 0) {
        return 0u;
    }
    uint8_t normalized = (uint8_t)(raw_state != 0u);
    filter->raw_state = normalized;
    if (normalized == filter->filtered_state) {
        filter->candidate_state = normalized;
        filter->candidate_count = 0u;
        return 0u;
    }
    if (normalized != filter->candidate_state) {
        filter->candidate_state = normalized;
        filter->candidate_count = 1u;
        return 0u;
    }
    if (filter->candidate_count < filter->stable_samples_required) {
        ++filter->candidate_count;
    }
    if (filter->candidate_count >= filter->stable_samples_required) {
        filter->filtered_state = normalized;
        filter->last_transition_ms = now_ms;
        ++filter->transition_count;
        filter->candidate_count = 0u;
        return 1u;
    }
    return 0u;
}
