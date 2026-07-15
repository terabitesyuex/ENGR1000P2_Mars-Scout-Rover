#include "soft_i2c.h"

#include "board_config.h"

static void i2c_delay(void) {
    volatile uint16_t ticks = 24u;
    while (ticks-- > 0u) {
    }
}

static void scl_high(void) {
    GPIO_SetBits(OPENRF1_SOFT_I2C_SCL_PORT, OPENRF1_SOFT_I2C_SCL_PIN);
}

static void scl_low(void) {
    GPIO_ResetBits(OPENRF1_SOFT_I2C_SCL_PORT, OPENRF1_SOFT_I2C_SCL_PIN);
}

static void sda_high(void) {
    GPIO_SetBits(OPENRF1_SOFT_I2C_SDA_PORT, OPENRF1_SOFT_I2C_SDA_PIN);
}

static void sda_low(void) {
    GPIO_ResetBits(OPENRF1_SOFT_I2C_SDA_PORT, OPENRF1_SOFT_I2C_SDA_PIN);
}

static uint8_t sda_read(void) {
    return GPIO_ReadInputDataBit(OPENRF1_SOFT_I2C_SDA_PORT, OPENRF1_SOFT_I2C_SDA_PIN) != 0u;
}

void openrf1_soft_i2c_init(void) {
    GPIO_InitTypeDef gpio;

    RCC_APB2PeriphClockCmd(OPENRF1_SOFT_I2C_SCL_RCC | OPENRF1_SOFT_I2C_SDA_RCC, ENABLE);

    gpio.GPIO_Mode = GPIO_Mode_Out_OD;
    gpio.GPIO_Speed = GPIO_Speed_50MHz;
    gpio.GPIO_Pin = OPENRF1_SOFT_I2C_SCL_PIN;
    GPIO_Init(OPENRF1_SOFT_I2C_SCL_PORT, &gpio);
    gpio.GPIO_Pin = OPENRF1_SOFT_I2C_SDA_PIN;
    GPIO_Init(OPENRF1_SOFT_I2C_SDA_PORT, &gpio);

    sda_high();
    scl_high();
    i2c_delay();
}

void openrf1_soft_i2c_start(void) {
    sda_high();
    scl_high();
    i2c_delay();
    sda_low();
    i2c_delay();
    scl_low();
}

void openrf1_soft_i2c_stop(void) {
    scl_low();
    sda_low();
    i2c_delay();
    scl_high();
    i2c_delay();
    sda_high();
    i2c_delay();
}

OpenRf1I2cStatus openrf1_soft_i2c_write_byte(uint8_t value) {
    for (uint8_t mask = 0x80u; mask != 0u; mask >>= 1u) {
        if ((value & mask) != 0u) {
            sda_high();
        } else {
            sda_low();
        }
        i2c_delay();
        scl_high();
        i2c_delay();
        scl_low();
    }
    sda_high();
    return openrf1_soft_i2c_wait_ack(OPENRF1_SOFT_I2C_ACK_TIMEOUT_TICKS);
}

uint8_t openrf1_soft_i2c_read_byte(uint8_t send_ack) {
    uint8_t value = 0u;
    sda_high();
    for (uint8_t bit = 0u; bit < 8u; ++bit) {
        value <<= 1u;
        scl_high();
        i2c_delay();
        if (sda_read()) {
            value |= 1u;
        }
        scl_low();
        i2c_delay();
    }
    if (send_ack != 0u) {
        openrf1_soft_i2c_ack();
    } else {
        openrf1_soft_i2c_nack();
    }
    return value;
}

OpenRf1I2cStatus openrf1_soft_i2c_wait_ack(uint16_t timeout_ticks) {
    sda_high();
    i2c_delay();
    scl_high();
    while (sda_read()) {
        i2c_delay();
        if (timeout_ticks == 0u) {
            scl_low();
            openrf1_soft_i2c_stop();
            return OPENRF1_I2C_ACK_TIMEOUT;
        }
        --timeout_ticks;
    }
    scl_low();
    return OPENRF1_I2C_OK;
}

void openrf1_soft_i2c_ack(void) {
    scl_low();
    sda_low();
    i2c_delay();
    scl_high();
    i2c_delay();
    scl_low();
    sda_high();
}

void openrf1_soft_i2c_nack(void) {
    scl_low();
    sda_high();
    i2c_delay();
    scl_high();
    i2c_delay();
    scl_low();
}

OpenRf1I2cStatus openrf1_soft_i2c_recover_bus(uint8_t pulses) {
    if (pulses == 0u) {
        return OPENRF1_I2C_INVALID_ARGUMENT;
    }
    sda_high();
    for (uint8_t index = 0u; index < pulses; ++index) {
        scl_low();
        i2c_delay();
        scl_high();
        i2c_delay();
        if (sda_read()) {
            openrf1_soft_i2c_stop();
            return OPENRF1_I2C_OK;
        }
    }
    openrf1_soft_i2c_stop();
    return sda_read() ? OPENRF1_I2C_OK : OPENRF1_I2C_BUS_STUCK;
}
