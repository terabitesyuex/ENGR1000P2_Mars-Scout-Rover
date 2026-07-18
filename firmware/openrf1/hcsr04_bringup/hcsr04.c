#include "hcsr04.h"

#include "board_config.h"

static Hcsr04ResultCode wait_for_echo_state(Hcsr04Driver *driver, uint8_t expected_high, uint32_t start_us, Hcsr04ResultCode timeout_code) {
    uint32_t polls = 0u;
    while (driver->io.read_echo() != expected_high) {
        uint32_t now_us = driver->io.read_timer_us();
        if (hcsr04_elapsed_us(start_us, now_us, driver->timer_modulus_us) >= driver->timeout_us) {
            return timeout_code;
        }
        ++polls;
        if (polls >= driver->wait_poll_limit) {
            return HCSR04_RESULT_TIMER_MEASUREMENT_FAILURE;
        }
    }
    return HCSR04_RESULT_OK;
}

Hcsr04ResultCode hcsr04_driver_init(Hcsr04Driver *driver, const Hcsr04Io *io) {
    if (driver == 0 || io == 0 || io->write_trigger == 0 || io->read_echo == 0 ||
        io->read_timer_us == 0 || io->delay_us == 0) {
        return HCSR04_RESULT_INTERNAL_STATE_ERROR;
    }

    driver->io = *io;
    driver->timer_modulus_us = OPENRF1_HCSR04_TIMER_MODULUS_US;
    driver->timeout_us = OPENRF1_HCSR04_ECHO_TIMEOUT_US;
    driver->wait_poll_limit = OPENRF1_HCSR04_WAIT_POLL_LIMIT;
    driver->trigger_pulse_us = OPENRF1_HCSR04_TRIGGER_PULSE_US;
    driver->initialized = 1u;
    driver->io.write_trigger(0u);
    return HCSR04_RESULT_OK;
}

Hcsr04ResultCode hcsr04_measure_once(Hcsr04Driver *driver, Hcsr04MeasurementResult *result) {
    if (driver == 0 || result == 0 || driver->initialized == 0u) {
        return HCSR04_RESULT_INTERNAL_STATE_ERROR;
    }

    result->echo_pulse_us = 0u;
    result->distance_mm = 0u;

    uint32_t start_us = driver->io.read_timer_us();
    Hcsr04ResultCode status = wait_for_echo_state(driver, 0u, start_us, HCSR04_RESULT_ECHO_NOT_LOW_BEFORE_TRIGGER);
    if (status != HCSR04_RESULT_OK) {
        driver->io.write_trigger(0u);
        return status;
    }

    driver->io.write_trigger(0u);
    driver->io.write_trigger(1u);
    driver->io.delay_us(driver->trigger_pulse_us);
    driver->io.write_trigger(0u);

    start_us = driver->io.read_timer_us();
    status = wait_for_echo_state(driver, 1u, start_us, HCSR04_RESULT_ECHO_RISE_TIMEOUT);
    if (status != HCSR04_RESULT_OK) {
        return status;
    }

    uint32_t rising_edge_us = driver->io.read_timer_us();
    status = wait_for_echo_state(driver, 0u, rising_edge_us, HCSR04_RESULT_ECHO_FALL_TIMEOUT);
    if (status != HCSR04_RESULT_OK) {
        return status;
    }

    uint32_t falling_edge_us = driver->io.read_timer_us();
    uint32_t pulse_us = hcsr04_elapsed_us(rising_edge_us, falling_edge_us, driver->timer_modulus_us);
    status = hcsr04_validate_pulse_width_us(pulse_us);
    if (status != HCSR04_RESULT_OK) {
        return status;
    }

    result->echo_pulse_us = pulse_us;
    result->distance_mm = hcsr04_echo_us_to_distance_mm(pulse_us);
    return HCSR04_RESULT_OK;
}

uint32_t hcsr04_elapsed_us(uint32_t start_us, uint32_t end_us, uint32_t modulus_us) {
    if (modulus_us == 0u) {
        return 0u;
    }
    if (end_us >= start_us) {
        return end_us - start_us;
    }
    return (modulus_us - start_us) + end_us;
}

Hcsr04ResultCode hcsr04_validate_pulse_width_us(uint32_t echo_pulse_us) {
    if (echo_pulse_us == 0u || echo_pulse_us >= OPENRF1_HCSR04_ECHO_TIMEOUT_US) {
        return HCSR04_RESULT_PULSE_WIDTH_OUT_OF_BOUNDS;
    }
    return HCSR04_RESULT_OK;
}

uint16_t hcsr04_echo_us_to_distance_mm(uint32_t echo_pulse_us) {
    uint32_t distance_mm = (echo_pulse_us * 343u + 1000u) / 2000u;
    if (distance_mm > 0xFFFFu) {
        return 0xFFFFu;
    }
    return (uint16_t)distance_mm;
}

const char *hcsr04_result_code_to_text(Hcsr04ResultCode code) {
    switch (code) {
        case HCSR04_RESULT_OK:
            return "ok";
        case HCSR04_RESULT_ECHO_NOT_LOW_BEFORE_TRIGGER:
            return "echo_not_low_before_trigger";
        case HCSR04_RESULT_ECHO_RISE_TIMEOUT:
            return "echo_rise_timeout";
        case HCSR04_RESULT_ECHO_FALL_TIMEOUT:
            return "echo_fall_timeout";
        case HCSR04_RESULT_TIMER_CONFIGURATION_FAILURE:
            return "timer_configuration_failure";
        case HCSR04_RESULT_TIMER_MEASUREMENT_FAILURE:
            return "timer_measurement_failure";
        case HCSR04_RESULT_PULSE_WIDTH_OUT_OF_BOUNDS:
            return "pulse_width_out_of_bounds";
        case HCSR04_RESULT_INTERNAL_STATE_ERROR:
        default:
            return "internal_state_error";
    }
}

const char *hcsr04_result_operation_to_text(Hcsr04ResultCode code) {
    switch (code) {
        case HCSR04_RESULT_ECHO_NOT_LOW_BEFORE_TRIGGER:
            return "wait_for_echo_low";
        case HCSR04_RESULT_ECHO_RISE_TIMEOUT:
            return "wait_for_echo_rising_edge";
        case HCSR04_RESULT_ECHO_FALL_TIMEOUT:
            return "wait_for_echo_falling_edge";
        case HCSR04_RESULT_TIMER_CONFIGURATION_FAILURE:
            return "timer_configuration";
        case HCSR04_RESULT_TIMER_MEASUREMENT_FAILURE:
            return "timer_measurement";
        case HCSR04_RESULT_PULSE_WIDTH_OUT_OF_BOUNDS:
            return "pulse_width_validation";
        case HCSR04_RESULT_OK:
            return "measurement";
        case HCSR04_RESULT_INTERNAL_STATE_ERROR:
        default:
            return "internal_state";
    }
}
