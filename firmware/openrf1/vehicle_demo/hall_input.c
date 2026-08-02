#include "hall_input.h"

#include "demo_config.h"

static uint8_t normalize_level(uint8_t level) {
    return level != 0u ? 1u : 0u;
}

void demo_hall_input_init(DemoHallInput *input, uint8_t initial_level) {
    uint8_t level;
    if (input == 0) {
        return;
    }
    level = normalize_level(initial_level);
    input->raw_level = level;
    input->debounced_level = level;
    input->candidate_level = level;
    input->candidate_count = 0u;
    input->candidate_started_ms = 0u;
    input->baseline_level = level;
    input->baseline_candidate_level = level;
    input->baseline_candidate_count = 1u;
    input->baseline_ready = 0u;
    input->landmark_active = 0u;
    input->event_pending = 0u;
    input->landmark_count = 0u;
    input->last_landmark_timestamp_ms = 0u;
}

void demo_hall_input_update(DemoHallInput *input, uint8_t raw_level, uint32_t now_ms) {
    uint8_t level;
    if (input == 0) {
        return;
    }
    level = normalize_level(raw_level);
    input->raw_level = level;

    if (input->baseline_ready == 0u) {
        if (level != input->baseline_candidate_level) {
            input->baseline_candidate_level = level;
            input->baseline_candidate_count = 1u;
        } else if (input->baseline_candidate_count < OPENRF1_DEMO_HALL_BASELINE_SAMPLES) {
            ++input->baseline_candidate_count;
        }
        if (input->baseline_candidate_count >= OPENRF1_DEMO_HALL_BASELINE_SAMPLES) {
            input->baseline_level = level;
            input->debounced_level = level;
            input->candidate_level = level;
            input->candidate_count = 0u;
            input->baseline_ready = 1u;
        }
        return;
    }

    if (level == input->debounced_level) {
        input->candidate_level = level;
        input->candidate_count = 0u;
        return;
    }
    if (level != input->candidate_level) {
        input->candidate_level = level;
        input->candidate_count = 1u;
        input->candidate_started_ms = now_ms;
        return;
    }
    if (input->candidate_count < OPENRF1_DEMO_HALL_DEBOUNCE_SAMPLES) {
        ++input->candidate_count;
    }
    if (input->candidate_count >= OPENRF1_DEMO_HALL_DEBOUNCE_SAMPLES) {
        input->debounced_level = level;
        input->candidate_level = level;
        input->candidate_count = 0u;
        if (level == input->baseline_level) {
            input->landmark_active = 0u;
        } else if (input->landmark_active == 0u) {
            input->landmark_active = 1u;
            ++input->landmark_count;
            input->last_landmark_timestamp_ms = input->candidate_started_ms;
            input->event_pending = 1u;
        }
    }
}

void demo_hall_input_clear_pending_event(DemoHallInput *input) {
    if (input != 0) {
        input->event_pending = 0u;
    }
}
