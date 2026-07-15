#pragma once

#include <stdint.h>

typedef enum {
    OPENRF1_I2C_OK = 0,
    OPENRF1_I2C_ACK_TIMEOUT,
    OPENRF1_I2C_BUS_STUCK,
    OPENRF1_I2C_INVALID_ARGUMENT
} OpenRf1I2cStatus;

void openrf1_soft_i2c_init(void);
void openrf1_soft_i2c_start(void);
void openrf1_soft_i2c_stop(void);
OpenRf1I2cStatus openrf1_soft_i2c_write_byte(uint8_t value);
uint8_t openrf1_soft_i2c_read_byte(uint8_t send_ack);
OpenRf1I2cStatus openrf1_soft_i2c_wait_ack(uint16_t timeout_ticks);
void openrf1_soft_i2c_ack(void);
void openrf1_soft_i2c_nack(void);
OpenRf1I2cStatus openrf1_soft_i2c_recover_bus(uint8_t pulses);
