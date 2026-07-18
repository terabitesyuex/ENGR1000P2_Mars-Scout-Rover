#pragma once

#include <stddef.h>
#include <stdint.h>

#include "ground_sensors.h"

typedef enum {
    GROUND_SENSORS_TELEMETRY_OK = 0,
    GROUND_SENSORS_TELEMETRY_BUFFER_TOO_SMALL,
    GROUND_SENSORS_TELEMETRY_INVALID_ARGUMENT
} GroundSensorsTelemetryStatus;

GroundSensorsTelemetryStatus ground_sensors_format_identity(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms
);
GroundSensorsTelemetryStatus ground_sensors_format_sample(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    const GroundSensorsState *state
);
GroundSensorsTelemetryStatus ground_sensors_format_error(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    GroundSensorsResultCode code,
    const char *operation
);
