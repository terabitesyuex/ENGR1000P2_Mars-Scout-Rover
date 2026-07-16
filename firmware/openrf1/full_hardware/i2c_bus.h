#pragma once

#include <stdint.h>

#include "openrf1_status.h"

#define OPENRF1_I2C_MAX_TRANSFER_BYTES ((uint8_t)32u)

void openrf1_i2c_bus_init(void);
OpenRf1Status openrf1_i2c_write(uint8_t address_7bit, const uint8_t *data, uint8_t length);
OpenRf1Status openrf1_i2c_read(uint8_t address_7bit, uint8_t *data, uint8_t length);
OpenRf1Status openrf1_i2c_write_read(
    uint8_t address_7bit,
    const uint8_t *write_data,
    uint8_t write_length,
    uint8_t *read_data,
    uint8_t read_length
);
OpenRf1Status openrf1_i2c_probe(uint8_t address_7bit);
OpenRf1Status openrf1_i2c_recover(void);
