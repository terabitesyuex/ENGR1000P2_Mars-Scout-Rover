#include "board_config.h"
#include "platform_mpu6050_bringup.h"
#include "telemetry_mpu6050_bringup.h"

#include "../full_hardware/i2c_bus.h"
#include "../full_hardware/mpu6050.h"
#include "../full_hardware/openrf1_status.h"

typedef struct {
    Mpu6050BringupStage stage;
    Mpu6050RegisterConfig config;
    OpenRf1Status init_status;
    uint32_t sequence;
    uint32_t next_sample_ms;
    int32_t gyro_bias_x_mdps;
    int32_t gyro_bias_y_mdps;
    int32_t gyro_bias_z_mdps;
    uint8_t who_am_i;
    uint8_t ready;
} Mpu6050BringupApp;

static char g_telemetry_buffer[OPENRF1_MPU6050_TELEMETRY_BUFFER_BYTES];

static OpenRf1Status initialize_mpu6050(Mpu6050BringupApp *app);
static OpenRf1Status calibrate_gyro(Mpu6050BringupApp *app);
static OpenRf1Status configure_register(Mpu6050BringupApp *app, Mpu6050BringupStage stage, uint8_t reg, uint8_t value, uint8_t *readback);
static OpenRf1Status verify_final_configuration(Mpu6050BringupApp *app);
static void emit_startup(Mpu6050BringupApp *app, uint32_t now_ms);
static void emit_imu_or_error(Mpu6050BringupApp *app, uint32_t now_ms);
static void emit_line(Mpu6050BringupTelemetryStatus format_status, Mpu6050BringupApp *app);

int main(void) {
    Mpu6050BringupApp app = {0};
    app.stage = MPU6050_BRINGUP_STAGE_PLATFORM_INIT;

    openrf1_mpu6050_platform_init();
    app.init_status = initialize_mpu6050(&app);
    if (app.init_status == OPENRF1_STATUS_OK) {
        app.init_status = calibrate_gyro(&app);
    }
    app.ready = app.init_status == OPENRF1_STATUS_OK ? 1u : 0u;
    app.next_sample_ms = openrf1_mpu6050_millis() + OPENRF1_MPU6050_SAMPLE_PERIOD_MS;
    emit_startup(&app, openrf1_mpu6050_millis());

    while (1) {
        uint32_t now_ms = openrf1_mpu6050_millis();
        if ((int32_t)(now_ms - app.next_sample_ms) >= 0) {
            app.next_sample_ms += OPENRF1_MPU6050_SAMPLE_PERIOD_MS;
            emit_imu_or_error(&app, now_ms);
        }
    }
}

static OpenRf1Status calibrate_gyro(Mpu6050BringupApp *app) {
    const uint32_t sample_count = 500u;
    int64_t sum_x_mdps = 0;
    int64_t sum_y_mdps = 0;
    int64_t sum_z_mdps = 0;

    openrf1_mpu6050_delay_ms(5000u);

    for (uint32_t i = 0u; i < sample_count; ++i) {
        Mpu6050RawSample sample;
        OpenRf1Status status = mpu6050_read_raw_sample(
            OPENRF1_MPU6050_ADDRESS_7BIT,
            &sample
        );
        if (status != OPENRF1_STATUS_OK) {
            return status;
        }

        sum_x_mdps += mpu6050_gyro_raw_to_mdps(
            sample.gyro_x_raw,
            MPU6050_GYRO_RANGE_250DPS
        );
        sum_y_mdps += mpu6050_gyro_raw_to_mdps(
            sample.gyro_y_raw,
            MPU6050_GYRO_RANGE_250DPS
        );
        sum_z_mdps += mpu6050_gyro_raw_to_mdps(
            sample.gyro_z_raw,
            MPU6050_GYRO_RANGE_250DPS
        );

        openrf1_mpu6050_delay_ms(10u);
    }

    app->gyro_bias_x_mdps = (int32_t)(sum_x_mdps / (int64_t)sample_count);
    app->gyro_bias_y_mdps = (int32_t)(sum_y_mdps / (int64_t)sample_count);
    app->gyro_bias_z_mdps = (int32_t)(sum_z_mdps / (int64_t)sample_count);

    return OPENRF1_STATUS_OK;
}

