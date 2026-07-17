#include "telemetry_bmp280_bringup.h"

#include <stdio.h>

#include "board_config.h"

static Bmp280BringupTelemetryStatus map_snprintf_result(int written, size_t buffer_size) {
    if (written < 0) {
        return BMP280_BRINGUP_TELEMETRY_INVALID_ARGUMENT;
    }
    return (size_t)written < buffer_size ? BMP280_BRINGUP_TELEMETRY_OK : BMP280_BRINGUP_TELEMETRY_BUFFER_TOO_SMALL;
}

const char *bmp280_bringup_stage_to_text(Bmp280BringupStage stage) {
    switch (stage) {
        case BMP280_BRINGUP_STAGE_PLATFORM_INIT:
            return "platform_init";
        case BMP280_BRINGUP_STAGE_I2C_RECOVERY:
            return "i2c_recovery";
        case BMP280_BRINGUP_STAGE_PROBE_ADDRESS:
            return "probe_address";
        case BMP280_BRINGUP_STAGE_READ_CHIP_ID:
            return "read_chip_id";
        case BMP280_BRINGUP_STAGE_READ_CALIBRATION:
            return "read_calibration";
        case BMP280_BRINGUP_STAGE_CONFIGURE_SENSOR:
            return "configure_sensor";
        case BMP280_BRINGUP_STAGE_READ_CONFIGURATION:
            return "read_configuration";
        case BMP280_BRINGUP_STAGE_RUNNING:
            return "running";
        default:
            return "unknown";
    }
}

Bmp280BringupTelemetryStatus bmp280_bringup_format_identity(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    OpenRf1Status status,
    Bmp280BringupStage stage,
    uint8_t has_chip_id,
    uint8_t chip_id,
    uint8_t ctrl_meas,
    uint8_t config
) {
    if (buffer == 0 || buffer_size == 0u) {
        return BMP280_BRINGUP_TELEMETRY_INVALID_ARGUMENT;
    }

    const char *status_text = openrf1_status_to_text(status);
    const char *stage_text = bmp280_bringup_stage_to_text(stage);
    int written = 0;
    if (has_chip_id != 0u) {
        written = snprintf(
            buffer,
            buffer_size,
            "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
            "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"sensor_identity\","
            "\"sensor_id\":\"%s\",\"status\":\"%s\","
            "\"payload\":{\"configured_address\":\"0x%02X\",\"expected_chip_id\":\"0x%02X\","
            "\"chip_id\":\"0x%02X\",\"initialization_stage\":\"%s\",\"error_code\":%s,"
            "\"ctrl_meas\":\"0x%02X\",\"config\":\"0x%02X\"}}\n",
            (unsigned long)sequence,
            (unsigned long)timestamp_ms,
            OPENRF1_BMP280_SENSOR_ID,
            status_text,
            (unsigned int)OPENRF1_BMP280_ADDRESS_7BIT,
            (unsigned int)BMP280_CHIP_ID_EXPECTED,
            (unsigned int)chip_id,
            stage_text,
            status == OPENRF1_STATUS_OK ? "null" : "\"sensor_init_failed\"",
            (unsigned int)ctrl_meas,
            (unsigned int)config
        );
    } else {
        written = snprintf(
            buffer,
            buffer_size,
            "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
            "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"sensor_identity\","
            "\"sensor_id\":\"%s\",\"status\":\"%s\","
            "\"payload\":{\"configured_address\":\"0x%02X\",\"expected_chip_id\":\"0x%02X\","
            "\"chip_id\":null,\"initialization_stage\":\"%s\",\"error_code\":%s,"
            "\"ctrl_meas\":\"0x%02X\",\"config\":\"0x%02X\"}}\n",
            (unsigned long)sequence,
            (unsigned long)timestamp_ms,
            OPENRF1_BMP280_SENSOR_ID,
            status_text,
            (unsigned int)OPENRF1_BMP280_ADDRESS_7BIT,
            (unsigned int)BMP280_CHIP_ID_EXPECTED,
            stage_text,
            status == OPENRF1_STATUS_OK ? "null" : "\"sensor_init_failed\"",
            (unsigned int)ctrl_meas,
            (unsigned int)config
        );
    }
    return map_snprintf_result(written, buffer_size);
}

Bmp280BringupTelemetryStatus bmp280_bringup_format_environmental(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    const Bmp280CompensatedSample *sample
) {
    if (buffer == 0 || buffer_size == 0u || sample == 0) {
        return BMP280_BRINGUP_TELEMETRY_INVALID_ARGUMENT;
    }

    int32_t temperature = sample->temperature_centideg_c;
    uint32_t temperature_abs = temperature < 0 ? (uint32_t)(-temperature) : (uint32_t)temperature;
    const char *sign = temperature < 0 ? "-" : "";
    int written = snprintf(
        buffer,
        buffer_size,
        "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
        "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"environmental\","
        "\"sensor_id\":\"%s\",\"status\":\"ok\","
        "\"payload\":{\"temperature_c\":%s%lu.%02lu,\"pressure_pa\":%lu}}\n",
        (unsigned long)sequence,
        (unsigned long)timestamp_ms,
        OPENRF1_BMP280_SENSOR_ID,
        sign,
        (unsigned long)(temperature_abs / 100u),
        (unsigned long)(temperature_abs % 100u),
        (unsigned long)sample->pressure_pa
    );
    return map_snprintf_result(written, buffer_size);
}

Bmp280BringupTelemetryStatus bmp280_bringup_format_error(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    OpenRf1Status status,
    Bmp280BringupStage stage
) {
    if (buffer == 0 || buffer_size == 0u) {
        return BMP280_BRINGUP_TELEMETRY_INVALID_ARGUMENT;
    }

    int written = snprintf(
        buffer,
        buffer_size,
        "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
        "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"environmental\","
        "\"sensor_id\":\"%s\",\"status\":\"%s\","
        "\"payload\":{\"temperature_c\":null,\"pressure_pa\":null,"
        "\"initialization_stage\":\"%s\",\"error_code\":\"%s\"}}\n",
        (unsigned long)sequence,
        (unsigned long)timestamp_ms,
        OPENRF1_BMP280_SENSOR_ID,
        openrf1_status_to_text(status),
        bmp280_bringup_stage_to_text(stage),
        openrf1_status_to_text(status)
    );
    return map_snprintf_result(written, buffer_size);
}
