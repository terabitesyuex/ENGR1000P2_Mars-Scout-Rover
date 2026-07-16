#pragma once

#include <stddef.h>
#include <stdint.h>

#include "openrf1_status.h"
#include "rplidar_c1_transport.h"

typedef enum {
    OPENRF1_FULL_TELEMETRY_OK = 0,
    OPENRF1_FULL_TELEMETRY_BUFFER_TOO_SMALL,
    OPENRF1_FULL_TELEMETRY_INVALID_ARGUMENT
} OpenRf1FullTelemetryStatus;

OpenRf1FullTelemetryStatus openrf1_format_subsystem_status(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    const char *subsystem,
    OpenRf1Status status,
    uint32_t error_count
);

OpenRf1FullTelemetryStatus openrf1_format_lidar_transport_stats(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    const RplidarC1TransportStats *stats
);
