#include "telemetry.h"

#include <stdio.h>

#include "board_config.h"

TelemetryFormatStatus telemetry_format_bh1750(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    const Bh1750Sample *sample
) {
    if (buffer == NULL || sample == NULL || buffer_size == 0u) {
        return TELEMETRY_FORMAT_INVALID_ARGUMENT;
    }

    const char *status = bh1750_status_to_telemetry(sample->status);
    int written = 0;
    if (sample->has_illuminance != 0u) {
        uint32_t whole_lux = sample->illuminance_centilux / 100u;
        uint32_t frac_lux = sample->illuminance_centilux % 100u;
        written = snprintf(
            buffer,
            buffer_size,
            "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
            "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"illuminance\","
            "\"sensor_id\":\"%s\",\"status\":\"%s\","
            "\"payload\":{\"illuminance_lux\":%lu.%02lu}}\n",
            (unsigned long)sequence,
            (unsigned long)sample->timestamp_ms,
            OPENRF1_BH1750_SENSOR_ID,
            status,
            (unsigned long)whole_lux,
            (unsigned long)frac_lux
        );
    } else {
        written = snprintf(
            buffer,
            buffer_size,
            "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
            "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"illuminance\","
            "\"sensor_id\":\"%s\",\"status\":\"%s\","
            "\"payload\":{\"illuminance_lux\":null}}\n",
            (unsigned long)sequence,
            (unsigned long)sample->timestamp_ms,
            OPENRF1_BH1750_SENSOR_ID,
            status
        );
    }

    if (written < 0) {
        return TELEMETRY_FORMAT_INVALID_ARGUMENT;
    }
    if ((size_t)written >= buffer_size) {
        return TELEMETRY_FORMAT_BUFFER_TOO_SMALL;
    }
    return TELEMETRY_FORMAT_OK;
}
