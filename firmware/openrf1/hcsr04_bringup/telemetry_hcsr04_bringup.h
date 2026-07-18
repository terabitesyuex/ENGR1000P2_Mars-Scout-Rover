#pragma once

#include <stddef.h>
#include <stdint.h>

#include "hcsr04.h"

typedef enum {
    HCSR04_BRINGUP_TELEMETRY_OK = 0,
    HCSR04_BRINGUP_TELEMETRY_BUFFER_TOO_SMALL,
    HCSR04_BRINGUP_TELEMETRY_INVALID_ARGUMENT
} Hcsr04BringupTelemetryStatus;

Hcsr04BringupTelemetryStatus hcsr04_bringup_format_identity(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms
);
Hcsr04BringupTelemetryStatus hcsr04_bringup_format_measurement(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    const Hcsr04MeasurementResult *measurement
);
Hcsr04BringupTelemetryStatus hcsr04_bringup_format_error(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    Hcsr04ResultCode code
);
