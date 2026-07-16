#include "i2c_bus.h"

#include "../app/soft_i2c.h"
#include "board_config.h"

static uint8_t address_write(uint8_t address_7bit) {
    return (uint8_t)(address_7bit << 1u);
}

static uint8_t address_read(uint8_t address_7bit) {
    return (uint8_t)((address_7bit << 1u) | 0x01u);
}

static OpenRf1Status map_i2c_status(OpenRf1I2cStatus status) {
    if (status == OPENRF1_I2C_OK) {
        return OPENRF1_STATUS_OK;
    }
    if (status == OPENRF1_I2C_ACK_TIMEOUT) {
        return OPENRF1_STATUS_NACK;
    }
    if (status == OPENRF1_I2C_INVALID_ARGUMENT) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    return OPENRF1_STATUS_HARDWARE_FAULT;
}

static OpenRf1Status fail_and_recover(OpenRf1I2cStatus status) {
    openrf1_soft_i2c_stop();
    (void)openrf1_i2c_recover();
    return map_i2c_status(status);
}

void openrf1_i2c_bus_init(void) {
    openrf1_soft_i2c_init();
}

OpenRf1Status openrf1_i2c_write(uint8_t address_7bit, const uint8_t *data, uint8_t length) {
    if (address_7bit > 0x7Fu || (data == 0 && length > 0u) || length > OPENRF1_I2C_MAX_TRANSFER_BYTES) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    openrf1_soft_i2c_start();
    OpenRf1I2cStatus status = openrf1_soft_i2c_write_byte(address_write(address_7bit));
    if (status != OPENRF1_I2C_OK) {
        return fail_and_recover(status);
    }
    for (uint8_t index = 0u; index < length; ++index) {
        status = openrf1_soft_i2c_write_byte(data[index]);
        if (status != OPENRF1_I2C_OK) {
            return fail_and_recover(status);
        }
    }
    openrf1_soft_i2c_stop();
    return OPENRF1_STATUS_OK;
}

OpenRf1Status openrf1_i2c_read(uint8_t address_7bit, uint8_t *data, uint8_t length) {
    if (address_7bit > 0x7Fu || data == 0 || length == 0u || length > OPENRF1_I2C_MAX_TRANSFER_BYTES) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    openrf1_soft_i2c_start();
    OpenRf1I2cStatus status = openrf1_soft_i2c_write_byte(address_read(address_7bit));
    if (status != OPENRF1_I2C_OK) {
        return fail_and_recover(status);
    }
    for (uint8_t index = 0u; index < length; ++index) {
        data[index] = openrf1_soft_i2c_read_byte((uint8_t)(index + 1u < length));
    }
    openrf1_soft_i2c_stop();
    return OPENRF1_STATUS_OK;
}

OpenRf1Status openrf1_i2c_write_read(
    uint8_t address_7bit,
    const uint8_t *write_data,
    uint8_t write_length,
    uint8_t *read_data,
    uint8_t read_length
) {
    OpenRf1Status status = openrf1_i2c_write(address_7bit, write_data, write_length);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    return openrf1_i2c_read(address_7bit, read_data, read_length);
}

OpenRf1Status openrf1_i2c_probe(uint8_t address_7bit) {
    if (address_7bit > 0x7Fu) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    openrf1_soft_i2c_start();
    OpenRf1I2cStatus status = openrf1_soft_i2c_write_byte(address_write(address_7bit));
    openrf1_soft_i2c_stop();
    return map_i2c_status(status);
}

OpenRf1Status openrf1_i2c_recover(void) {
    return map_i2c_status(openrf1_soft_i2c_recover_bus(OPENRF1_SOFT_I2C_RECOVERY_PULSES));
}
