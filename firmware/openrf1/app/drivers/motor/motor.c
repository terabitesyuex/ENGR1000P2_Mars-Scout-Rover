#include "motor.h"

static uint8_t motor_id_is_valid(MotorId motor_id) {
    return (uint8_t)((int)motor_id >= 0 && motor_id < MOTOR_ID_COUNT);
}

static uint8_t motor_direction_is_valid(MotorDirection direction) {
    return (uint8_t)(
        direction == MOTOR_DIRECTION_STOP ||
        direction == MOTOR_DIRECTION_FORWARD ||
        direction == MOTOR_DIRECTION_REVERSE
    );
}

static MotorStatus motor_apply(
    MotorController *controller,
    MotorId motor_id,
    const MotorOutput *output
) {
    MotorStatus backend_status;

    if (controller == 0 || output == 0) {
        return MOTOR_STATUS_INVALID_ARGUMENT;
    }
    if (controller->initialized == 0u) {
        return MOTOR_STATUS_NOT_INITIALIZED;
    }
    if (!motor_id_is_valid(motor_id)) {
        return MOTOR_STATUS_INVALID_MOTOR_ID;
    }

    backend_status = controller->hardware.apply_output(
        controller->hardware_context,
        motor_id,
        output
    );
    if (backend_status != MOTOR_STATUS_OK) {
        return MOTOR_STATUS_BACKEND_ERROR;
    }

    controller->outputs[motor_id] = *output;
    return MOTOR_STATUS_OK;
}

MotorStatus motor_controller_init(
    MotorController *controller,
    const MotorHardwareOps *hardware,
    void *hardware_context
) {
    MotorOutput stopped_output;
    MotorStatus first_error = MOTOR_STATUS_OK;
    MotorId motor_id;

    if (controller == 0 || hardware == 0 || hardware->apply_output == 0) {
        return MOTOR_STATUS_INVALID_ARGUMENT;
    }

    controller->hardware = *hardware;
    controller->hardware_context = hardware_context;
    controller->initialized = 1u;
    stopped_output.direction = MOTOR_DIRECTION_STOP;
    stopped_output.duty_permille = 0u;

    for (motor_id = MOTOR_ID_FRONT_LEFT; motor_id < MOTOR_ID_COUNT; ++motor_id) {
        MotorStatus status = motor_apply(controller, motor_id, &stopped_output);
        if (status != MOTOR_STATUS_OK && first_error == MOTOR_STATUS_OK) {
            first_error = status;
        }
    }

    if (first_error != MOTOR_STATUS_OK) {
        controller->initialized = 0u;
    }
    return first_error;
}

MotorStatus motor_set_speed(MotorController *controller, MotorId motor_id, int16_t speed_permille) {
    MotorOutput output;

    if (speed_permille < -MOTOR_COMMAND_MAX_PERMILLE ||
        speed_permille > MOTOR_COMMAND_MAX_PERMILLE) {
        return MOTOR_STATUS_COMMAND_OUT_OF_RANGE;
    }

    if (speed_permille > 0) {
        output.direction = MOTOR_DIRECTION_FORWARD;
        output.duty_permille = (uint16_t)speed_permille;
    } else if (speed_permille < 0) {
        output.direction = MOTOR_DIRECTION_REVERSE;
        output.duty_permille = (uint16_t)(-speed_permille);
    } else {
        output.direction = MOTOR_DIRECTION_STOP;
        output.duty_permille = 0u;
    }

    return motor_apply(controller, motor_id, &output);
}

MotorStatus motor_set_direction(MotorController *controller, MotorId motor_id, MotorDirection direction) {
    MotorOutput output;

    if (controller == 0) {
        return MOTOR_STATUS_INVALID_ARGUMENT;
    }
    if (controller->initialized == 0u) {
        return MOTOR_STATUS_NOT_INITIALIZED;
    }
    if (!motor_id_is_valid(motor_id)) {
        return MOTOR_STATUS_INVALID_MOTOR_ID;
    }
    if (!motor_direction_is_valid(direction)) {
        return MOTOR_STATUS_INVALID_DIRECTION;
    }

    output = controller->outputs[motor_id];
    output.direction = direction;
    if (direction == MOTOR_DIRECTION_STOP) {
        output.duty_permille = 0u;
    }
    return motor_apply(controller, motor_id, &output);
}

MotorStatus motor_stop(MotorController *controller, MotorId motor_id) {
    MotorOutput output;

    output.direction = MOTOR_DIRECTION_STOP;
    output.duty_permille = 0u;
    return motor_apply(controller, motor_id, &output);
}

MotorStatus motor_stop_all(MotorController *controller) {
    MotorStatus first_error = MOTOR_STATUS_OK;
    MotorId motor_id;

    if (controller == 0) {
        return MOTOR_STATUS_INVALID_ARGUMENT;
    }
    for (motor_id = MOTOR_ID_FRONT_LEFT; motor_id < MOTOR_ID_COUNT; ++motor_id) {
        MotorStatus status = motor_stop(controller, motor_id);
        if (status != MOTOR_STATUS_OK && first_error == MOTOR_STATUS_OK) {
            first_error = status;
        }
    }
    return first_error;
}

MotorStatus motor_get_output(const MotorController *controller, MotorId motor_id, MotorOutput *output) {
    if (controller == 0 || output == 0) {
        return MOTOR_STATUS_INVALID_ARGUMENT;
    }
    if (controller->initialized == 0u) {
        return MOTOR_STATUS_NOT_INITIALIZED;
    }
    if (!motor_id_is_valid(motor_id)) {
        return MOTOR_STATUS_INVALID_MOTOR_ID;
    }

    *output = controller->outputs[motor_id];
    return MOTOR_STATUS_OK;
}

int16_t motor_output_signed_speed_permille(const MotorOutput *output) {
    if (output == 0 || output->direction == MOTOR_DIRECTION_STOP) {
        return 0;
    }
    if (output->direction == MOTOR_DIRECTION_REVERSE) {
        return (int16_t)(-(int16_t)output->duty_permille);
    }
    return (int16_t)output->duty_permille;
}
