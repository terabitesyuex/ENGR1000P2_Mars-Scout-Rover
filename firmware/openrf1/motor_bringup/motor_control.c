#include "motor_control.h"

#include "board_config.h"

static uint8_t sign_valid(int8_t sign) {
    return sign == -1 || sign == 1;
}

static void clear_output(MotorBringupControl *control) {
    control->requested_direction = 0;
    control->electrical_direction = 0;
    control->applied_duty_permille = 0u;
    control->output_active = 0u;
}

void motor_bringup_init(MotorBringupControl *control) {
    if (control == 0) {
        return;
    }
    control->config.connector = 0u;
    control->config.motor_sign = 0;
    control->config.encoder_sign = 0;
    control->config.max_duty_permille = 0u;
    control->config.watchdog_ms = 0u;
    control->config.valid = 0u;
    control->state = MOTOR_BRINGUP_UNCONFIGURED;
    control->last_heartbeat_ms = 0u;
    clear_output(control);
}

uint8_t motor_bringup_configure(
    MotorBringupControl *control,
    uint8_t connector,
    int8_t motor_sign,
    int8_t encoder_sign,
    uint16_t max_duty_permille,
    uint32_t watchdog_ms,
    uint32_t now_ms
) {
    if (control == 0 || connector < 1u || connector > 4u ||
        sign_valid(motor_sign) == 0u || sign_valid(encoder_sign) == 0u ||
        max_duty_permille == 0u ||
        max_duty_permille > OPENRF1_MOTOR_BRINGUP_DUTY_REPRESENTATION_MAX ||
        watchdog_ms == 0u ||
        watchdog_ms > OPENRF1_MOTOR_BRINGUP_WATCHDOG_REPRESENTATION_MAX_MS) {
        if (control != 0) {
            motor_bringup_init(control);
            control->state = MOTOR_BRINGUP_FAULT;
        }
        return 0u;
    }
    clear_output(control);
    control->config.connector = connector;
    control->config.motor_sign = motor_sign;
    control->config.encoder_sign = encoder_sign;
    control->config.max_duty_permille = max_duty_permille;
    control->config.watchdog_ms = watchdog_ms;
    control->config.valid = 1u;
    control->state = MOTOR_BRINGUP_DISARMED;
    control->last_heartbeat_ms = now_ms;
    return 1u;
}

uint8_t motor_bringup_arm(MotorBringupControl *control, uint32_t now_ms) {
    if (control == 0 || control->config.valid == 0u ||
        control->state != MOTOR_BRINGUP_DISARMED) {
        return 0u;
    }
    clear_output(control);
    control->state = MOTOR_BRINGUP_ARMED;
    control->last_heartbeat_ms = now_ms;
    return 1u;
}

uint8_t motor_bringup_run(
    MotorBringupControl *control,
    int8_t requested_direction,
    uint16_t duty_permille,
    uint32_t now_ms
) {
    if (control == 0 || control->config.valid == 0u ||
        (control->state != MOTOR_BRINGUP_ARMED &&
         control->state != MOTOR_BRINGUP_RUNNING) ||
        sign_valid(requested_direction) == 0u || duty_permille == 0u ||
        duty_permille > control->config.max_duty_permille) {
        if (control != 0) {
            clear_output(control);
            control->state = MOTOR_BRINGUP_FAULT;
        }
        return 0u;
    }
    control->requested_direction = requested_direction;
    control->electrical_direction =
        (int8_t)(requested_direction * control->config.motor_sign);
    control->applied_duty_permille = duty_permille;
    control->output_active = 1u;
    control->last_heartbeat_ms = now_ms;
    control->state = MOTOR_BRINGUP_RUNNING;
    return 1u;
}

uint8_t motor_bringup_heartbeat(MotorBringupControl *control, uint32_t now_ms) {
    if (control == 0 ||
        (control->state != MOTOR_BRINGUP_ARMED &&
         control->state != MOTOR_BRINGUP_RUNNING)) {
        return 0u;
    }
    control->last_heartbeat_ms = now_ms;
    return 1u;
}

void motor_bringup_stop(MotorBringupControl *control) {
    if (control == 0) {
        return;
    }
    clear_output(control);
    control->state = control->config.valid != 0u ?
        MOTOR_BRINGUP_DISARMED : MOTOR_BRINGUP_UNCONFIGURED;
}

void motor_bringup_reset(MotorBringupControl *control) {
    motor_bringup_init(control);
}

uint8_t motor_bringup_service(MotorBringupControl *control, uint32_t now_ms) {
    if (control == 0 || control->config.valid == 0u) {
        return 0u;
    }
    if ((control->state == MOTOR_BRINGUP_ARMED ||
         control->state == MOTOR_BRINGUP_RUNNING) &&
        (uint32_t)(now_ms - control->last_heartbeat_ms) >
            control->config.watchdog_ms) {
        clear_output(control);
        control->state = MOTOR_BRINGUP_FAULT;
        return 0u;
    }
    return 1u;
}
