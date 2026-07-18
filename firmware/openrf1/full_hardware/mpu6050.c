#include "mpu6050.h"

#include "i2c_bus.h"

static int16_t s16_be(uint8_t msb, uint8_t lsb) {
    return (int16_t)((uint16_t)(((uint16_t)msb << 8u) | (uint16_t)lsb));
}

static OpenRf1Status require_readback(uint8_t expected, uint8_t observed) {
    return expected == observed ? OPENRF1_STATUS_OK : OPENRF1_STATUS_HARDWARE_FAULT;
}

OpenRf1Status mpu6050_validate_who_am_i(uint8_t who_am_i) {
    return (who_am_i == MPU6050_WHO_AM_I_EXPECTED) ? OPENRF1_STATUS_OK : OPENRF1_STATUS_BAD_ID;
}

OpenRf1Status mpu6050_read_register(uint8_t address_7bit, uint8_t reg, uint8_t *value) {
    if (value == 0) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    return openrf1_i2c_write_read(address_7bit, &reg, 1u, value, 1u);
}

OpenRf1Status mpu6050_write_register(uint8_t address_7bit, uint8_t reg, uint8_t value) {
    uint8_t buffer[2u] = {reg, value};
    return openrf1_i2c_write(address_7bit, buffer, (uint8_t)sizeof(buffer));
}

OpenRf1Status mpu6050_write_register_readback(
    uint8_t address_7bit,
    uint8_t reg,
    uint8_t value,
    uint8_t *readback
) {
    if (readback == 0) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    OpenRf1Status status = mpu6050_write_register(address_7bit, reg, value);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    status = mpu6050_read_register(address_7bit, reg, readback);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    return require_readback(value, *readback);
}

OpenRf1Status mpu6050_read_who_am_i(uint8_t address_7bit, uint8_t *who_am_i) {
    OpenRf1Status status = mpu6050_read_register(address_7bit, MPU6050_REG_WHO_AM_I, who_am_i);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    return mpu6050_validate_who_am_i(*who_am_i);
}

OpenRf1Status mpu6050_wake_for_bringup(uint8_t address_7bit, uint8_t *pwr_mgmt_1_readback) {
    return mpu6050_write_register_readback(
        address_7bit,
        MPU6050_REG_PWR_MGMT_1,
        MPU6050_PWR_MGMT_1_X_GYRO_PLL,
        pwr_mgmt_1_readback
    );
}

OpenRf1Status mpu6050_configure_for_bringup(uint8_t address_7bit, Mpu6050RegisterConfig *readback) {
    if (readback == 0) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    OpenRf1Status status = mpu6050_write_register_readback(
        address_7bit,
        MPU6050_REG_SMPLRT_DIV,
        MPU6050_SMPLRT_DIV_100HZ_DLPF,
        &readback->smplrt_div
    );
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    status = mpu6050_write_register_readback(
        address_7bit,
        MPU6050_REG_CONFIG,
        MPU6050_CONFIG_DLPF_44HZ,
        &readback->config
    );
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    status = mpu6050_write_register_readback(
        address_7bit,
        MPU6050_REG_GYRO_CONFIG,
        MPU6050_GYRO_CONFIG_250DPS,
        &readback->gyro_config
    );
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    status = mpu6050_write_register_readback(
        address_7bit,
        MPU6050_REG_ACCEL_CONFIG,
        MPU6050_ACCEL_CONFIG_2G,
        &readback->accel_config
    );
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    return mpu6050_read_register(address_7bit, MPU6050_REG_PWR_MGMT_1, &readback->pwr_mgmt_1);
}

OpenRf1Status mpu6050_read_configuration(uint8_t address_7bit, Mpu6050RegisterConfig *readback) {
    if (readback == 0) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    OpenRf1Status status = mpu6050_read_register(address_7bit, MPU6050_REG_PWR_MGMT_1, &readback->pwr_mgmt_1);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    status = mpu6050_read_register(address_7bit, MPU6050_REG_SMPLRT_DIV, &readback->smplrt_div);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    status = mpu6050_read_register(address_7bit, MPU6050_REG_CONFIG, &readback->config);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    status = mpu6050_read_register(address_7bit, MPU6050_REG_GYRO_CONFIG, &readback->gyro_config);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    return mpu6050_read_register(address_7bit, MPU6050_REG_ACCEL_CONFIG, &readback->accel_config);
}

OpenRf1Status mpu6050_read_raw_sample(uint8_t address_7bit, Mpu6050RawSample *sample) {
    if (sample == 0) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    uint8_t reg = MPU6050_REG_ACCEL_XOUT_H;
    uint8_t buffer[MPU6050_BURST_SAMPLE_BYTES];
    OpenRf1Status status = openrf1_i2c_write_read(address_7bit, &reg, 1u, buffer, (uint8_t)sizeof(buffer));
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    sample->accel_x_raw = s16_be(buffer[0], buffer[1]);
    sample->accel_y_raw = s16_be(buffer[2], buffer[3]);
    sample->accel_z_raw = s16_be(buffer[4], buffer[5]);
    sample->temperature_raw = s16_be(buffer[6], buffer[7]);
    sample->gyro_x_raw = s16_be(buffer[8], buffer[9]);
    sample->gyro_y_raw = s16_be(buffer[10], buffer[11]);
    sample->gyro_z_raw = s16_be(buffer[12], buffer[13]);
    return OPENRF1_STATUS_OK;
}

int32_t mpu6050_accel_raw_to_mg(int16_t raw, Mpu6050AccelRange range) {
    static const int32_t lsb_per_g[] = {16384, 8192, 4096, 2048};
    if ((uint32_t)range > (uint32_t)MPU6050_ACCEL_RANGE_16G) {
        range = MPU6050_ACCEL_RANGE_2G;
    }
    return ((int32_t)raw * 1000) / lsb_per_g[range];
}

int32_t mpu6050_gyro_raw_to_mdps(int16_t raw, Mpu6050GyroRange range) {
    static const int32_t lsb_per_dps_times_10[] = {1310, 655, 328, 164};
    if ((uint32_t)range > (uint32_t)MPU6050_GYRO_RANGE_2000DPS) {
        range = MPU6050_GYRO_RANGE_250DPS;
    }
    return ((int32_t)raw * 10000) / lsb_per_dps_times_10[range];
}

int32_t mpu6050_temperature_raw_to_centideg_c(int16_t raw) {
    return 3653 + (((int32_t)raw * 100) / 340);
}
