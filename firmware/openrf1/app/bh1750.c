#include "bh1750.h"

#include <stddef.h>

#include "board_config.h"
#include "soft_i2c.h"

#define BH1750_CMD_POWER_DOWN ((uint8_t)0x00u)
#define BH1750_CMD_POWER_ON ((uint8_t)0x01u)
#define BH1750_CMD_ONE_TIME_HIGH_RESOLUTION ((uint8_t)0x20u)

static Bh1750Status write_command(uint8_t command);
static Bh1750Status recover_after_i2c_failure(void);

void bh1750_context_init(Bh1750Context *context) {
    if (context == NULL) {
        return;
    }
    context->state = BH1750_STATE_NOT_INITIALIZED;
    context->next_action_ms = 0u;
    context->publish_period_ms = OPENRF1_BH1750_PERIOD_MS;
    context->measurement_time_ms = OPENRF1_BH1750_MEASUREMENT_TIME_MS;
    context->retry_backoff_ms = OPENRF1_BH1750_RETRY_BACKOFF_MS;
    context->last_publish_ms = 0u;
    context->initialized = 0u;
}

uint8_t bh1750_write_address_from_7bit(uint8_t address_7bit) {
    return (uint8_t)(address_7bit << 1u);
}

uint8_t bh1750_read_address_from_7bit(uint8_t address_7bit) {
    return (uint8_t)((address_7bit << 1u) | 0x01u);
}

uint16_t bh1750_raw_from_bytes(uint8_t msb, uint8_t lsb) {
    return (uint16_t)(((uint16_t)msb << 8u) | (uint16_t)lsb);
}

uint32_t bh1750_raw_to_centilux(uint16_t raw_count) {
    return (((uint32_t)raw_count * 250u) + 1u) / 3u;
}

Bh1750Status bh1750_power_on(void) {
    return write_command(BH1750_CMD_POWER_ON);
}

Bh1750Status bh1750_power_down(void) {
    return write_command(BH1750_CMD_POWER_DOWN);
}

Bh1750Status bh1750_start_high_resolution_measurement(void) {
    Bh1750Status status = bh1750_power_on();
    if (status != BH1750_STATUS_OK) {
        return status;
    }
    return write_command(BH1750_CMD_ONE_TIME_HIGH_RESOLUTION);
}

Bh1750Status bh1750_read_raw_count(uint16_t *raw_count) {
    if (raw_count == NULL) {
        return BH1750_STATUS_HARDWARE_FAULT;
    }
    openrf1_soft_i2c_start();
    if (openrf1_soft_i2c_write_byte(bh1750_read_address_from_7bit(OPENRF1_BH1750_ADDRESS_7BIT)) != OPENRF1_I2C_OK) {
        return recover_after_i2c_failure();
    }
    uint8_t msb = openrf1_soft_i2c_read_byte(1u);
    uint8_t lsb = openrf1_soft_i2c_read_byte(0u);
    openrf1_soft_i2c_stop();
    *raw_count = bh1750_raw_from_bytes(msb, lsb);
    return BH1750_STATUS_OK;
}

bool bh1750_task(Bh1750Context *context, uint32_t now_ms, Bh1750Sample *sample) {
    if (context == NULL || sample == NULL) {
        return false;
    }
    if ((int32_t)(now_ms - context->next_action_ms) < 0) {
        return false;
    }

    sample->timestamp_ms = now_ms;
    sample->illuminance_centilux = 0u;
    sample->has_illuminance = 0u;

    if (context->state == BH1750_STATE_NOT_INITIALIZED) {
        openrf1_soft_i2c_init();
        context->initialized = 1u;
        context->state = BH1750_STATE_START_MEASUREMENT;
    }

    if (context->state == BH1750_STATE_START_MEASUREMENT) {
        Bh1750Status status = bh1750_start_high_resolution_measurement();
        if (status == BH1750_STATUS_OK) {
            context->state = BH1750_STATE_WAIT_MEASUREMENT;
            context->next_action_ms = now_ms + context->measurement_time_ms;
            return false;
        }
        context->state = BH1750_STATE_RETRY_BACKOFF;
        context->next_action_ms = now_ms + context->retry_backoff_ms;
        sample->status = status;
        return true;
    }

    if (context->state == BH1750_STATE_WAIT_MEASUREMENT) {
        context->state = BH1750_STATE_READ_MEASUREMENT;
    }

    if (context->state == BH1750_STATE_READ_MEASUREMENT) {
        uint16_t raw_count = 0u;
        Bh1750Status status = bh1750_read_raw_count(&raw_count);
        if (status == BH1750_STATUS_OK) {
            sample->status = BH1750_STATUS_OK;
            sample->illuminance_centilux = bh1750_raw_to_centilux(raw_count);
            sample->has_illuminance = 1u;
            uint32_t idle_time_ms = 0u;
            if (context->publish_period_ms > context->measurement_time_ms) {
                idle_time_ms = context->publish_period_ms - context->measurement_time_ms;
            }
            context->last_publish_ms = now_ms;
            context->state = BH1750_STATE_START_MEASUREMENT;
            context->next_action_ms = now_ms + idle_time_ms;
            return true;
        }
        context->state = BH1750_STATE_RETRY_BACKOFF;
        context->next_action_ms = now_ms + context->retry_backoff_ms;
        sample->status = status;
        return true;
    }

    if (context->state == BH1750_STATE_RETRY_BACKOFF) {
        context->state = BH1750_STATE_START_MEASUREMENT;
        return false;
    }

    sample->status = BH1750_STATUS_HARDWARE_FAULT;
    context->state = BH1750_STATE_RETRY_BACKOFF;
    context->next_action_ms = now_ms + context->retry_backoff_ms;
    return true;
}

const char *bh1750_status_to_telemetry(Bh1750Status status) {
    switch (status) {
        case BH1750_STATUS_OK:
            return "ok";
        case BH1750_STATUS_TIMEOUT:
            return "timeout";
        case BH1750_STATUS_NOT_INITIALIZED:
            return "not_initialized";
        case BH1750_STATUS_STALE:
            return "stale";
        case BH1750_STATUS_HARDWARE_FAULT:
        default:
            return "hardware_fault";
    }
}

static Bh1750Status write_command(uint8_t command) {
    openrf1_soft_i2c_start();
    if (openrf1_soft_i2c_write_byte(bh1750_write_address_from_7bit(OPENRF1_BH1750_ADDRESS_7BIT)) != OPENRF1_I2C_OK) {
        return recover_after_i2c_failure();
    }
    if (openrf1_soft_i2c_write_byte(command) != OPENRF1_I2C_OK) {
        return recover_after_i2c_failure();
    }
    openrf1_soft_i2c_stop();
    return BH1750_STATUS_OK;
}

static Bh1750Status recover_after_i2c_failure(void) {
    OpenRf1I2cStatus recovery_status;

    openrf1_soft_i2c_stop();
    recovery_status = openrf1_soft_i2c_recover_bus(OPENRF1_SOFT_I2C_RECOVERY_PULSES);
    if (recovery_status == OPENRF1_I2C_OK) {
        return BH1750_STATUS_TIMEOUT;
    }
    return BH1750_STATUS_HARDWARE_FAULT;
}
