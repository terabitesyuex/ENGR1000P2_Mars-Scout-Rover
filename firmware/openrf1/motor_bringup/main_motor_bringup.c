#include "board_config.h"
#include "motor_control.h"
#include "platform_motor_bringup.h"

#include "encoder_input.h"

#include <stdio.h>

static MotorBringupControl g_control;
static DemoEncoderInput g_encoders;
static uint16_t g_raw_counts[DEMO_ENCODER_CHANNEL_COUNT];
static char g_command[OPENRF1_MOTOR_BRINGUP_COMMAND_BUFFER_BYTES];
static char g_telemetry[OPENRF1_MOTOR_BRINGUP_TELEMETRY_BUFFER_BYTES];
static uint32_t g_sequence;
static uint32_t g_last_status_ms;

static uint8_t strings_equal(const char *left, const char *right) {
    while (*left != '\0' && *right != '\0') {
        if (*left != *right) {
            return 0u;
        }
        ++left;
        ++right;
    }
    return *left == *right ? 1u : 0u;
}

static const char *state_name(MotorBringupState state) {
    switch (state) {
        case MOTOR_BRINGUP_UNCONFIGURED:
            return "unconfigured";
        case MOTOR_BRINGUP_DISARMED:
            return "disarmed";
        case MOTOR_BRINGUP_ARMED:
            return "armed";
        case MOTOR_BRINGUP_RUNNING:
            return "running";
        default:
            return "fault";
    }
}

static void force_safe_stop(void) {
    motor_bringup_stop(&g_control);
    openrf1_motor_stop_all();
}

static uint8_t sync_output(void) {
    if (g_control.output_active == 0u) {
        openrf1_motor_stop_all();
        return 1u;
    }
    if (openrf1_motor_apply(
            g_control.config.connector,
            g_control.electrical_direction,
            g_control.applied_duty_permille
        ) == 0u) {
        force_safe_stop();
        return 0u;
    }
    return 1u;
}

static uint8_t emit_identity(uint32_t now_ms) {
    int written = snprintf(
        g_telemetry,
        sizeof(g_telemetry),
        "{\"sequence\":%lu,\"timestamp_ms\":%lu,"
        "\"message_type\":\"motor_bringup_identity\","
        "\"status\":\"software_ready\",\"payload\":{"
        "\"target\":\"OpenRF1_Motor_Bringup\",\"board\":\"%s\","
        "\"mapping_status\":\"%s\",\"default_state\":\"unconfigured\","
        "\"motor_outputs_enabled_at_startup\":false,"
        "\"user_duty_limit_required\":true,"
        "\"user_direction_signs_required\":true}}\r\n",
        (unsigned long)g_sequence,
        (unsigned long)now_ms,
        OPENRF1_MOTOR_BRINGUP_BOARD,
        OPENRF1_MOTOR_BRINGUP_MAPPING_STATUS
    );
    if (written <= 0 || written >= (int)sizeof(g_telemetry) ||
        openrf1_motor_console_write(g_telemetry) == 0u) {
        return 0u;
    }
    ++g_sequence;
    return 1u;
}

static uint8_t emit_status(uint32_t now_ms) {
    int32_t selected_delta = 0;
    int written;
    openrf1_motor_read_encoder_raw(g_raw_counts);
    (void)demo_encoder_input_update(&g_encoders, g_raw_counts, now_ms);
    if (g_control.config.valid != 0u) {
        selected_delta =
            g_encoders.channels[g_control.config.connector - 1u].delta_count *
            (int32_t)g_control.config.encoder_sign;
    }
    written = snprintf(
        g_telemetry,
        sizeof(g_telemetry),
        "{\"sequence\":%lu,\"timestamp_ms\":%lu,"
        "\"message_type\":\"motor_bringup_status\",\"status\":\"%s\","
        "\"payload\":{\"mapping_status\":\"%s\","
        "\"config_valid\":%s,\"selected_connector\":%u,"
        "\"motor_sign\":%d,\"encoder_sign\":%d,"
        "\"configured_max_duty_permille\":%u,\"watchdog_ms\":%lu,"
        "\"output_active\":%s,\"requested_direction\":%d,"
        "\"electrical_direction\":%d,\"applied_duty_permille\":%u,"
        "\"cn1_raw_count\":%u,\"cn2_raw_count\":%u,"
        "\"cn3_raw_count\":%u,\"cn4_raw_count\":%u,"
        "\"selected_signed_delta_count\":%ld}}\r\n",
        (unsigned long)g_sequence,
        (unsigned long)now_ms,
        state_name(g_control.state),
        OPENRF1_MOTOR_BRINGUP_MAPPING_STATUS,
        g_control.config.valid != 0u ? "true" : "false",
        (unsigned int)g_control.config.connector,
        (int)g_control.config.motor_sign,
        (int)g_control.config.encoder_sign,
        (unsigned int)g_control.config.max_duty_permille,
        (unsigned long)g_control.config.watchdog_ms,
        g_control.output_active != 0u ? "true" : "false",
        (int)g_control.requested_direction,
        (int)g_control.electrical_direction,
        (unsigned int)g_control.applied_duty_permille,
        (unsigned int)g_raw_counts[0],
        (unsigned int)g_raw_counts[1],
        (unsigned int)g_raw_counts[2],
        (unsigned int)g_raw_counts[3],
        (long)selected_delta
    );
    if (written <= 0 || written >= (int)sizeof(g_telemetry) ||
        openrf1_motor_console_write(g_telemetry) == 0u) {
        return 0u;
    }
    ++g_sequence;
    return 1u;
}

