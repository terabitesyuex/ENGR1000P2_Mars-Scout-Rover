#pragma once

#include <stdint.h>

typedef enum {
    MOTOR_BRINGUP_UNCONFIGURED = 0,
    MOTOR_BRINGUP_DISARMED,
    MOTOR_BRINGUP_ARMED,
    MOTOR_BRINGUP_RUNNING,
    MOTOR_BRINGUP_FAULT
} MotorBringupState;

typedef struct {
    uint8_t connector;
    int8_t motor_sign;
    int8_t encoder_sign;
    uint16_t max_duty_permille;
    uint32_t watchdog_ms;
    uint8_t valid;
} MotorBringupConfig;

typedef struct {
    MotorBringupConfig config;
    MotorBringupState state;
    int8_t requested_direction;
    int8_t electrical_direction;
    uint16_t applied_duty_permille;
    uint32_t last_heartbeat_ms;
    uint8_t output_active;
} MotorBringupControl;

void motor_bringup_init(MotorBringupControl *control);
uint8_t motor_bringup_configure(
    MotorBringupControl *control,
    uint8_t connector,
    int8_t motor_sign,
    int8_t encoder_sign,
    uint16_t max_duty_permille,
    uint32_t watchdog_ms,
    uint32_t now_ms
);
uint8_t motor_bringup_arm(MotorBringupControl *control, uint32_t now_ms);
uint8_t motor_bringup_run(
    MotorBringupControl *control,
    int8_t requested_direction,
    uint16_t duty_permille,
    uint32_t now_ms
);
uint8_t motor_bringup_heartbeat(MotorBringupControl *control, uint32_t now_ms);
void motor_bringup_stop(MotorBringupControl *control);
void motor_bringup_reset(MotorBringupControl *control);
uint8_t motor_bringup_service(MotorBringupControl *control, uint32_t now_ms);

