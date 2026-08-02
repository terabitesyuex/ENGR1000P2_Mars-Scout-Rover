#include <stdint.h>
#include <stdio.h>

#include "demo_config.h"
#include "encoder_input.h"
#include "hall_input.h"
#include "obstacle_control.h"
#include "platform_vehicle_demo.h"
#include "ultrasonic_array.h"

static DemoObstacleController g_controller;
static DemoUltrasonicArray g_ultrasonic;
static DemoHallInput g_hall;
static DemoEncoderInput g_encoders;
static DemoObstacleSample g_samples[3];
static uint16_t g_encoder_raw_counts[DEMO_ENCODER_CHANNEL_COUNT];
static char g_command[OPENRF1_DEMO_COMMAND_BUFFER_BYTES];
static char g_telemetry[OPENRF1_DEMO_TELEMETRY_BUFFER_BYTES];
static uint32_t g_sequence;
static uint32_t g_last_status_ms;
static uint32_t g_next_hall_sample_ms;
static uint32_t g_next_encoder_sample_ms;
static uint32_t g_encoder_telemetry_drop_count;
static DemoMotion g_applied_motion;

static void format_distance(
    char output[6],
    const DemoObstacleSample *sample
) {
    if (sample->status != DEMO_SENSOR_OK) {
        (void)snprintf(output, 6u, "null");
    } else {
        (void)snprintf(output, 6u, "%u", (unsigned int)sample->distance_mm);
    }
}

static uint8_t strings_equal(const char *left, const char *right) {
    if (left == 0 || right == 0) {
        return 0u;
    }
    while (*left != '\0' && *right != '\0') {
        if (*left != *right) {
            return 0u;
        }
        ++left;
        ++right;
    }
    return (uint8_t)(*left == '\0' && *right == '\0');
}

static uint8_t emit_identity(uint32_t now_ms) {
    int written = snprintf(
        g_telemetry,
        sizeof(g_telemetry),
        "{\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"vehicle_demo_identity\"," 
        "\"status\":\"software_ready\",\"payload\":{\"pin_profile\":\"%s\"," 
        "\"left\":\"%s/%s\",\"center\":\"%s/%s\",\"right\":\"%s/%s\"," 
        "\"hall_pin\":\"%s\",\"hall_sample_period_ms\":%lu,"
        "\"encoder_mapping\":\"%s\",\"encoder_counter_bits\":%u,"
        "\"encoder_sample_period_ms\":%lu,"
        "\"timer\":\"TIM6_1MHz_extended\",\"motor_pwm\":\"TIM8\"," 
        "\"command_watchdog_ms\":%lu}}\r\n",
        (unsigned long)g_sequence,
        (unsigned long)now_ms,
        OPENRF1_DEMO_PIN_PROFILE,
        OPENRF1_DEMO_US_LEFT_TRIGGER_PIN,
        OPENRF1_DEMO_US_LEFT_ECHO_PIN,
        OPENRF1_DEMO_US_CENTER_TRIGGER_PIN,
        OPENRF1_DEMO_US_CENTER_ECHO_PIN,
        OPENRF1_DEMO_US_RIGHT_TRIGGER_PIN,
        OPENRF1_DEMO_US_RIGHT_ECHO_PIN,
        OPENRF1_DEMO_HALL_PIN,
        (unsigned long)OPENRF1_DEMO_HALL_SAMPLE_PERIOD_MS,
        OPENRF1_DEMO_ENCODER_MAPPING_STATUS,
        (unsigned int)OPENRF1_DEMO_ENCODER_COUNTER_BITS,
        (unsigned long)OPENRF1_DEMO_ENCODER_SAMPLE_PERIOD_MS,
        (unsigned long)OPENRF1_DEMO_COMMAND_WATCHDOG_MS
    );
    if (written <= 0 || written >= (int)sizeof(g_telemetry)) {
        return 0u;
    }
    ++g_sequence;
    return demo_platform_console_write(g_telemetry);
}

