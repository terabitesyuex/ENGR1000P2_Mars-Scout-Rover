#include "board_config.h"
#include "hcsr04.h"
#include "platform_hcsr04_bringup.h"
#include "telemetry_hcsr04_bringup.h"

#include "../full_hardware/openrf1_status.h"

typedef struct {
    Hcsr04Driver driver;
    OpenRf1Status platform_status;
    Hcsr04ResultCode driver_status;
    uint32_t sequence;
    uint32_t next_attempt_ms;
    uint8_t ready;
} Hcsr04BringupApp;

static char g_telemetry_buffer[OPENRF1_HCSR04_TELEMETRY_BUFFER_BYTES];

static void initialize_app(Hcsr04BringupApp *app);
static void emit_identity_or_error(Hcsr04BringupApp *app, uint32_t now_ms);
static void emit_measurement_attempt(Hcsr04BringupApp *app, uint32_t now_ms);
static void emit_line(Hcsr04BringupTelemetryStatus status, Hcsr04BringupApp *app, uint32_t now_ms);

int main(void) {
    Hcsr04BringupApp app = {0};
    initialize_app(&app);
    app.next_attempt_ms = openrf1_hcsr04_millis() + OPENRF1_HCSR04_MEASUREMENT_PERIOD_MS;
    emit_identity_or_error(&app, openrf1_hcsr04_millis());

    while (1) {
        uint32_t now_ms = openrf1_hcsr04_millis();
        if ((int32_t)(now_ms - app.next_attempt_ms) >= 0) {
            app.next_attempt_ms += OPENRF1_HCSR04_MEASUREMENT_PERIOD_MS;
            emit_measurement_attempt(&app, now_ms);
        }
    }
}

static void initialize_app(Hcsr04BringupApp *app) {
    static const Hcsr04Io io = {
        openrf1_hcsr04_trigger_write,
        openrf1_hcsr04_echo_read,
        openrf1_hcsr04_timer_now_us,
        openrf1_hcsr04_delay_us,
    };

    app->platform_status = openrf1_hcsr04_platform_init();
    if (app->platform_status != OPENRF1_STATUS_OK) {
        app->driver_status = HCSR04_RESULT_TIMER_CONFIGURATION_FAILURE;
        app->ready = 0u;
        return;
    }

    app->driver_status = hcsr04_driver_init(&app->driver, &io);
    app->ready = app->driver_status == HCSR04_RESULT_OK ? 1u : 0u;
}

static void emit_identity_or_error(Hcsr04BringupApp *app, uint32_t now_ms) {
    Hcsr04BringupTelemetryStatus status;
    if (app->ready != 0u) {
        status = hcsr04_bringup_format_identity(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms
        );
    } else {
        status = hcsr04_bringup_format_error(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms,
            app->driver_status
        );
    }
    emit_line(status, app, now_ms);
}

static void emit_measurement_attempt(Hcsr04BringupApp *app, uint32_t now_ms) {
    if (app->ready == 0u) {
        Hcsr04BringupTelemetryStatus status = hcsr04_bringup_format_error(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms,
            app->driver_status
        );
        emit_line(status, app, now_ms);
        return;
    }

    Hcsr04MeasurementResult measurement;
    Hcsr04ResultCode code = hcsr04_measure_once(&app->driver, &measurement);
    Hcsr04BringupTelemetryStatus format_status;
    if (code == HCSR04_RESULT_OK) {
        format_status = hcsr04_bringup_format_measurement(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms,
            &measurement
        );
    } else {
        format_status = hcsr04_bringup_format_error(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms,
            code
        );
    }
    emit_line(format_status, app, now_ms);
}

static void emit_line(Hcsr04BringupTelemetryStatus status, Hcsr04BringupApp *app, uint32_t now_ms) {
    if (status != HCSR04_BRINGUP_TELEMETRY_OK) {
        status = hcsr04_bringup_format_error(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->sequence,
            now_ms,
            HCSR04_RESULT_TELEMETRY_FORMAT_FAILURE
        );
    }
    if (status == HCSR04_BRINGUP_TELEMETRY_OK) {
        openrf1_hcsr04_debug_write_bounded(g_telemetry_buffer, OPENRF1_HCSR04_TELEMETRY_BUFFER_BYTES);
        ++app->sequence;
        return;
    }
    openrf1_hcsr04_debug_write_bounded(
        "HCSR04_TELEMETRY_FORMAT_FAILURE\n",
        (uint16_t)(sizeof("HCSR04_TELEMETRY_FORMAT_FAILURE\n") - 1u)
    );
    ++app->sequence;
}
