#pragma once

#include <stdint.h>

#include "openrf1_status.h"

#define BMP280_CHIP_ID_EXPECTED ((uint8_t)0x58u)

typedef struct {
    uint16_t dig_t1;
    int16_t dig_t2;
    int16_t dig_t3;
    uint16_t dig_p1;
    int16_t dig_p2;
    int16_t dig_p3;
    int16_t dig_p4;
    int16_t dig_p5;
    int16_t dig_p6;
    int16_t dig_p7;
    int16_t dig_p8;
    int16_t dig_p9;
} Bmp280Calibration;

typedef struct {
    int32_t adc_temperature;
    int32_t adc_pressure;
} Bmp280RawSample;

typedef struct {
    int32_t temperature_centideg_c;
    uint32_t pressure_pa;
    int32_t t_fine;
} Bmp280CompensatedSample;

OpenRf1Status bmp280_validate_chip_id(uint8_t chip_id);
OpenRf1Status bmp280_read_chip_id(uint8_t address_7bit, uint8_t *chip_id);
OpenRf1Status bmp280_read_calibration(uint8_t address_7bit, Bmp280Calibration *calibration);
OpenRf1Status bmp280_read_raw_sample(uint8_t address_7bit, Bmp280RawSample *raw_sample);
OpenRf1Status bmp280_compensate(
    const Bmp280Calibration *calibration,
    const Bmp280RawSample *raw_sample,
    Bmp280CompensatedSample *compensated
);
