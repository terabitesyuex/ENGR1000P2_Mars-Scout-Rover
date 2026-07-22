#include "telemetry_hcsr04_bringup.h"

#include <stdio.h>

#include "board_config.h"

static Hcsr04BringupTelemetryStatus map_snprintf_result(int written, size_t buffer_size) {
    if (written < 0) {
        return HCSR04_BRINGUP_TELEMETRY_INVALID_ARGUMENT;
    }
    return (size_t)written < buffer_size ? HCSR04_BRINGUP_TELEMETRY_OK : HCSR04_BRINGUP_TELEMETRY_BUFFER_TOO_SMALL;
}

Hcsr04BringupTelemetryStatus hcsr04_bringup_format_identity(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms
) {
    if (buffer == 0 || buffer_size == 0u) {
        return HCSR04_BRINGUP_TELEMETRY_INVALID_ARGUMENT;
    }

    int written = snprintf(
        buffer,
        buffer_size,
        "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
        "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"sensor_identity\","
        "\"sensor_id\":\"%s\",\"status\":\"ok\","
        "\"payload\":{\"sensor\":\"%s\",\"connector\":\"%s\","
        "\"trigger_pin\":\"%s\",\"echo_pin\":\"%s\","
        "\"timer\":\"%s\",\"timer_tick_hz\":%lu,"
        "\"trigger_pulse_us\":%u,\"echo_timeout_us\":%lu,\"measurement_period_ms\":%lu,"
        "\"distance_unit\":\"mm\",\"distance_model\":\"%s\"}}\n",
        (unsigned long)sequence,
        (unsigned long)timestamp_ms,
        OPENRF1_HCSR04_SENSOR_ID,
        OPENRF1_HCSR04_SENSOR_NAME,
        OPENRF1_HCSR04_CONNECTOR,
        OPENRF1_HCSR04_TRIGGER_PIN_TEXT,
        OPENRF1_HCSR04_ECHO_PIN_TEXT,
        OPENRF1_HCSR04_TIMER_TEXT,
        (unsigned long)OPENRF1_HCSR04_TIMER_TICK_HZ,
        (unsigned int)OPENRF1_HCSR04_TRIGGER_PULSE_US,
        (unsigned long)OPENRF1_HCSR04_ECHO_TIMEOUT_US,
        (unsigned long)OPENRF1_HCSR04_MEASUREMENT_PERIOD_MS,
        OPENRF1_HCSR04_DISTANCE_MODEL
    );
    return map_snprintf_result(written, buffer_size);
}

Hcsr04BringupTelemetryStatus hcsr04_bringup_format_measurement(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    const Hcsr04MeasurementResult *measurement
) {
    if (buffer == 0 || buffer_size == 0u || measurement == 0) {
        return HCSR04_BRINGUP_TELEMETRY_INVALID_ARGUMENT;
    }

    int written = snprintf(
        buffer,
        buffer_size,
        "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
        "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"ultrasonic\","
        "\"sensor_id\":\"%s\",\"status\":\"ok\","
        "\"payload\":{\"echo_pulse_us\":%lu,\"distance_mm\":%u,"
        "\"distance_model\":\"%s\"}}\n",
        (unsigned long)sequence,
        (unsigned long)timestamp_ms,
        OPENRF1_HCSR04_SENSOR_ID,
        (unsigned long)measurement->echo_pulse_us,
        (unsigned int)measurement->distance_mm,
        OPENRF1_HCSR04_DISTANCE_MODEL
    );
    return map_snprintf_result(written, buffer_size);
}

Hcsr04BringupTelemetryStatus hcsr04_bringup_format_error(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    Hcsr04ResultCode code
) {
    if (buffer == 0 || buffer_size == 0u) {
        return HCSR04_BRINGUP_TELEMETRY_INVALID_ARGUMENT;
    }

    int written = snprintf(
        buffer,
        buffer_size,
        "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
        "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"ultrasonic\","
        "\"sensor_id\":\"%s\",\"status\":\"error\","
        "\"payload\":{\"echo_pulse_us\":null,\"distance_mm\":null,"
        "\"distance_model\":\"%s\"},"
        "\"error\":{\"code\":\"%s\",\"operation\":\"%s\",\"timeout_us\":%lu}}\n",
        (unsigned long)sequence,
        (unsigned long)timestamp_ms,
        OPENRF1_HCSR04_SENSOR_ID,
        OPENRF1_HCSR04_DISTANCE_MODEL,
        hcsr04_result_code_to_text(code),
        hcsr04_result_operation_to_text(code),
        (unsigned long)OPENRF1_HCSR04_ECHO_TIMEOUT_US
    );
    return map_snprintf_result(written, buffer_size);
}
