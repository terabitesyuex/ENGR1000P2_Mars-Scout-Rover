#include "ground_sensors.h"

#include "board_config.h"

static uint8_t normalize_level(uint8_t level) {
    return (uint8_t)(level != 0u);
}

static uint8_t level_is_valid(uint8_t level) {
    return level <= 1u ? 1u : 0u;
}

GroundSensorsResultCode ground_sensors_validate_static_config(uint8_t debounce_samples) {
    if (debounce_samples == 0u) {
        return GROUND_SENSORS_RESULT_INVALID_DEBOUNCE_THRESHOLD;
    }
    if (OPENRF1_GROUND_SAMPLE_PERIOD_MS != 5u ||
        OPENRF1_GROUND_TELEMETRY_PERIOD_MS != 50u ||
        OPENRF1_GROUND_DEBOUNCE_SAMPLES != 4u ||
        OPENRF1_GROUND_EFFECTIVE_DEBOUNCE_MS != 20u) {
        return GROUND_SENSORS_RESULT_SCHEDULER_INVARIANT;
    }
    if (OPENRF1_GROUND_SIGNAL4_USED != 0u) {
        return GROUND_SENSORS_RESULT_UNSUPPORTED_GPIO_MAPPING;
    }
    return GROUND_SENSORS_RESULT_OK;
}

GroundSensorsResultCode ground_sensor_debounce_init(
    GroundSensorDebounceState *state,
    uint8_t initial_level,
    uint8_t debounce_samples
) {
    if (state == 0) {
        return GROUND_SENSORS_RESULT_INVALID_ARGUMENT;
    }
    if (!level_is_valid(initial_level)) {
        return GROUND_SENSORS_RESULT_INVALID_LEVEL;
    }
    if (debounce_samples == 0u) {
        return GROUND_SENSORS_RESULT_INVALID_DEBOUNCE_THRESHOLD;
    }

    uint8_t normalized = normalize_level(initial_level);
    state->raw_level = normalized;
    state->debounced_level = normalized;
    state->candidate_level = normalized;
    state->candidate_count = 0u;
    state->debounce_samples = debounce_samples;
    return GROUND_SENSORS_RESULT_OK;
}

GroundSensorsResultCode ground_sensor_debounce_update(GroundSensorDebounceState *state, uint8_t raw_level) {
    if (state == 0) {
        return GROUND_SENSORS_RESULT_INVALID_ARGUMENT;
    }
    if (!level_is_valid(raw_level)) {
        return GROUND_SENSORS_RESULT_INVALID_LEVEL;
    }
    if (state->debounce_samples == 0u) {
        return GROUND_SENSORS_RESULT_INVALID_DEBOUNCE_THRESHOLD;
    }

    uint8_t normalized = normalize_level(raw_level);
    state->raw_level = normalized;
    if (normalized == state->debounced_level) {
        state->candidate_level = normalized;
        state->candidate_count = 0u;
        return GROUND_SENSORS_RESULT_OK;
    }
    if (normalized != state->candidate_level) {
        state->candidate_level = normalized;
        state->candidate_count = 1u;
        return GROUND_SENSORS_RESULT_OK;
    }
    if (state->candidate_count < state->debounce_samples) {
        ++state->candidate_count;
    }
    if (state->candidate_count >= state->debounce_samples) {
        state->debounced_level = normalized;
        state->candidate_level = normalized;
        state->candidate_count = 0u;
    }
    return GROUND_SENSORS_RESULT_OK;
}

GroundSensorsResultCode ground_sensors_init(
    GroundSensorsState *state,
    const GroundSensorsRawLevels *initial_levels,
    uint8_t debounce_samples
) {
    if (state == 0 || initial_levels == 0) {
        return GROUND_SENSORS_RESULT_INVALID_ARGUMENT;
    }
    GroundSensorsResultCode status = ground_sensors_validate_static_config(debounce_samples);
    if (status != GROUND_SENSORS_RESULT_OK) {
        return status;
    }
    status = ground_sensor_debounce_init(&state->left_tcrt5000, initial_levels->left_tcrt5000, debounce_samples);
    if (status != GROUND_SENSORS_RESULT_OK) {
        return status;
    }
    status = ground_sensor_debounce_init(&state->right_tcrt5000, initial_levels->right_tcrt5000, debounce_samples);
    if (status != GROUND_SENSORS_RESULT_OK) {
        return status;
    }
    return ground_sensor_debounce_init(&state->hall_sensor, initial_levels->hall_sensor, debounce_samples);
}

GroundSensorsResultCode ground_sensors_update_sample(
    GroundSensorsState *state,
    const GroundSensorsRawLevels *sample
) {
    if (state == 0 || sample == 0) {
        return GROUND_SENSORS_RESULT_INVALID_ARGUMENT;
    }
    GroundSensorsResultCode status = ground_sensor_debounce_update(&state->left_tcrt5000, sample->left_tcrt5000);
    if (status != GROUND_SENSORS_RESULT_OK) {
        return status;
    }
    status = ground_sensor_debounce_update(&state->right_tcrt5000, sample->right_tcrt5000);
    if (status != GROUND_SENSORS_RESULT_OK) {
        return status;
    }
    return ground_sensor_debounce_update(&state->hall_sensor, sample->hall_sensor);
}

const char *ground_sensors_result_code_to_text(GroundSensorsResultCode code) {
    switch (code) {
        case GROUND_SENSORS_RESULT_OK:
            return "ok";
        case GROUND_SENSORS_RESULT_INVALID_ARGUMENT:
            return "invalid_argument";
        case GROUND_SENSORS_RESULT_INVALID_LEVEL:
            return "invalid_level";
        case GROUND_SENSORS_RESULT_INVALID_DEBOUNCE_THRESHOLD:
            return "invalid_debounce_threshold";
        case GROUND_SENSORS_RESULT_DUPLICATE_GPIO_ASSIGNMENT:
            return "duplicate_gpio_assignment";
        case GROUND_SENSORS_RESULT_UNSUPPORTED_GPIO_MAPPING:
            return "unsupported_gpio_mapping";
        case GROUND_SENSORS_RESULT_SCHEDULER_INVARIANT:
        default:
            return "scheduler_invariant";
    }
}
