#include "board_config.h"
#include "ground_sensors.h"
#include "platform_ground_sensors_bringup.h"
#include "telemetry_ground_sensors_bringup.h"

#include "../full_hardware/openrf1_status.h"

typedef struct {
    GroundSensorsState sensors;
    GroundSensorsResultCode driver_status;
    OpenRf1Status platform_status;
    uint32_t sequence;
    uint32_t next_sample_ms;
    uint32_t next_telemetry_ms;
    uint8_t ready;
} GroundSensorsBringupApp;

static char g_telemetry_buffer[OPENRF1_GROUND_TELEMETRY_BUFFER_BYTES];

static void initialize_app(GroundSensorsBringupApp *app);
static void service_sample(GroundSensorsBringupApp *app);
static void emit_identity_or_error(GroundSensorsBringupApp *app, uint32_t now_ms);
static void emit_sample_or_error(GroundSensorsBringupApp *app, uint32_t now_ms);
static void emit_line(GroundSensorsTelemetryStatus status, GroundSensorsBringupApp *app);

int main(void) {
    GroundSensorsBringupApp app = {0};
    initialize_app(&app);
    uint32_t now_ms = openrf1_ground_millis();
    app.next_sample_ms = now_ms + OPENRF1_GROUND_SAMPLE_PERIOD_MS;
    app.next_telemetry_ms = now_ms + OPENRF1_GROUND_TELEMETRY_PERIOD_MS;
    emit_identity_or_error(&app, now_ms);

    while (1) {
        now_ms = openrf1_ground_millis();
        if ((int32_t)(now_ms - app.next_sample_ms) >= 0) {
            app.next_sample_ms += OPENRF1_GROUND_SAMPLE_PERIOD_MS;
            service_sample(&app);
        }
        if ((int32_t)(now_ms - app.next_telemetry_ms) >= 0) {
            app.next_telemetry_ms += OPENRF1_GROUND_TELEMETRY_PERIOD_MS;
            emit_sample_or_error(&app, now_ms);
        }
    }
}

static void initialize_app(GroundSensorsBringupApp *app) {
    app->platform_status = openrf1_ground_platform_init();
    if (app->platform_status != OPENRF1_STATUS_OK) {
        app->driver_status = GROUND_SENSORS_RESULT_SCHEDULER_INVARIANT;
        app->ready = 0u;
        return;
    }

    GroundSensorsRawLevels initial_levels = openrf1_ground_read_levels();
    app->driver_status = ground_sensors_init(
        &app->sensors,
        &initial_levels,
        OPENRF1_GROUND_DEBOUNCE_SAMPLES
    );
    app->ready = app->driver_status == GROUND_SENSORS_RESULT_OK ? 1u : 0u;
}

static void service_sample(GroundSensorsBringupApp *app) {
    if (app->ready == 0u) {
        return;
    }
    GroundSensorsRawLevels levels = openrf1_ground_read_levels();
    app->driver_status = ground_sensors_update_sample(&app->sensors, &levels);
    if (app->driver_status != GROUND_SENSORS_RESULT_OK) {
        app->ready = 0u;
    }
}

static void emit_identity_or_error(GroundSensorsBringupApp *app, uint32_t now_ms) {
    GroundSensorsTelemetryStatus status;
    if (app->ready != 0u) {
        status = ground_sensors_format_identity(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms
        );
    } else {
        status = ground_sensors_format_error(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms,
            app->driver_status,
            "initialize"
        );
    }
    emit_line(status, app);
}

static void emit_sample_or_error(GroundSensorsBringupApp *app, uint32_t now_ms) {
    GroundSensorsTelemetryStatus status;
    if (app->ready != 0u) {
        status = ground_sensors_format_sample(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms,
            &app->sensors
        );
    } else {
        status = ground_sensors_format_error(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms,
            app->driver_status,
            "sample"
        );
    }
    emit_line(status, app);
}

static void emit_line(GroundSensorsTelemetryStatus status, GroundSensorsBringupApp *app) {
    if (status == GROUND_SENSORS_TELEMETRY_OK) {
        openrf1_ground_debug_write_bounded(g_telemetry_buffer, OPENRF1_GROUND_TELEMETRY_BUFFER_BYTES);
        ++app->sequence;
    }
}
