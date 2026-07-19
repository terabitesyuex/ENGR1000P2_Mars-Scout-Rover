#include "telemetry_mpu6050_bringup.h"

#include <stdio.h>

#include "board_config.h"

typedef struct {
    const char *sign;
    uint32_t whole;
    uint32_t fraction;
} FixedValue;

static Mpu6050BringupTelemetryStatus map_snprintf_result(int written, size_t buffer_size) {
    if (written < 0) {
        return MPU6050_BRINGUP_TELEMETRY_INVALID_ARGUMENT;
    }
    return (size_t)written < buffer_size ? MPU6050_BRINGUP_TELEMETRY_OK : MPU6050_BRINGUP_TELEMETRY_BUFFER_TOO_SMALL;
}

static FixedValue fixed3_from_milli(int32_t value_milli) {
    uint32_t magnitude = value_milli < 0 ? (uint32_t)(-value_milli) : (uint32_t)value_milli;
    FixedValue fixed = {value_milli < 0 ? "-" : "", magnitude / 1000u, magnitude % 1000u};
    return fixed;
}

static FixedValue fixed2_from_centi(int32_t value_centi) {
    uint32_t magnitude = value_centi < 0 ? (uint32_t)(-value_centi) : (uint32_t)value_centi;
    FixedValue fixed = {value_centi < 0 ? "-" : "", magnitude / 100u, magnitude % 100u};
    return fixed;
}

const char *mpu6050_bringup_stage_to_text(Mpu6050BringupStage stage) {
    switch (stage) {
        case MPU6050_BRINGUP_STAGE_PLATFORM_INIT:
            return "platform_init";
        case MPU6050_BRINGUP_STAGE_I2C_RECOVERY:
            return "i2c_recovery";
        case MPU6050_BRINGUP_STAGE_PROBE_ADDRESS:
            return "probe_address";
        case MPU6050_BRINGUP_STAGE_READ_WHO_AM_I:
            return "read_who_am_i";
        case MPU6050_BRINGUP_STAGE_WAKE_SENSOR:
            return "wake_sensor";
        case MPU6050_BRINGUP_STAGE_SETTLE_AFTER_WAKE:
            return "settle_after_wake";
        case MPU6050_BRINGUP_STAGE_CONFIGURE_SMPLRT_DIV:
            return "configure_smplrt_div";
        case MPU6050_BRINGUP_STAGE_CONFIGURE_DLPF:
            return "configure_dlpf";
        case MPU6050_BRINGUP_STAGE_CONFIGURE_GYRO:
            return "configure_gyro";
        case MPU6050_BRINGUP_STAGE_CONFIGURE_ACCEL:
            return "configure_accel";
        case MPU6050_BRINGUP_STAGE_READ_CONFIGURATION:
            return "read_configuration";
        case MPU6050_BRINGUP_STAGE_RUNNING:
            return "running";
        default:
            return "unknown";
    }
}

static const char *stage_operation(Mpu6050BringupStage stage) {
    switch (stage) {
        case MPU6050_BRINGUP_STAGE_I2C_RECOVERY:
            return "i2c_recovery";
        case MPU6050_BRINGUP_STAGE_PROBE_ADDRESS:
            return "probe_address";
        case MPU6050_BRINGUP_STAGE_READ_WHO_AM_I:
            return "read_who_am_i";
        case MPU6050_BRINGUP_STAGE_WAKE_SENSOR:
            return "write_readback_pwr_mgmt_1";
        case MPU6050_BRINGUP_STAGE_CONFIGURE_SMPLRT_DIV:
            return "write_readback_smplrt_div";
        case MPU6050_BRINGUP_STAGE_CONFIGURE_DLPF:
            return "write_readback_config";
        case MPU6050_BRINGUP_STAGE_CONFIGURE_GYRO:
            return "write_readback_gyro_config";
        case MPU6050_BRINGUP_STAGE_CONFIGURE_ACCEL:
            return "write_readback_accel_config";
        case MPU6050_BRINGUP_STAGE_READ_CONFIGURATION:
            return "read_configuration";
        case MPU6050_BRINGUP_STAGE_RUNNING:
            return "read_measurement_burst";
        default:
            return "initialization";
    }
}