static uint8_t handle_command(const char *command, uint32_t now_ms) {
    unsigned int connector;
    int motor_sign;
    int encoder_sign;
    unsigned int max_duty;
    unsigned long watchdog_ms;
    int requested_direction;
    unsigned int duty;
    char extra;

    if (sscanf(
            command,
            "CONFIG %u %d %d %u %lu %c",
            &connector,
            &motor_sign,
            &encoder_sign,
            &max_duty,
            &watchdog_ms,
            &extra
        ) == 5) {
        if (connector < 1u || connector > 4u ||
            (motor_sign != -1 && motor_sign != 1) ||
            (encoder_sign != -1 && encoder_sign != 1) ||
            max_duty == 0u ||
            max_duty > OPENRF1_MOTOR_BRINGUP_DUTY_REPRESENTATION_MAX ||
            watchdog_ms == 0u ||
            watchdog_ms >
                OPENRF1_MOTOR_BRINGUP_WATCHDOG_REPRESENTATION_MAX_MS) {
            return 0u;
        }
        return motor_bringup_configure(
            &g_control,
            (uint8_t)connector,
            (int8_t)motor_sign,
            (int8_t)encoder_sign,
            (uint16_t)max_duty,
            (uint32_t)watchdog_ms,
            now_ms
        );
    }
    if (sscanf(command, "RUN %d %u %c", &requested_direction, &duty, &extra) == 2) {
        if ((requested_direction != -1 && requested_direction != 1) ||
            duty == 0u ||
            duty > OPENRF1_MOTOR_BRINGUP_DUTY_REPRESENTATION_MAX) {
            return 0u;
        }
        return motor_bringup_run(
            &g_control,
            (int8_t)requested_direction,
            (uint16_t)duty,
            now_ms
        );
    }
    if (strings_equal(command, "ARM") != 0u) {
        return motor_bringup_arm(&g_control, now_ms);
    }
    if (strings_equal(command, "HEARTBEAT") != 0u) {
        return motor_bringup_heartbeat(&g_control, now_ms);
    }
    if (strings_equal(command, "STOP") != 0u ||
        strings_equal(command, "DISARM") != 0u) {
        motor_bringup_stop(&g_control);
        return 1u;
    }
    if (strings_equal(command, "RESET") != 0u) {
        motor_bringup_reset(&g_control);
        return 1u;
    }
    return 0u;
}

int main(void) {
    uint32_t now_ms;
    motor_bringup_init(&g_control);
    if (openrf1_motor_platform_init() == 0u) {
        openrf1_motor_stop_all();
        for (;;) {
        }
    }
    now_ms = openrf1_motor_millis();
    openrf1_motor_read_encoder_raw(g_raw_counts);
    demo_encoder_input_init(&g_encoders, g_raw_counts, now_ms);
    g_sequence = 0u;
    g_last_status_ms = now_ms;
    if (emit_identity(now_ms) == 0u) {
        force_safe_stop();
    }

    for (;;) {
        MotorConsoleReadResult read_result;
        now_ms = openrf1_motor_millis();
        if (motor_bringup_service(&g_control, now_ms) == 0u &&
            g_control.state == MOTOR_BRINGUP_FAULT) {
            openrf1_motor_stop_all();
        }
        read_result = openrf1_motor_console_read_line(
            g_command,
            sizeof(g_command)
        );
        if (read_result == MOTOR_CONSOLE_FAULT) {
            force_safe_stop();
        } else if (read_result == MOTOR_CONSOLE_LINE_READY) {
            if (handle_command(g_command, now_ms) == 0u ||
                sync_output() == 0u) {
                force_safe_stop();
            }
        }
        if ((uint32_t)(now_ms - g_last_status_ms) >=
            OPENRF1_MOTOR_BRINGUP_STATUS_PERIOD_MS) {
            g_last_status_ms = now_ms;
            if (emit_status(now_ms) == 0u) {
                force_safe_stop();
            }
        }
    }
}
