#pragma once

#include <stdint.h>

#define MOTOR_COMMAND_MAX_PERMILLE ((int16_t)1000)

typedef enum {
    MOTOR_ID_FRONT_LEFT = 0,
    MOTOR_ID_FRONT_RIGHT,
    MOTOR_ID_REAR_LEFT,
    MOTOR_ID_REAR_RIGHT,
    MOTOR_ID_COUNT
} MotorId;

typedef enum {
    MOTOR_DIRECTION_STOP = 0,
    MOTOR_DIRECTION_FORWARD = 1,
    MOTOR_DIRECTION_REVERSE = -1
} MotorDirection;

typedef enum {
    MOTOR_STATUS_OK = 0,
    MOTOR_STATUS_INVALID_ARGUMENT,
    MOTOR_STATUS_INVALID_MOTOR_ID,
    MOTOR_STATUS_INVALID_DIRECTION,
    MOTOR_STATUS_COMMAND_OUT_OF_RANGE,
    MOTOR_STATUS_NOT_INITIALIZED,
    MOTOR_STATUS_BACKEND_ERROR
} MotorStatus;

typedef struct {
    MotorDirection direction;
    uint16_t duty_permille;
} MotorOutput;

typedef MotorStatus (*MotorApplyOutputFn)(
    void *context,
    MotorId motor_id,
    const MotorOutput *output
);

typedef struct {
    MotorApplyOutputFn apply_output;
} MotorHardwareOps;

typedef struct {
    MotorHardwareOps hardware;
    void *hardware_context;
    MotorOutput outputs[MOTOR_ID_COUNT];
    uint8_t initialized;
} MotorController;

MotorStatus motor_controller_init(
    MotorController *controller,
    const MotorHardwareOps *hardware,
    void *hardware_context
);
MotorStatus motor_set_speed(MotorController *controller, MotorId motor_id, int16_t speed_permille);
MotorStatus motor_set_direction(MotorController *controller, MotorId motor_id, MotorDirection direction);
MotorStatus motor_stop(MotorController *controller, MotorId motor_id);
MotorStatus motor_stop_all(MotorController *controller);
MotorStatus motor_get_output(const MotorController *controller, MotorId motor_id, MotorOutput *output);
int16_t motor_output_signed_speed_permille(const MotorOutput *output);