static const char *stage_register_json(Mpu6050BringupStage stage) {
    switch (stage) {
        case MPU6050_BRINGUP_STAGE_READ_WHO_AM_I:
            return "\"0x75\"";
        case MPU6050_BRINGUP_STAGE_WAKE_SENSOR:
            return "\"0x6B\"";
        case MPU6050_BRINGUP_STAGE_CONFIGURE_SMPLRT_DIV:
            return "\"0x19\"";
        case MPU6050_BRINGUP_STAGE_CONFIGURE_DLPF:
            return "\"0x1A\"";
        case MPU6050_BRINGUP_STAGE_CONFIGURE_GYRO:
            return "\"0x1B\"";
        case MPU6050_BRINGUP_STAGE_CONFIGURE_ACCEL:
            return "\"0x1C\"";
        case MPU6050_BRINGUP_STAGE_RUNNING:
            return "\"0x3B\"";
        default:
            return "null";
    }
}

Mpu6050BringupTelemetryStatus mpu6050_bringup_format_identity(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    Mpu6050BringupStage stage,
    uint8_t who_am_i,
    const Mpu6050RegisterConfig *config
) {
    if (buffer == 0 || buffer_size == 0u || config == 0) {
        return MPU6050_BRINGUP_TELEMETRY_INVALID_ARGUMENT;
    }

    int written = snprintf(
        buffer,
        buffer_size,
        "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
        "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"sensor_identity\","
        "\"sensor_id\":\"%s\",\"status\":\"ok\","
        "\"payload\":{\"sensor\":\"mpu6050\",\"configured_address\":\"0x%02X\","
        "\"expected_who_am_i\":\"0x%02X\",\"who_am_i\":\"0x%02X\","
        "\"initialization_stage\":\"%s\",\"error_code\":null,"
        "\"pwr_mgmt_1\":\"0x%02X\",\"smplrt_div\":\"0x%02X\","
        "\"config\":\"0x%02X\",\"gyro_config\":\"0x%02X\",\"accel_config\":\"0x%02X\","
        "\"accel_range_g\":2,\"gyro_range_dps\":250,\"telemetry_period_ms\":%lu}}\n",
        (unsigned long)sequence,
        (unsigned long)timestamp_ms,
        OPENRF1_MPU6050_SENSOR_ID,
        (unsigned int)OPENRF1_MPU6050_ADDRESS_7BIT,
        (unsigned int)MPU6050_WHO_AM_I_EXPECTED,
        (unsigned int)who_am_i,
        mpu6050_bringup_stage_to_text(stage),
        (unsigned int)config->pwr_mgmt_1,
        (unsigned int)config->smplrt_div,
        (unsigned int)config->config,
        (unsigned int)config->gyro_config,
        (unsigned int)config->accel_config,
        (unsigned long)OPENRF1_MPU6050_SAMPLE_PERIOD_MS
    );
    return map_snprintf_result(written, buffer_size);
}

