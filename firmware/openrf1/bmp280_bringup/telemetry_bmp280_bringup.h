#pragma once

#include <stddef.h>
#include <stdint.h>

#include "../full_hardware/bmp280.h"
#include "../full_hardware/openrf1_status.h"

typedef enum {
    BMP280_BRINGUP_TELEMETRY_OK = 0,
    BMP280_BRINGUP_TELEMETRY_BUFFER_TOO_SMALL,
    BMP280_BRINGUP_TELEMETRY_INVALID_ARGUMENT
} Bmp280BringupTelemetryStatus;

typedef enum {
    BMP280_BRINGUP_STAGE_PLATFORM_INIT = 0,
    BMP280_BRINGUP_STAGE_I2C_RECOVERY,
    BMP280_BRINGUP_STAGE_PROBE_ADDRESS,
    BMP280_BRINGUP_STAGE_READ_CHIP_ID,
    BMP280_BRINGUP_STAGE_READ_CALIBRATION,
    BMP280_BRINGUP_STAGE_CONFIGURE_SENSOR,
    BMP280_BRINGUP_STAGE_READ_CONFIGURATION,
    BMP280_BRINGUP_STAGE_RUNNING
} Bmp280BringupStage;

const char *bmp280_bringup_stage_to_text(Bmp280BringupStage stage);
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
);
Bmp280BringupTelemetryStatus bmp280_bringup_format_environmental(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    const Bmp280CompensatedSample *sample
);
Bmp280BringupTelemetryStatus bmp280_bringup_format_error(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    OpenRf1Status status,
    Bmp280BringupStage stage
);