static OpenRf1Status initialize_mpu6050(Mpu6050BringupApp *app) {
    OpenRf1Status status;

    app->stage = MPU6050_BRINGUP_STAGE_I2C_RECOVERY;
    openrf1_i2c_bus_init();
    status = openrf1_i2c_recover();
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }

    app->stage = MPU6050_BRINGUP_STAGE_PROBE_ADDRESS;
    status = openrf1_i2c_probe(OPENRF1_MPU6050_ADDRESS_7BIT);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }

    app->stage = MPU6050_BRINGUP_STAGE_READ_WHO_AM_I;
    status = mpu6050_read_who_am_i(OPENRF1_MPU6050_ADDRESS_7BIT, &app->who_am_i);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }

    app->stage = MPU6050_BRINGUP_STAGE_WAKE_SENSOR;
    status = mpu6050_wake_for_bringup(OPENRF1_MPU6050_ADDRESS_7BIT, &app->config.pwr_mgmt_1);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }

    app->stage = MPU6050_BRINGUP_STAGE_SETTLE_AFTER_WAKE;
    openrf1_mpu6050_delay_ms(OPENRF1_MPU6050_WAKE_SETTLE_MS);

    status = configure_register(app, MPU6050_BRINGUP_STAGE_CONFIGURE_SMPLRT_DIV, MPU6050_REG_SMPLRT_DIV, MPU6050_SMPLRT_DIV_100HZ_DLPF, &app->config.smplrt_div);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    status = configure_register(app, MPU6050_BRINGUP_STAGE_CONFIGURE_DLPF, MPU6050_REG_CONFIG, MPU6050_CONFIG_DLPF_44HZ, &app->config.config);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    status = configure_register(app, MPU6050_BRINGUP_STAGE_CONFIGURE_GYRO, MPU6050_REG_GYRO_CONFIG, MPU6050_GYRO_CONFIG_250DPS, &app->config.gyro_config);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    status = configure_register(app, MPU6050_BRINGUP_STAGE_CONFIGURE_ACCEL, MPU6050_REG_ACCEL_CONFIG, MPU6050_ACCEL_CONFIG_2G, &app->config.accel_config);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }

    return verify_final_configuration(app);
}

static OpenRf1Status configure_register(Mpu6050BringupApp *app, Mpu6050BringupStage stage, uint8_t reg, uint8_t value, uint8_t *readback) {
    app->stage = stage;
    return mpu6050_write_register_readback(OPENRF1_MPU6050_ADDRESS_7BIT, reg, value, readback);
}

static OpenRf1Status verify_final_configuration(Mpu6050BringupApp *app) {
    app->stage = MPU6050_BRINGUP_STAGE_READ_CONFIGURATION;
    OpenRf1Status status = mpu6050_read_configuration(OPENRF1_MPU6050_ADDRESS_7BIT, &app->config);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    if (app->config.pwr_mgmt_1 != MPU6050_PWR_MGMT_1_X_GYRO_PLL ||
        app->config.smplrt_div != MPU6050_SMPLRT_DIV_100HZ_DLPF ||
        app->config.config != MPU6050_CONFIG_DLPF_44HZ ||
        app->config.gyro_config != MPU6050_GYRO_CONFIG_250DPS ||
        app->config.accel_config != MPU6050_ACCEL_CONFIG_2G) {
        return OPENRF1_STATUS_HARDWARE_FAULT;
    }

    app->stage = MPU6050_BRINGUP_STAGE_RUNNING;
    return OPENRF1_STATUS_OK;
}

static void emit_startup(Mpu6050BringupApp *app, uint32_t now_ms) {
    Mpu6050BringupTelemetryStatus status;
    if (app->ready != 0u) {
        status = mpu6050_bringup_format_identity(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms,
            app->stage,
            app->who_am_i,
            &app->config
        );
    } else {
        status = mpu6050_bringup_format_error(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms,
            app->init_status,
            app->stage
        );
    }
    emit_line(status, app);
}

static void emit_imu_or_error(Mpu6050BringupApp *app, uint32_t now_ms) {
    if (app->ready == 0u) {
        Mpu6050BringupTelemetryStatus status = mpu6050_bringup_format_error(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms,
            app->init_status,
            app->stage
        );
        emit_line(status, app);
        return;
    }

    Mpu6050RawSample sample;
    OpenRf1Status status = mpu6050_read_raw_sample(OPENRF1_MPU6050_ADDRESS_7BIT, &sample);
    if (status != OPENRF1_STATUS_OK) {
        Mpu6050BringupTelemetryStatus format_status = mpu6050_bringup_format_error(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms,
            status,
            MPU6050_BRINGUP_STAGE_RUNNING
        );
        emit_line(format_status, app);
        return;
    }

    Mpu6050BringupTelemetryStatus format_status = mpu6050_bringup_format_imu(
        g_telemetry_buffer,
        sizeof(g_telemetry_buffer),
        app->sequence,
        now_ms,
        &sample,
        app->gyro_bias_x_mdps,
        app->gyro_bias_y_mdps,
        app->gyro_bias_z_mdps
    );
    emit_line(format_status, app);
}

static void emit_line(Mpu6050BringupTelemetryStatus format_status, Mpu6050BringupApp *app) {
    if (format_status == MPU6050_BRINGUP_TELEMETRY_OK) {
        openrf1_mpu6050_debug_write_bounded(g_telemetry_buffer, OPENRF1_MPU6050_TELEMETRY_BUFFER_BYTES);
        ++app->sequence;
    }
}