static uint8_t emit_status(uint32_t now_ms) {
    char left_distance[6];
    char center_distance[6];
    char right_distance[6];
    format_distance(left_distance, &g_samples[0]);
    format_distance(center_distance, &g_samples[1]);
    format_distance(right_distance, &g_samples[2]);
    int written = snprintf(
        g_telemetry,
        sizeof(g_telemetry),
        "{\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"vehicle_demo_status\"," 
        "\"status\":\"%s\",\"payload\":{\"control_state\":\"%s\"," 
        "\"motion\":\"%s\",\"armed\":%s,\"left_distance_mm\":%s," 
        "\"center_distance_mm\":%s,\"right_distance_mm\":%s," 
        "\"left_sensor_status\":\"%s\",\"center_sensor_status\":\"%s\"," 
        "\"right_sensor_status\":\"%s\",\"hall_raw_level\":%u,"
        "\"hall_debounced_level\":%u,\"hall_baseline_ready\":%s,"
        "\"hall_baseline_level\":%u,\"hall_landmark_active\":%s,"
        "\"hall_landmark_count\":%lu,\"encoder_sample_valid\":%s,"
        "\"encoder_count_range_error\":%s,"
        "\"encoder_telemetry_drop_count\":%lu}}\r\n",
        (unsigned long)g_sequence,
        (unsigned long)now_ms,
        g_controller.state == DEMO_CONTROL_SENSOR_FAULT ||
        g_controller.state == DEMO_CONTROL_WATCHDOG_FAULT ? "error" : "ok",
        demo_control_state_name(g_controller.state),
        demo_motion_name(g_controller.motion),
        g_controller.armed != 0u ? "true" : "false",
        left_distance,
        center_distance,
        right_distance,
        demo_sensor_status_name(g_samples[0].status),
        demo_sensor_status_name(g_samples[1].status),
        demo_sensor_status_name(g_samples[2].status),
        (unsigned int)g_hall.raw_level,
        (unsigned int)g_hall.debounced_level,
        g_hall.baseline_ready != 0u ? "true" : "false",
        (unsigned int)g_hall.baseline_level,
        g_hall.landmark_active != 0u ? "true" : "false",
        (unsigned long)g_hall.landmark_count,
        g_encoders.sample_valid != 0u ? "true" : "false",
        g_encoders.count_range_error != 0u ? "true" : "false",
        (unsigned long)g_encoder_telemetry_drop_count
    );
    if (written <= 0 || written >= (int)sizeof(g_telemetry)) {
        return 0u;
    }
    ++g_sequence;
    return demo_platform_console_write(g_telemetry);
}

static uint8_t emit_encoder_sample(void) {
    const DemoEncoderChannel *cn1 = &g_encoders.channels[DEMO_ENCODER_CN1];
    const DemoEncoderChannel *cn2 = &g_encoders.channels[DEMO_ENCODER_CN2];
    const DemoEncoderChannel *cn3 = &g_encoders.channels[DEMO_ENCODER_CN3];
    const DemoEncoderChannel *cn4 = &g_encoders.channels[DEMO_ENCODER_CN4];
    int written = snprintf(
        g_telemetry,
        sizeof(g_telemetry),
        "{\"sequence\":%lu,\"timestamp_ms\":%lu,"
        "\"message_type\":\"vehicle_demo_encoder\",\"status\":\"raw_counts\","
        "\"payload\":{\"mapping_status\":\"%s\",\"counter_bits\":%u,"
        "\"interval_ms\":%lu,\"direction_signs_verified\":false,"
        "\"cn1_raw_count\":%u,\"cn1_delta_count\":%ld,\"cn1_cumulative_count\":%ld,"
        "\"cn2_raw_count\":%u,\"cn2_delta_count\":%ld,\"cn2_cumulative_count\":%ld,"
        "\"cn3_raw_count\":%u,\"cn3_delta_count\":%ld,\"cn3_cumulative_count\":%ld,"
        "\"cn4_raw_count\":%u,\"cn4_delta_count\":%ld,\"cn4_cumulative_count\":%ld}}\r\n",
        (unsigned long)g_sequence,
        (unsigned long)g_encoders.timestamp_ms,
        OPENRF1_DEMO_ENCODER_MAPPING_STATUS,
        (unsigned int)OPENRF1_DEMO_ENCODER_COUNTER_BITS,
        (unsigned long)g_encoders.interval_ms,
        (unsigned int)cn1->raw_count,
        (long)cn1->delta_count,
        (long)cn1->cumulative_count,
        (unsigned int)cn2->raw_count,
        (long)cn2->delta_count,
        (long)cn2->cumulative_count,
        (unsigned int)cn3->raw_count,
        (long)cn3->delta_count,
        (long)cn3->cumulative_count,
        (unsigned int)cn4->raw_count,
        (long)cn4->delta_count,
        (long)cn4->cumulative_count
    );
    if (written <= 0 || written >= (int)sizeof(g_telemetry)) {
        return 0u;
    }
    if (demo_platform_console_write(g_telemetry) == 0u) {
        return 0u;
    }
    ++g_sequence;
    return 1u;
}

