#pragma once

#include <stdint.h>

#include "openrf1_status.h"

#define MPU6050_WHO_AM_I_EXPECTED ((uint8_t)0x68u)

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

OpenRf1Status mpu6050_validate_who_am_i(uint8_t who_am_i);
OpenRf1Status mpu6050_read_who_am_i(uint8_t address_7bit, uint8_t *who_am_i);
OpenRf1Status mpu6050_read_raw_sample(uint8_t address_7bit, Mpu6050RawSample *sample);
int32_t mpu6050_accel_raw_to_mg(int16_t raw, Mpu6050AccelRange range);
int32_t mpu6050_gyro_raw_to_mdps(int16_t raw, Mpu6050GyroRange range);
int32_t mpu6050_temperature_raw_to_centideg_c(int16_t raw);
