#include "obstacle_control.h"

#include "demo_config.h"

static uint8_t time_reached(uint32_t now_ms, uint32_t deadline_ms) {
    return (uint8_t)((int32_t)(now_ms - deadline_ms) >= 0);
}

static uint8_t sample_is_current(const DemoObstacleSample *sample, uint32_t now_ms) {
    return (uint8_t)(
        sample != 0 &&
        sample->status == DEMO_SENSOR_OK &&
        (uint32_t)(now_ms - sample->updated_ms) <= OPENRF1_DEMO_SENSOR_MAX_AGE_MS
    );
}

static uint8_t all_samples_current(const DemoObstacleSample samples[3], uint32_t now_ms) {
    uint8_t index;
    if (samples == 0) {
        return 0u;
    }
    for (index = 0u; index < 3u; ++index) {
        if (sample_is_current(&samples[index], now_ms) == 0u) {
            return 0u;
        }
    }
    return 1u;
}

static uint8_t sample_is_hazard(const DemoObstacleSample samples[3], uint8_t index) {
    uint16_t threshold_mm = index == 1u ?
        OPENRF1_DEMO_FRONT_STOP_MM : OPENRF1_DEMO_SIDE_STOP_MM;
    return (uint8_t)(samples[index].distance_mm < threshold_mm);
}

static uint8_t any_hazard(const DemoObstacleSample samples[3]) {
    return (uint8_t)(
        sample_is_hazard(samples, 0u) != 0u ||
        sample_is_hazard(samples, 1u) != 0u ||
        sample_is_hazard(samples, 2u) != 0u
    );
}

static uint32_t newest_sample_ms(const DemoObstacleSample samples[3]) {
    uint32_t newest_ms = samples[0].updated_ms;
    if (samples[1].updated_ms > newest_ms) {
        newest_ms = samples[1].updated_ms;
    }
    if (samples[2].updated_ms > newest_ms) {
        newest_ms = samples[2].updated_ms;
    }
    return newest_ms;
}

static void enter_state(
    DemoObstacleController *controller,
    DemoControlState state,
    uint32_t now_ms
) {
    controller->state = state;
    controller->motion = DEMO_MOTION_STOP;
    controller->state_deadline_ms = now_ms;

    if (state == DEMO_CONTROL_FORWARD) {
        controller->motion = DEMO_MOTION_FORWARD;
    } else if (state == DEMO_CONTROL_STOP_CHECK) {
        controller->state_deadline_ms = now_ms + OPENRF1_DEMO_STOP_CHECK_MS;
    } else if (state == DEMO_CONTROL_TURN_RIGHT) {
        controller->motion = DEMO_MOTION_TURN_RIGHT;
        controller->state_deadline_ms = now_ms + OPENRF1_DEMO_TURN_RIGHT_MS;
    } else if (state == DEMO_CONTROL_TURN_LEFT) {
        controller->motion = DEMO_MOTION_TURN_LEFT;
        controller->state_deadline_ms = now_ms + OPENRF1_DEMO_TURN_LEFT_MS;
    } else if (state == DEMO_CONTROL_TURN_SETTLE) {
        controller->state_deadline_ms = now_ms + OPENRF1_DEMO_TURN_SETTLE_MS;
    }
}

static void enter_sensor_fault(DemoObstacleController *controller, uint32_t now_ms) {
    controller->armed = 0u;
    controller->hazard_count = 0u;
    enter_state(controller, DEMO_CONTROL_SENSOR_FAULT, now_ms);
}

void demo_obstacle_control_init(DemoObstacleController *controller) {
    if (controller == 0) {
        return;
    }
    controller->armed = 0u;
    controller->hazard_count = 0u;
    controller->last_heartbeat_ms = 0u;
    controller->last_sample_evaluation_ms = 0u;
    enter_state(controller, DEMO_CONTROL_DISARMED, 0u);
}

uint8_t demo_obstacle_command(
    DemoObstacleController *controller,
    DemoCommand command,
    const DemoObstacleSample samples[3],
    uint32_t now_ms
) {
    if (controller == 0) {
        return 0u;
    }
    if (command == DEMO_COMMAND_STOP) {
        controller->armed = 0u;
        controller->hazard_count = 0u;
        enter_state(controller, DEMO_CONTROL_DISARMED, now_ms);
        return 1u;
    }
    if (command == DEMO_COMMAND_HEARTBEAT) {
        if (controller->armed == 0u) {
            return 0u;
        }
        controller->last_heartbeat_ms = now_ms;
        return 1u;
    }
    if (all_samples_current(samples, now_ms) == 0u) {
        enter_sensor_fault(controller, now_ms);
        return 0u;
    }
    if (command == DEMO_COMMAND_ARM) {
        controller->armed = 1u;
        controller->last_heartbeat_ms = now_ms;
        controller->last_sample_evaluation_ms = now_ms;
        controller->hazard_count = 0u;
        enter_state(controller, DEMO_CONTROL_READY, now_ms);
        return 1u;
    }
    if (command == DEMO_COMMAND_START && controller->armed != 0u) {
        if (any_hazard(samples) != 0u) {
            controller->hazard_count = 0u;
            enter_state(controller, DEMO_CONTROL_READY, now_ms);
            return 0u;
        }
        controller->last_heartbeat_ms = now_ms;
        controller->hazard_count = 0u;
        enter_state(controller, DEMO_CONTROL_FORWARD, now_ms);
        return 1u;
    }
    return 0u;
}