static uint8_t emit_hall_event(void) {
    int written = snprintf(
        g_telemetry,
        sizeof(g_telemetry),
        "{\"sequence\":%lu,\"timestamp_ms\":%lu,"
        "\"message_type\":\"vehicle_demo_hall_event\",\"status\":\"ok\","
        "\"payload\":{\"landmark_index\":%lu,\"baseline_level\":%u,"
        "\"trigger_level\":%u,\"baseline_inferred\":true}}\r\n",
        (unsigned long)g_sequence,
        (unsigned long)g_hall.last_landmark_timestamp_ms,
        (unsigned long)g_hall.landmark_count,
        (unsigned int)g_hall.baseline_level,
        (unsigned int)g_hall.debounced_level
    );
    if (written <= 0 || written >= (int)sizeof(g_telemetry)) {
        return 0u;
    }
    if (demo_platform_console_write(g_telemetry) == 0u) {
        return 0u;
    }
    ++g_sequence;
    demo_hall_input_clear_pending_event(&g_hall);
    return 1u;
}

static uint8_t emit_motor_diagnostics(uint32_t now_ms) {
    DemoMotorDiagnostics diagnostics;
    int written;

    demo_platform_read_motor_diagnostics(&diagnostics);
    written = snprintf(
        g_telemetry,
        sizeof(g_telemetry),
        "{\"sequence\":%lu,\"timestamp_ms\":%lu,\"message_type\":\"vehicle_demo_motor_diag\","
        "\"status\":\"ok\",\"payload\":{\"ccr1\":%u,\"ccr2\":%u,\"ccr3\":%u,\"ccr4\":%u,"
        "\"tim8_cr1\":%lu,\"tim8_ccer\":%lu,\"tim8_bdtr\":%lu,\"gpio_c_crl\":%lu,"
        "\"gpio_c_crh\":%lu,\"afio_mapr\":%lu}}\r\n",
        (unsigned long)g_sequence,
        (unsigned long)now_ms,
        (unsigned int)diagnostics.ccr1,
        (unsigned int)diagnostics.ccr2,
        (unsigned int)diagnostics.ccr3,
        (unsigned int)diagnostics.ccr4,
        (unsigned long)diagnostics.timer_cr1,
        (unsigned long)diagnostics.timer_ccer,
        (unsigned long)diagnostics.timer_bdtr,
        (unsigned long)diagnostics.gpio_c_crl,
        (unsigned long)diagnostics.gpio_c_crh,
        (unsigned long)diagnostics.afio_mapr
    );
    if (written <= 0 || written >= (int)sizeof(g_telemetry)) {
        return 0u;
    }
    ++g_sequence;
    return demo_platform_console_write(g_telemetry);
}

static void force_safe_stop(uint32_t now_ms) {
    (void)demo_obstacle_command(
        &g_controller,
        DEMO_COMMAND_STOP,
        g_samples,
        now_ms
    );
    demo_platform_stop_all();
    g_applied_motion = DEMO_MOTION_STOP;
}

static void handle_command(const char *command, uint32_t now_ms) {
    DemoCommand parsed;
    if (strings_equal(command, "STOP") != 0u ||
        strings_equal(command, "DISARM") != 0u) {
        parsed = DEMO_COMMAND_STOP;
    } else if (strings_equal(command, "ARM") != 0u) {
        parsed = DEMO_COMMAND_ARM;
    } else if (strings_equal(command, "START") != 0u) {
        parsed = DEMO_COMMAND_START;
    } else if (strings_equal(command, "HEARTBEAT") != 0u) {
        parsed = DEMO_COMMAND_HEARTBEAT;
    } else if (strings_equal(command, "MOTOR_DIAG") != 0u) {
        (void)emit_motor_diagnostics(now_ms);
        return;
    } else {
        force_safe_stop(now_ms);
        return;
    }
    (void)demo_obstacle_command(&g_controller, parsed, g_samples, now_ms);
}

