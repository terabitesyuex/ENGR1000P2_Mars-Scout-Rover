#pragma once

#include <stdint.h>

typedef enum {
    HCSR04_RESULT_OK = 0,
    HCSR04_RESULT_ECHO_NOT_LOW_BEFORE_TRIGGER,
    HCSR04_RESULT_ECHO_RISE_TIMEOUT,
    HCSR04_RESULT_ECHO_FALL_TIMEOUT,
    HCSR04_RESULT_TIMER_CONFIGURATION_FAILURE,
    HCSR04_RESULT_TIMER_MEASUREMENT_FAILURE,
    HCSR04_RESULT_PULSE_WIDTH_OUT_OF_BOUNDS,
    HCSR04_RESULT_TELEMETRY_FORMAT_FAILURE,
    HCSR04_RESULT_INTERNAL_STATE_ERROR
} Hcsr04ResultCode;

typedef struct {
    uint32_t echo_pulse_us;
    uint16_t distance_mm;
} Hcsr04MeasurementResult;

typedef struct {
    void (*write_trigger)(uint8_t high);
    uint8_t (*read_echo)(void);
    uint32_t (*read_timer_us)(void);
    void (*delay_us)(uint16_t delay_us);
} Hcsr04Io;

typedef struct {
    Hcsr04Io io;
    uint32_t timer_modulus_us;
    uint32_t timeout_us;
    uint32_t wait_poll_limit;
    uint16_t trigger_pulse_us;
    uint8_t initialized;
} Hcsr04Driver;

Hcsr04ResultCode hcsr04_driver_init(Hcsr04Driver *driver, const Hcsr04Io *io);
Hcsr04ResultCode hcsr04_measure_once(Hcsr04Driver *driver, Hcsr04MeasurementResult *result);
uint32_t hcsr04_elapsed_us(uint32_t start_us, uint32_t end_us, uint32_t modulus_us);
Hcsr04ResultCode hcsr04_validate_pulse_width_us(uint32_t echo_pulse_us);
uint16_t hcsr04_echo_us_to_distance_mm(uint32_t echo_pulse_us);
const char *hcsr04_result_code_to_text(Hcsr04ResultCode code);
const char *hcsr04_result_operation_to_text(Hcsr04ResultCode code);
