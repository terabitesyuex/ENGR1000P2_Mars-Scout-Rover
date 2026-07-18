#pragma once

#include <stdint.h>

typedef enum {
    GROUND_SENSORS_RESULT_OK = 0,
    GROUND_SENSORS_RESULT_INVALID_ARGUMENT,
    GROUND_SENSORS_RESULT_INVALID_LEVEL,
    GROUND_SENSORS_RESULT_INVALID_DEBOUNCE_THRESHOLD,
    GROUND_SENSORS_RESULT_DUPLICATE_GPIO_ASSIGNMENT,
    GROUND_SENSORS_RESULT_UNSUPPORTED_GPIO_MAPPING,
    GROUND_SENSORS_RESULT_SCHEDULER_INVARIANT
} GroundSensorsResultCode;

typedef struct {
    uint8_t raw_level;
    uint8_t debounced_level;
    uint8_t candidate_level;
    uint8_t candidate_count;
    uint8_t debounce_samples;
} GroundSensorDebounceState;

typedef struct {
    uint8_t left_tcrt5000;
    uint8_t right_tcrt5000;
    uint8_t hall_sensor;
} GroundSensorsRawLevels;

typedef struct {
    GroundSensorDebounceState left_tcrt5000;
    GroundSensorDebounceState right_tcrt5000;
    GroundSensorDebounceState hall_sensor;
} GroundSensorsState;

GroundSensorsResultCode ground_sensors_validate_static_config(uint8_t debounce_samples);
GroundSensorsResultCode ground_sensor_debounce_init(
    GroundSensorDebounceState *state,
    uint8_t initial_level,
    uint8_t debounce_samples
);
GroundSensorsResultCode ground_sensor_debounce_update(GroundSensorDebounceState *state, uint8_t raw_level);
GroundSensorsResultCode ground_sensors_init(
    GroundSensorsState *state,
    const GroundSensorsRawLevels *initial_levels,
    uint8_t debounce_samples
);
GroundSensorsResultCode ground_sensors_update_sample(
    GroundSensorsState *state,
    const GroundSensorsRawLevels *sample
);
const char *ground_sensors_result_code_to_text(GroundSensorsResultCode code);