int main(void) {
    DemoUltrasonicHardware ultrasonic_hardware;

    demo_obstacle_control_init(&g_controller);
    if (demo_platform_init() == 0u) {
        demo_platform_stop_all();
        for (;;) {
        }
    }

    ultrasonic_hardware.trigger_write = demo_platform_trigger_write;
    ultrasonic_hardware.echo_read = demo_platform_echo_read;
    if (demo_ultrasonic_array_init(
            &g_ultrasonic,
            &ultrasonic_hardware,
            demo_platform_micros()
        ) == 0u) {
        demo_platform_stop_all();
        for (;;) {
        }
    }
    demo_ultrasonic_copy_samples(&g_ultrasonic, g_samples);
    demo_hall_input_init(&g_hall, demo_platform_hall_read());
    demo_platform_encoder_read_raw(g_encoder_raw_counts);
    demo_encoder_input_init(
        &g_encoders,
        g_encoder_raw_counts,
        demo_platform_millis()
    );
    g_sequence = 0u;
    g_last_status_ms = demo_platform_millis();
    g_next_hall_sample_ms = g_last_status_ms + OPENRF1_DEMO_HALL_SAMPLE_PERIOD_MS;
    g_next_encoder_sample_ms =
        g_last_status_ms + OPENRF1_DEMO_ENCODER_SAMPLE_PERIOD_MS;
    g_encoder_telemetry_drop_count = 0u;
    g_applied_motion = DEMO_MOTION_STOP;
    if (emit_identity(g_last_status_ms) == 0u) {
        force_safe_stop(g_last_status_ms);
    }

    for (;;) {
        DemoConsoleReadResult read_result;
        uint32_t now_ms = demo_platform_millis();

        demo_ultrasonic_array_service(
            &g_ultrasonic,
            demo_platform_micros(),
            now_ms
        );
        demo_ultrasonic_copy_samples(&g_ultrasonic, g_samples);

        if ((int32_t)(now_ms - g_next_hall_sample_ms) >= 0) {
            /* Drop missed slots so scheduler delay cannot fake stable samples. */
            g_next_hall_sample_ms = now_ms + OPENRF1_DEMO_HALL_SAMPLE_PERIOD_MS;
            demo_hall_input_update(&g_hall, demo_platform_hall_read(), now_ms);
        }

        if (g_hall.event_pending != 0u) {
            (void)emit_hall_event();
        }

        if ((int32_t)(now_ms - g_next_encoder_sample_ms) >= 0) {
            g_next_encoder_sample_ms =
                now_ms + OPENRF1_DEMO_ENCODER_SAMPLE_PERIOD_MS;
            demo_platform_encoder_read_raw(g_encoder_raw_counts);
            if (demo_encoder_input_update(
                    &g_encoders,
                    g_encoder_raw_counts,
                    now_ms
                ) != 0u && emit_encoder_sample() == 0u) {
                ++g_encoder_telemetry_drop_count;
            }
        }

        read_result = demo_platform_console_read_line(g_command, sizeof(g_command));
        if (read_result == DEMO_CONSOLE_FAULT) {
            force_safe_stop(now_ms);
        } else if (read_result == DEMO_CONSOLE_LINE_READY) {
            handle_command(g_command, now_ms);
        }

        demo_obstacle_update(&g_controller, g_samples, now_ms);
        if (g_controller.motion != g_applied_motion) {
            demo_platform_set_motion(g_controller.motion);
            g_applied_motion = g_controller.motion;
        }

        if ((uint32_t)(now_ms - g_last_status_ms) >= OPENRF1_DEMO_STATUS_PERIOD_MS) {
            g_last_status_ms += OPENRF1_DEMO_STATUS_PERIOD_MS;
            if (emit_status(now_ms) == 0u) {
                force_safe_stop(now_ms);
            }
        }
    }
}
