#include <stdint.h>

#include "drivers/encoder/encoder.h"
#include "drivers/motor/motor.h"

/*
 * Link-only foundation entry point. It deliberately uses inert injected
 * backends because motor and encoder peripheral mappings are still unknown.
 */
static MotorStatus foundation_apply_motor(
    void *context,
    MotorId motor_id,
    const MotorOutput *output
) {
    (void)context;
    (void)motor_id;
    if (output == 0) {
        return MOTOR_STATUS_INVALID_ARGUMENT;
    }
    return MOTOR_STATUS_OK;
}

static EncoderStatus foundation_read_encoder(
    void *context,
    EncoderId encoder_id,
    int32_t *count
) {
    (void)context;
    (void)encoder_id;
    if (count == 0) {
        return ENCODER_STATUS_INVALID_ARGUMENT;
    }
    *count = 0;
    return ENCODER_STATUS_OK;
}

int main(void) {
    MotorController motors;
    EncoderBank encoders;
    MotorHardwareOps motor_hardware;
    EncoderHardwareOps encoder_hardware;
    volatile uint32_t initialization_status;

    motor_hardware.apply_output = foundation_apply_motor;
    encoder_hardware.read_count = foundation_read_encoder;

    initialization_status = (uint32_t)motor_controller_init(
        &motors,
        &motor_hardware,
        0
    );
    initialization_status |= (uint32_t)encoder_bank_init(
        &encoders,
        &encoder_hardware,
        0
    );
    initialization_status |= (uint32_t)encoder_update_all(&encoders, 0u);

    for (;;) {
        (void)initialization_status;
    }
}
