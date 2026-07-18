#pragma once

#include <stdint.h>

#include "openrf1_status.h"

#define MPU6050_ADDRESS_7BIT ((uint8_t)0x68u)
#define MPU6050_WHO_AM_I_EXPECTED ((uint8_t)0x68u)
#define MPU6050_REG_SMPLRT_DIV ((uint8_t)0x19u)
#define MPU6050_REG_CONFIG ((uint8_t)0x1Au)
#define MPU6050_REG_GYRO_CONFIG ((uint8_t)0x1Bu)
#define MPU6050_REG_ACCEL_CONFIG ((uint8_t)0x1Cu)
#define MPU6050_REG_ACCEL_XOUT_H ((uint8_t)0x3Bu)
#define MPU6050_REG_PWR_MGMT_1 ((uint8_t)0x6Bu)
#define MPU6050_REG_WHO_AM_I ((uint8_t)0x75u)

#define MPU6050_PWR_MGMT_1_X_GYRO_PLL ((uint8_t)0x01u)
#define MPU6050_SMPLRT_DIV_100HZ_DLPF ((uint8_t)0x09u)
#define MPU6050_CONFIG_DLPF_44HZ ((uint8_t)0x03u)
#define MPU6050_GYRO_CONFIG_250DPS ((uint8_t)0x00u)
#define MPU6050_ACCEL_CONFIG_2G ((uint8_t)0x00u)
#define MPU6050_BURST_SAMPLE_BYTES ((uint8_t)14u)
#define MPU6050_BRINGUP_SETTLE_MS ((uint32_t)100u)

typedef enum {
    MPU6050_ACCEL_RANGE_2G = 0,
    MPU6050_ACCEL_RANGE_4G = 1,
    MPU6050_ACCEL_RANGE_8G = 2,
    MPU6050_ACCEL_RANGE_16G = 3
} Mpu6050AccelRange;

typedef enum {
    MPU6050_GYRO_RANGE_250DPS = 0,
    MPU6050_GYRO_RANGE_500DPS = 1,
    MPU6050_GYRO_RANGE_1000DPS = 2,
    MPU6050_GYRO_RANGE_2000DPS = 3
} Mpu6050GyroRange;

typedef struct {
    int16_t accel_x_raw;
    int16_t accel_y_raw;
    int16_t accel_z_raw;
    int16_t temperature_raw;
    int16_t gyro_x_raw;
    int16_t gyro_y_raw;
    int16_t gyro_z_raw;
} Mpu6050RawSample;

typedef struct {
    int16_t accel_bias_raw[3];
    int16_t gyro_bias_raw[3];
    uint8_t calibrated;
} Mpu6050CalibrationState;

typedef struct {
    uint8_t pwr_mgmt_1;
    uint8_t smplrt_div;
    uint8_t config;
    uint8_t gyro_config;
    uint8_t accel_config;
} Mpu6050RegisterConfig;

OpenRf1Status mpu6050_validate_who_am_i(uint8_t who_am_i);
OpenRf1Status mpu6050_read_register(uint8_t address_7bit, uint8_t reg, uint8_t *value);
OpenRf1Status mpu6050_write_register(uint8_t address_7bit, uint8_t reg, uint8_t value);
OpenRf1Status mpu6050_write_register_readback(
    uint8_t address_7bit,
    uint8_t reg,
    uint8_t value,
    uint8_t *readback
);
OpenRf1Status mpu6050_read_who_am_i(uint8_t address_7bit, uint8_t *who_am_i);
OpenRf1Status mpu6050_wake_for_bringup(uint8_t address_7bit, uint8_t *pwr_mgmt_1_readback);
OpenRf1Status mpu6050_configure_for_bringup(uint8_t address_7bit, Mpu6050RegisterConfig *readback);
OpenRf1Status mpu6050_read_configuration(uint8_t address_7bit, Mpu6050RegisterConfig *readback);
OpenRf1Status mpu6050_read_raw_sample(uint8_t address_7bit, Mpu6050RawSample *sample);
int32_t mpu6050_accel_raw_to_mg(int16_t raw, Mpu6050AccelRange range);
int32_t mpu6050_gyro_raw_to_mdps(int16_t raw, Mpu6050GyroRange range);
int32_t mpu6050_temperature_raw_to_centideg_c(int16_t raw);
