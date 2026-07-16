#include "telemetry_full.h"

#include <stdio.h>

OpenRf1FullTelemetryStatus openrf1_format_subsystem_status(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    const char *subsystem,
    OpenRf1Status status,
    uint32_t error_count
) {
    if (buffer == 0 || buffer_size == 0u || subsystem == 0) {
        return OPENRF1_FULL_TELEMETRY_INVALID_ARGUMENT;
    }
    int written = snprintf(
        buffer,
        buffer_size,
        "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
        "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"subsystem_status\","
        "\"sensor_id\":\"stm32_subsystem\",\"status\":\"ok\","
        "\"payload\":{\"subsystem\":\"%s\",\"health\":\"%s\",\"error_count\":%lu}}\n",
        (unsigned long)sequence,
        (unsigned long)timestamp_ms,
        subsystem,
        openrf1_status_to_text(status),
        (unsigned long)error_count
    );
    if (written < 0) {
        return OPENRF1_FULL_TELEMETRY_INVALID_ARGUMENT;
    }
    return (size_t)written < buffer_size ? OPENRF1_FULL_TELEMETRY_OK : OPENRF1_FULL_TELEMETRY_BUFFER_TOO_SMALL;
}

OpenRf1FullTelemetryStatus openrf1_format_lidar_transport_stats(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    const RplidarC1TransportStats *stats
) {
    if (buffer == 0 || buffer_size == 0u || stats == 0) {
        return OPENRF1_FULL_TELEMETRY_INVALID_ARGUMENT;
    }
    int written = snprintf(
        buffer,
        buffer_size,
        "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
        "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"lidar_transport_stats\","
        "\"sensor_id\":\"c1_1\",\"status\":\"ok\","
        "\"payload\":{\"rx_bytes\":%lu,\"bytes_read\":%lu,\"overflow_count\":%lu,"
        "\"framing_error_count\":%lu,\"last_rx_tick_ms\":%lu}}\n",
        (unsigned long)sequence,
        (unsigned long)timestamp_ms,
        (unsigned long)stats->rx_bytes,
        (unsigned long)stats->bytes_read,
        (unsigned long)stats->overflow_count,
        (unsigned long)stats->framing_error_count,
        (unsigned long)stats->last_rx_tick_ms
    );
    if (written < 0) {
        return OPENRF1_FULL_TELEMETRY_INVALID_ARGUMENT;
    }
    return (size_t)written < buffer_size ? OPENRF1_FULL_TELEMETRY_OK : OPENRF1_FULL_TELEMETRY_BUFFER_TOO_SMALL;
}
