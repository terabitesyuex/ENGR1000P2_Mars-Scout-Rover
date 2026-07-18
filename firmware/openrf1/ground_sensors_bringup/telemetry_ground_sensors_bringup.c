#include "telemetry_ground_sensors_bringup.h"

#include <stdio.h>

#include "board_config.h"

static GroundSensorsTelemetryStatus map_snprintf_result(int written, size_t buffer_size) {
    if (written < 0) {
        return GROUND_SENSORS_TELEMETRY_INVALID_ARGUMENT;
    }
    return (size_t)written < buffer_size ? GROUND_SENSORS_TELEMETRY_OK : GROUND_SENSORS_TELEMETRY_BUFFER_TOO_SMALL;
}

GroundSensorsTelemetryStatus ground_sensors_format_identity(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms
) {
    if (buffer == 0 || buffer_size == 0u) {
        return GROUND_SENSORS_TELEMETRY_INVALID_ARGUMENT;
    }

    int written = snprintf(
        buffer,
        buffer_size,
        "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
        "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"sensor_identity\","
        "\"sensor_id\":\"%s\",\"status\":\"ok\","
        "\"payload\":{\"sensor_group\":\"%s\",\"connector\":\"%s\",\"connector_part\":\"%s\","
        "\"connector_pin_order\":[{\"pin\":1,\"signal\":\"%s\"},{\"pin\":2,\"signal\":\"%s\"},"
        "{\"pin\":3,\"signal\":\"%s\"},{\"pin\":4,\"signal\":\"%s\"},"
        "{\"pin\":5,\"signal\":\"%s\"},{\"pin\":6,\"signal\":\"%s\"}],"
        "\"sample_period_ms\":%lu,\"telemetry_period_ms\":%lu,"
        "\"debounce_samples\":%u,\"effective_debounce_ms\":%lu,"
        "\"semantic_polarity\":\"unverified\",\"gpio_mode\":\"%s\","
        "\"channels\":{\"left_tcrt5000\":{\"connector_signal\":%u,\"connector_label\":\"%s\","
        "\"mcu_pin\":\"%s\",\"supply\":\"%s\"},"
        "\"right_tcrt5000\":{\"connector_signal\":%u,\"connector_label\":\"%s\","
        "\"mcu_pin\":\"%s\",\"supply\":\"%s\"},"
        "\"hall_sensor\":{\"connector_signal\":%u,\"connector_label\":\"%s\","
        "\"mcu_pin\":\"%s\",\"module_supply\":\"%s\",\"input_protection\":\"%s\"}},"
        "\"signal_4\":{\"status\":\"unused\",\"mapping_conflict\":\"%s\"}}}\n",
        (unsigned long)sequence,
        (unsigned long)timestamp_ms,
        OPENRF1_GROUND_SENSOR_GROUP_ID,
        OPENRF1_GROUND_SENSOR_GROUP_ID,
        OPENRF1_GROUND_CONNECTOR,
        OPENRF1_GROUND_CONNECTOR_PART,
        OPENRF1_GROUND_CONNECTOR_PIN1,
        OPENRF1_GROUND_CONNECTOR_PIN2,
        OPENRF1_GROUND_CONNECTOR_PIN3,
        OPENRF1_GROUND_CONNECTOR_PIN4,
        OPENRF1_GROUND_CONNECTOR_PIN5,
        OPENRF1_GROUND_CONNECTOR_PIN6,
        (unsigned long)OPENRF1_GROUND_SAMPLE_PERIOD_MS,
        (unsigned long)OPENRF1_GROUND_TELEMETRY_PERIOD_MS,
        (unsigned int)OPENRF1_GROUND_DEBOUNCE_SAMPLES,
        (unsigned long)OPENRF1_GROUND_EFFECTIVE_DEBOUNCE_MS,
        OPENRF1_GROUND_GPIO_MODE_TEXT,
        (unsigned int)OPENRF1_GROUND_LEFT_CONNECTOR_SIGNAL,
        OPENRF1_GROUND_LEFT_CONNECTOR_LABEL,
        OPENRF1_GROUND_LEFT_PIN_TEXT,
        OPENRF1_GROUND_LEFT_SUPPLY_TEXT,
        (unsigned int)OPENRF1_GROUND_RIGHT_CONNECTOR_SIGNAL,
        OPENRF1_GROUND_RIGHT_CONNECTOR_LABEL,
        OPENRF1_GROUND_RIGHT_PIN_TEXT,
        OPENRF1_GROUND_RIGHT_SUPPLY_TEXT,
        (unsigned int)OPENRF1_GROUND_HALL_CONNECTOR_SIGNAL,
        OPENRF1_GROUND_HALL_CONNECTOR_LABEL,
        OPENRF1_GROUND_HALL_PIN_TEXT,
        OPENRF1_GROUND_HALL_MODULE_SUPPLY_TEXT,
        OPENRF1_GROUND_HALL_INPUT_PROTECTION_TEXT,
        OPENRF1_GROUND_SIGNAL4_MAPPING_CONFLICT
    );
    return map_snprintf_result(written, buffer_size);
}

GroundSensorsTelemetryStatus ground_sensors_format_sample(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    const GroundSensorsState *state
) {
    if (buffer == 0 || buffer_size == 0u || state == 0) {
        return GROUND_SENSORS_TELEMETRY_INVALID_ARGUMENT;
    }

    int written = snprintf(
        buffer,
        buffer_size,
        "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
        "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"ground_sensors\","
        "\"sensor_id\":\"%s\",\"status\":\"ok\","
        "\"payload\":{\"left_tcrt5000\":{\"raw_level\":%u,\"debounced_level\":%u},"
        "\"right_tcrt5000\":{\"raw_level\":%u,\"debounced_level\":%u},"
        "\"hall_sensor\":{\"raw_level\":%u,\"debounced_level\":%u}}}\n",
        (unsigned long)sequence,
        (unsigned long)timestamp_ms,
        OPENRF1_GROUND_SENSOR_GROUP_ID,
        (unsigned int)state->left_tcrt5000.raw_level,
        (unsigned int)state->left_tcrt5000.debounced_level,
        (unsigned int)state->right_tcrt5000.raw_level,
        (unsigned int)state->right_tcrt5000.debounced_level,
        (unsigned int)state->hall_sensor.raw_level,
        (unsigned int)state->hall_sensor.debounced_level
    );
    return map_snprintf_result(written, buffer_size);
}

GroundSensorsTelemetryStatus ground_sensors_format_error(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    GroundSensorsResultCode code,
    const char *operation
) {
    if (buffer == 0 || buffer_size == 0u || operation == 0) {
        return GROUND_SENSORS_TELEMETRY_INVALID_ARGUMENT;
    }

    int written = snprintf(
        buffer,
        buffer_size,
        "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
        "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"ground_sensors\","
        "\"sensor_id\":\"%s\",\"status\":\"error\","
        "\"payload\":{\"sensor_group\":\"%s\"},"
        "\"error\":{\"code\":\"%s\",\"operation\":\"%s\"}}\n",
        (unsigned long)sequence,
        (unsigned long)timestamp_ms,
        OPENRF1_GROUND_SENSOR_GROUP_ID,
        OPENRF1_GROUND_SENSOR_GROUP_ID,
        ground_sensors_result_code_to_text(code),
        operation
    );
    return map_snprintf_result(written, buffer_size);
}
