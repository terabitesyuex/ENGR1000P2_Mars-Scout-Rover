#pragma once

#include <stdint.h>

/* Inventory only. Sensor GPIO/UART integration belongs in board_config.h. */
#define OPENRF1_MPU6050_COUNT ((uint8_t)1u)
#define OPENRF1_BMP280_COUNT ((uint8_t)1u)
#define OPENRF1_BH1750_COUNT ((uint8_t)1u)
#define OPENRF1_HCSR04_COUNT ((uint8_t)3u)
#define OPENRF1_TCRT5000_COUNT ((uint8_t)2u)
#define OPENRF1_HALL_SENSOR_COUNT ((uint8_t)1u)
#define OPENRF1_RPLIDAR_C1_COUNT ((uint8_t)1u)

/* Existing isolated bring-up code remains the source of sensor-level facts. */
#define OPENRF1_SENSOR_MANAGER_INTEGRATION_READY ((uint8_t)0u)
#define OPENRF1_SHARED_I2C_CONCURRENCY_VERIFIED ((uint8_t)0u)
#define OPENRF1_THREE_HCSR04_SIMULTANEOUS_PATHS_VERIFIED ((uint8_t)0u)
