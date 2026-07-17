#include "board_config.h"
#include "platform_bmp280_bringup.h"
#include "telemetry_bmp280_bringup.h"

#include "../full_hardware/bmp280.h"
#include "../full_hardware/i2c_bus.h"
#include "../full_hardware/openrf1_status.h"

typedef struct {
    Bmp280Calibration calibration;
    Bmp280BringupStage stage;
    OpenRf1Status init_status;
    uint32_t sequence;
    uint32_t next_sample_ms;
    uint8_t chip_id;
    uint8_t has_chip_id;
    uint8_t ctrl_meas;
    uint8_t config;
    uint8_t ready;
} Bmp280BringupApp;

static char g_telemetry_buffer[OPENRF1_BMP280_TELEMETRY_BUFFER_BYTES];

static OpenRf1Status initialize_bmp280(Bmp280BringupApp *app);
static void emit_identity(Bmp280BringupApp *app, uint32_t now_ms);
static void emit_environmental_or_error(Bmp280BringupApp *app, uint32_t now_ms);
static void emit_line(Bmp280BringupTelemetryStatus format_status, Bmp280BringupApp *app);

int main(void) {
    Bmp280BringupApp app = {0};
    app.stage = BMP280_BRINGUP_STAGE_PLATFORM_INIT;

    openrf1_bmp280_platform_init();
    app.init_status = initialize_bmp280(&app);
    app.ready = app.init_status == OPENRF1_STATUS_OK ? 1u : 0u;
    app.next_sample_ms = openrf1_bmp280_millis() + OPENRF1_BMP280_SAMPLE_PERIOD_MS;
    emit_identity(&app, openrf1_bmp280_millis());

    while (1) {
        uint32_t now_ms = openrf1_bmp280_millis();
        if ((int32_t)(now_ms - app.next_sample_ms) >= 0) {
            app.next_sample_ms += OPENRF1_BMP280_SAMPLE_PERIOD_MS;
            emit_environmental_or_error(&app, now_ms);
        }
    }
}

static OpenRf1Status initialize_bmp280(Bmp280BringupApp *app) {
    OpenRf1Status status;

    app->stage = BMP280_BRINGUP_STAGE_I2C_RECOVERY;
    openrf1_i2c_bus_init();
    status = openrf1_i2c_recover();
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }

    app->stage = BMP280_BRINGUP_STAGE_PROBE_ADDRESS;
    status = openrf1_i2c_probe(OPENRF1_BMP280_ADDRESS_7BIT);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }

    app->stage = BMP280_BRINGUP_STAGE_READ_CHIP_ID;
    status = bmp280_read_chip_id(OPENRF1_BMP280_ADDRESS_7BIT, &app->chip_id);
    app->has_chip_id = 1u;
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }

    app->stage = BMP280_BRINGUP_STAGE_READ_CALIBRATION;
    status = bmp280_read_calibration(OPENRF1_BMP280_ADDRESS_7BIT, &app->calibration);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }

    app->stage = BMP280_BRINGUP_STAGE_CONFIGURE_SENSOR;
    status = bmp280_configure_normal_mode(OPENRF1_BMP280_ADDRESS_7BIT);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }

    app->stage = BMP280_BRINGUP_STAGE_READ_CONFIGURATION;
    status = bmp280_read_configuration(OPENRF1_BMP280_ADDRESS_7BIT, &app->ctrl_meas, &app->config);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    if (app->ctrl_meas != BMP280_CTRL_MEAS_TEMP_X1_PRESS_X1_NORMAL ||
        app->config != BMP280_CONFIG_STANDBY_500_MS_FILTER_OFF) {
        return OPENRF1_STATUS_HARDWARE_FAULT;
    }

    app->stage = BMP280_BRINGUP_STAGE_RUNNING;
    return OPENRF1_STATUS_OK;
}

static void emit_identity(Bmp280BringupApp *app, uint32_t now_ms) {
    Bmp280BringupTelemetryStatus status = bmp280_bringup_format_identity(
        g_telemetry_buffer,
        sizeof(g_telemetry_buffer),
        app->sequence,
        now_ms,
        app->init_status,
        app->stage,
        app->has_chip_id,
        app->chip_id,
        app->ctrl_meas,
        app->config
    );
    emit_line(status, app);
}

static void emit_environmental_or_error(Bmp280BringupApp *app, uint32_t now_ms) {
    if (app->ready == 0u) {
        Bmp280BringupTelemetryStatus status = bmp280_bringup_format_error(
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

    Bmp280RawSample raw_sample;
    Bmp280CompensatedSample compensated;
    OpenRf1Status status = bmp280_read_raw_sample(OPENRF1_BMP280_ADDRESS_7BIT, &raw_sample);
    if (status == OPENRF1_STATUS_OK) {
        status = bmp280_compensate(&app->calibration, &raw_sample, &compensated);
    }
    if (status != OPENRF1_STATUS_OK) {
        Bmp280BringupTelemetryStatus format_status = bmp280_bringup_format_error(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms,
            status,
            BMP280_BRINGUP_STAGE_RUNNING
        );
        emit_line(format_status, app);
        return;
    }

    Bmp280BringupTelemetryStatus format_status = bmp280_bringup_format_environmental(
        g_telemetry_buffer,
        sizeof(g_telemetry_buffer),
        app->sequence,
        now_ms,
        &compensated
    );
    emit_line(format_status, app);
}

static void emit_line(Bmp280BringupTelemetryStatus format_status, Bmp280BringupApp *app) {
    if (format_status == BMP280_BRINGUP_TELEMETRY_OK) {
        openrf1_bmp280_debug_write_bounded(g_telemetry_buffer, OPENRF1_BMP280_TELEMETRY_BUFFER_BYTES);
        ++app->sequence;
    }
}
