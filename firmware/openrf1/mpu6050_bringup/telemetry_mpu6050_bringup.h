#pragma once

#include <stddef.h>
#include <stdint.h>

#include "../full_hardware/mpu6050.h"
#include "../full_hardware/openrf1_status.h"

typedef enum {
    MPU6050_BRINGUP_TELEMETRY_OK = 0,
    MPU6050_BRINGUP_TELEMETRY_BUFFER_TOO_SMALL,
    MPU6050_BRINGUP_TELEMETRY_INVALID_ARGUMENT
} Mpu6050BringupTelemetryStatus;

typedef enum {
    MPU6050_BRINGUP_STAGE_PLATFORM_INIT = 0,
    MPU6050_BRINGUP_STAGE_I2C_RECOVERY,
    MPU6050_BRINGUP_STAGE_PROBE_ADDRESS,
    MPU6050_BRINGUP_STAGE_READ_WHO_AM_I,
    MPU6050_BRINGUP_STAGE_WAKE_SENSOR,
    MPU6050_BRINGUP_STAGE_SETTLE_AFTER_WAKE,
    MPU6050_BRINGUP_STAGE_CONFIGURE_SMPLRT_DIV,
    MPU6050_BRINGUP_STAGE_CONFIGURE_DLPF,
    MPU6050_BRINGUP_STAGE_CONFIGURE_GYRO,
    MPU6050_BRINGUP_STAGE_CONFIGURE_ACCEL,
    MPU6050_BRINGUP_STAGE_READ_CONFIGURATION,
    MPU6050_BRINGUP_STAGE_RUNNING
} Mpu6050BringupStage;

const char *mpu6050_bringup_stage_to_text(Mpu6050BringupStage stage);
Mpu6050BringupTelemetryStatus mpu6050_bringup_format_identity(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    Mpu6050BringupStage stage,
    uint8_t who_am_i,
    const Mpu6050RegisterConfig *config
);
Mpu6050BringupTelemetryStatus mpu6050_bringup_format_imu(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    const Mpu6050RawSample *sample
);
Mpu6050BringupTelemetryStatus mpu6050_bringup_format_error(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    OpenRf1Status status,
    Mpu6050BringupStage stage
);
