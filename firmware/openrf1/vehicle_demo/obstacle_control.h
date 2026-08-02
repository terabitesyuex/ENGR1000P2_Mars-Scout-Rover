#pragma once

#include <stdint.h>

typedef enum {
    DEMO_SENSOR_OK = 0,
    DEMO_SENSOR_ECHO_NOT_LOW,
    DEMO_SENSOR_RISE_TIMEOUT,
    DEMO_SENSOR_FALL_TIMEOUT,
    DEMO_SENSOR_PULSE_OUT_OF_BOUNDS,
    DEMO_SENSOR_NOT_READY
} DemoSensorStatus;

typedef struct {
    DemoSensorStatus status;
    uint16_t distance_mm;
    uint32_t updated_ms;
} DemoObstacleSample;

typedef enum {
    DEMO_CONTROL_DISARMED = 0,
    DEMO_CONTROL_READY,
    DEMO_CONTROL_FORWARD,
    DEMO_CONTROL_STOP_CHECK,
    DEMO_CONTROL_TURN_RIGHT,
    DEMO_CONTROL_TURN_LEFT,
    DEMO_CONTROL_TURN_SETTLE,
    DEMO_CONTROL_SENSOR_FAULT,
    DEMO_CONTROL_WATCHDOG_FAULT
} DemoControlState;

typedef enum {
    DEMO_MOTION_STOP = 0,
    DEMO_MOTION_FORWARD,
    DEMO_MOTION_TURN_RIGHT,
    DEMO_MOTION_TURN_LEFT
} DemoMotion;

typedef enum {
    DEMO_COMMAND_ARM = 0,
    DEMO_COMMAND_START,
    DEMO_COMMAND_HEARTBEAT,
    DEMO_COMMAND_STOP
} DemoCommand;

typedef struct {
    DemoControlState state;
    DemoMotion motion;
    uint32_t state_deadline_ms;
    uint32_t last_heartbeat_ms;
    uint32_t last_sample_evaluation_ms;
    uint8_t hazard_count;
    uint8_t armed;
} DemoObstacleController;

void demo_obstacle_control_init(DemoObstacleController *controller);
uint8_t demo_obstacle_command(
    DemoObstacleController *controller,
    DemoCommand command,
    const DemoObstacleSample samples[3],
    uint32_t now_ms
);
void demo_obstacle_update(
    DemoObstacleController *controller,
    const DemoObstacleSample samples[3],
    uint32_t now_ms
);
const char *demo_control_state_name(DemoControlState state);
const char *demo_motion_name(DemoMotion motion);