static void choose_turn(
    DemoObstacleController *controller,
    const DemoObstacleSample samples[3],
    uint32_t now_ms
) {
    uint8_t left_hazard = sample_is_hazard(samples, 0u);
    uint8_t center_hazard = sample_is_hazard(samples, 1u);
    uint8_t right_hazard = sample_is_hazard(samples, 2u);

    if (any_hazard(samples) == 0u) {
        controller->hazard_count = 0u;
        enter_state(controller, DEMO_CONTROL_FORWARD, now_ms);
    } else if (center_hazard != 0u) {
        enter_state(
            controller,
            samples[2].distance_mm > samples[0].distance_mm ?
                DEMO_CONTROL_TURN_RIGHT : DEMO_CONTROL_TURN_LEFT,
            now_ms
        );
    } else if (left_hazard != 0u && right_hazard == 0u) {
        enter_state(controller, DEMO_CONTROL_TURN_RIGHT, now_ms);
    } else if (right_hazard != 0u && left_hazard == 0u) {
        enter_state(controller, DEMO_CONTROL_TURN_LEFT, now_ms);
    } else {
        enter_state(
            controller,
            samples[2].distance_mm > samples[0].distance_mm ?
                DEMO_CONTROL_TURN_RIGHT : DEMO_CONTROL_TURN_LEFT,
            now_ms
        );
    }
}

void demo_obstacle_update(
    DemoObstacleController *controller,
    const DemoObstacleSample samples[3],
    uint32_t now_ms
) {
    if (controller == 0) {
        return;
    }
    if (controller->armed == 0u) {
        controller->motion = DEMO_MOTION_STOP;
        return;
    }
    if ((uint32_t)(now_ms - controller->last_heartbeat_ms) >=
        OPENRF1_DEMO_COMMAND_WATCHDOG_MS) {
        controller->armed = 0u;
        controller->hazard_count = 0u;
        enter_state(controller, DEMO_CONTROL_WATCHDOG_FAULT, now_ms);
        return;
    }
    if (all_samples_current(samples, now_ms) == 0u) {
        enter_sensor_fault(controller, now_ms);
        return;
    }

    switch (controller->state) {
        case DEMO_CONTROL_FORWARD:
            if (newest_sample_ms(samples) == controller->last_sample_evaluation_ms) {
                break;
            }
            controller->last_sample_evaluation_ms = newest_sample_ms(samples);
            if (any_hazard(samples) != 0u) {
                if (controller->hazard_count < OPENRF1_DEMO_HAZARD_CONFIRM_COUNT) {
                    ++controller->hazard_count;
                }
                if (controller->hazard_count >= OPENRF1_DEMO_HAZARD_CONFIRM_COUNT) {
                    enter_state(controller, DEMO_CONTROL_STOP_CHECK, now_ms);
                }
            } else {
                controller->hazard_count = 0u;
                controller->motion = DEMO_MOTION_FORWARD;
            }
            break;
        case DEMO_CONTROL_STOP_CHECK:
            controller->motion = DEMO_MOTION_STOP;
            if (time_reached(now_ms, controller->state_deadline_ms) != 0u) {
                choose_turn(controller, samples, now_ms);
            }
            break;
        case DEMO_CONTROL_TURN_RIGHT:
        case DEMO_CONTROL_TURN_LEFT:
            if (time_reached(now_ms, controller->state_deadline_ms) != 0u) {
                enter_state(controller, DEMO_CONTROL_TURN_SETTLE, now_ms);
            }
            break;
        case DEMO_CONTROL_TURN_SETTLE:
            controller->motion = DEMO_MOTION_STOP;
            if (time_reached(now_ms, controller->state_deadline_ms) != 0u) {
                choose_turn(controller, samples, now_ms);
            }
            break;
        case DEMO_CONTROL_READY:
        case DEMO_CONTROL_DISARMED:
        case DEMO_CONTROL_SENSOR_FAULT:
        case DEMO_CONTROL_WATCHDOG_FAULT:
        default:
            controller->motion = DEMO_MOTION_STOP;
            break;
    }
}

const char *demo_control_state_name(DemoControlState state) {
    static const char *const names[] = {
        "disarmed", "ready", "forward", "stop_check", "turn_right",
        "turn_left", "turn_settle", "sensor_fault", "watchdog_fault"
    };
    return (unsigned int)state < (sizeof(names) / sizeof(names[0])) ?
        names[state] : "internal_fault";
}

const char *demo_motion_name(DemoMotion motion) {
    static const char *const names[] = {"stop", "forward", "turn_right", "turn_left"};
    return (unsigned int)motion < (sizeof(names) / sizeof(names[0])) ?
        names[motion] : "stop";
}