Mpu6050BringupTelemetryStatus mpu6050_bringup_format_imu(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    const Mpu6050RawSample *sample,
    int32_t gyro_bias_x_mdps,
    int32_t gyro_bias_y_mdps,
    int32_t gyro_bias_z_mdps
) {
    if (buffer == 0 || buffer_size == 0u || sample == 0) {
        return MPU6050_BRINGUP_TELEMETRY_INVALID_ARGUMENT;
    }

    FixedValue accel_x = fixed3_from_milli(mpu6050_accel_raw_to_mg(sample->accel_x_raw, MPU6050_ACCEL_RANGE_2G));
    FixedValue accel_y = fixed3_from_milli(mpu6050_accel_raw_to_mg(sample->accel_y_raw, MPU6050_ACCEL_RANGE_2G));
    FixedValue accel_z = fixed3_from_milli(mpu6050_accel_raw_to_mg(sample->accel_z_raw, MPU6050_ACCEL_RANGE_2G));
    FixedValue gyro_x = fixed3_from_milli(mpu6050_gyro_raw_to_mdps(sample->gyro_x_raw, MPU6050_GYRO_RANGE_250DPS) - gyro_bias_x_mdps);
    FixedValue gyro_y = fixed3_from_milli(mpu6050_gyro_raw_to_mdps(sample->gyro_y_raw, MPU6050_GYRO_RANGE_250DPS) - gyro_bias_y_mdps);
    FixedValue gyro_z = fixed3_from_milli(mpu6050_gyro_raw_to_mdps(sample->gyro_z_raw, MPU6050_GYRO_RANGE_250DPS) - gyro_bias_z_mdps);
    FixedValue temperature = fixed2_from_centi(mpu6050_temperature_raw_to_centideg_c(sample->temperature_raw));

    int written = snprintf(
        buffer,
        buffer_size,
        "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
        "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"imu\","
        "\"sensor_id\":\"%s\",\"status\":\"ok\","
        "\"payload\":{\"accel_raw\":{\"x\":%d,\"y\":%d,\"z\":%d},"
        "\"gyro_raw\":{\"x\":%d,\"y\":%d,\"z\":%d},\"temperature_raw\":%d,"
        "\"accel_g\":{\"x\":%s%lu.%03lu,\"y\":%s%lu.%03lu,\"z\":%s%lu.%03lu},"
        "\"gyro_dps\":{\"x\":%s%lu.%03lu,\"y\":%s%lu.%03lu,\"z\":%s%lu.%03lu},"
        "\"temperature_c\":%s%lu.%02lu}}\n",
        (unsigned long)sequence,
        (unsigned long)timestamp_ms,
        OPENRF1_MPU6050_SENSOR_ID,
        (int)sample->accel_x_raw,
        (int)sample->accel_y_raw,
        (int)sample->accel_z_raw,
        (int)sample->gyro_x_raw,
        (int)sample->gyro_y_raw,
        (int)sample->gyro_z_raw,
        (int)sample->temperature_raw,
        accel_x.sign,
        (unsigned long)accel_x.whole,
        (unsigned long)accel_x.fraction,
        accel_y.sign,
        (unsigned long)accel_y.whole,
        (unsigned long)accel_y.fraction,
        accel_z.sign,
        (unsigned long)accel_z.whole,
        (unsigned long)accel_z.fraction,
        gyro_x.sign,
        (unsigned long)gyro_x.whole,
        (unsigned long)gyro_x.fraction,
        gyro_y.sign,
        (unsigned long)gyro_y.whole,
        (unsigned long)gyro_y.fraction,
        gyro_z.sign,
        (unsigned long)gyro_z.whole,
        (unsigned long)gyro_z.fraction,
        temperature.sign,
        (unsigned long)temperature.whole,
        (unsigned long)temperature.fraction
    );
    return map_snprintf_result(written, buffer_size);
}

Mpu6050BringupTelemetryStatus mpu6050_bringup_format_error(
    char *buffer,
    size_t buffer_size,
    uint32_t sequence,
    uint32_t timestamp_ms,
    OpenRf1Status status,
    Mpu6050BringupStage stage
) {
    if (buffer == 0 || buffer_size == 0u) {
        return MPU6050_BRINGUP_TELEMETRY_INVALID_ARGUMENT;
    }

    int written = snprintf(
        buffer,
        buffer_size,
        "{\"protocol\":\"mars_scout_stm32_sensor_telemetry\",\"version\":1,"
        "\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"imu\","
        "\"sensor_id\":\"%s\",\"status\":\"%s\","
        "\"payload\":{\"accel_raw\":null,\"gyro_raw\":null,\"temperature_raw\":null,"
        "\"accel_g\":null,\"gyro_dps\":null,\"temperature_c\":null,"
        "\"initialization_stage\":\"%s\",\"operation\":\"%s\",\"register\":%s,"
        "\"error_code\":\"%s\"}}\n",
        (unsigned long)sequence,
        (unsigned long)timestamp_ms,
        OPENRF1_MPU6050_SENSOR_ID,
        openrf1_status_to_text(status),
        mpu6050_bringup_stage_to_text(stage),
        stage_operation(stage),
        stage_register_json(stage),
        openrf1_status_to_text(status)
    );
    return map_snprintf_result(written, buffer_size);
}
