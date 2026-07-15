#pragma once

#include <stddef.h>
#include <stdint.h>

#include "bh1750.h"

typedef enum {
    TELEMETRY_FORMAT_OK = 0,
    TELEMETRY_FORMAT_BUFFER_TOO_SMALL,
    TELEMETRY_FORMAT_INVALID_ARGUMENT
} TelemetryFormatStatus;

TelemetryFormatStatus telemetry_format_bh1750(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    const Bh1750Sample *sample
);
