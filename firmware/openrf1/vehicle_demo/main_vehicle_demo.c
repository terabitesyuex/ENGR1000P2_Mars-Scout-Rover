#include <stdint.h>
#include <stdio.h>

#include "demo_config.h"
#include "obstacle_control.h"
#include "platform_vehicle_demo.h"
#include "ultrasonic_array.h"

static DemoObstacleController g_controller;
static DemoUltrasonicArray g_ultrasonic;
static DemoObstacleSample g_samples[3];
static char g_command[OPENRF1_DEMO_COMMAND_BUFFER_BYTES];
static char g_telemetry[OPENRF1_DEMO_TELEMETRY_BUFFER_BYTES];
static uint32_t g_sequence;
static uint32_t g_last_status_ms;
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
        "\"right_sensor_status\":\"%s\"}}\r\n",
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
        demo_sensor_status_name(g_samples[2].status)
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
    g_sequence = 0u;
    g_last_status_ms = demo_platform_millis();
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
