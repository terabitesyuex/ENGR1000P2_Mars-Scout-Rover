#include "bmp280.h"

#include "i2c_bus.h"

#define BMP280_REG_CHIP_ID ((uint8_t)0xD0u)
#define BMP280_REG_CALIB_START ((uint8_t)0x88u)
#define BMP280_REG_PRESS_MSB ((uint8_t)0xF7u)

static uint16_t u16_le(uint8_t lsb, uint8_t msb) {
    return (uint16_t)((uint16_t)lsb | ((uint16_t)msb << 8u));
}

static int16_t s16_le(uint8_t lsb, uint8_t msb) {
    return (int16_t)u16_le(lsb, msb);
}

OpenRf1Status bmp280_validate_chip_id(uint8_t chip_id) {
    return chip_id == BMP280_CHIP_ID_EXPECTED ? OPENRF1_STATUS_OK : OPENRF1_STATUS_BAD_ID;
}

OpenRf1Status bmp280_read_chip_id(uint8_t address_7bit, uint8_t *chip_id) {
    if (chip_id == 0) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    uint8_t reg = BMP280_REG_CHIP_ID;
    OpenRf1Status status = openrf1_i2c_write_read(address_7bit, &reg, 1u, chip_id, 1u);
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    return bmp280_validate_chip_id(*chip_id);
}

OpenRf1Status bmp280_read_calibration(uint8_t address_7bit, Bmp280Calibration *calibration) {
    if (calibration == 0) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    uint8_t reg = BMP280_REG_CALIB_START;
    uint8_t buffer[24u];
    OpenRf1Status status = openrf1_i2c_write_read(address_7bit, &reg, 1u, buffer, (uint8_t)sizeof(buffer));
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    calibration->dig_t1 = u16_le(buffer[0], buffer[1]);
    calibration->dig_t2 = s16_le(buffer[2], buffer[3]);
    calibration->dig_t3 = s16_le(buffer[4], buffer[5]);
    calibration->dig_p1 = u16_le(buffer[6], buffer[7]);
    calibration->dig_p2 = s16_le(buffer[8], buffer[9]);
    calibration->dig_p3 = s16_le(buffer[10], buffer[11]);
    calibration->dig_p4 = s16_le(buffer[12], buffer[13]);
    calibration->dig_p5 = s16_le(buffer[14], buffer[15]);
    calibration->dig_p6 = s16_le(buffer[16], buffer[17]);
    calibration->dig_p7 = s16_le(buffer[18], buffer[19]);
    calibration->dig_p8 = s16_le(buffer[20], buffer[21]);
    calibration->dig_p9 = s16_le(buffer[22], buffer[23]);
    return OPENRF1_STATUS_OK;
}

OpenRf1Status bmp280_read_raw_sample(uint8_t address_7bit, Bmp280RawSample *raw_sample) {
    if (raw_sample == 0) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    uint8_t reg = BMP280_REG_PRESS_MSB;
    uint8_t buffer[6u];
    OpenRf1Status status = openrf1_i2c_write_read(address_7bit, &reg, 1u, buffer, (uint8_t)sizeof(buffer));
    if (status != OPENRF1_STATUS_OK) {
        return status;
    }
    raw_sample->adc_pressure =
        (int32_t)((((uint32_t)buffer[0]) << 12u) | (((uint32_t)buffer[1]) << 4u) | (((uint32_t)buffer[2]) >> 4u));
    raw_sample->adc_temperature =
        (int32_t)((((uint32_t)buffer[3]) << 12u) | (((uint32_t)buffer[4]) << 4u) | (((uint32_t)buffer[5]) >> 4u));
    return OPENRF1_STATUS_OK;
}

OpenRf1Status bmp280_compensate(
    const Bmp280Calibration *calibration,
    const Bmp280RawSample *raw_sample,
    Bmp280CompensatedSample *compensated
) {
    if (calibration == 0 || raw_sample == 0 || compensated == 0 || calibration->dig_p1 == 0u) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }

    int32_t var1 = ((((raw_sample->adc_temperature >> 3) - ((int32_t)calibration->dig_t1 << 1))) *
                    ((int32_t)calibration->dig_t2)) >> 11;
    int32_t var2 = (((((raw_sample->adc_temperature >> 4) - ((int32_t)calibration->dig_t1)) *
                      ((raw_sample->adc_temperature >> 4) - ((int32_t)calibration->dig_t1))) >> 12) *
                    ((int32_t)calibration->dig_t3)) >> 14;
    int32_t t_fine = var1 + var2;
    compensated->temperature_centideg_c = (int32_t)((t_fine * 5 + 128) >> 8);
    compensated->t_fine = t_fine;

    int64_t p_var1 = ((int64_t)t_fine) - 128000;
    int64_t p_var2 = p_var1 * p_var1 * (int64_t)calibration->dig_p6;
    p_var2 = p_var2 + ((p_var1 * (int64_t)calibration->dig_p5) << 17);
    p_var2 = p_var2 + (((int64_t)calibration->dig_p4) << 35);
    p_var1 = ((p_var1 * p_var1 * (int64_t)calibration->dig_p3) >> 8) +
             ((p_var1 * (int64_t)calibration->dig_p2) << 12);
    p_var1 = (((((int64_t)1) << 47) + p_var1)) * ((int64_t)calibration->dig_p1) >> 33;
    if (p_var1 == 0) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    int64_t pressure = 1048576 - raw_sample->adc_pressure;
    pressure = (((pressure << 31) - p_var2) * 3125) / p_var1;
    p_var1 = (((int64_t)calibration->dig_p9) * (pressure >> 13) * (pressure >> 13)) >> 25;
    p_var2 = (((int64_t)calibration->dig_p8) * pressure) >> 19;
    pressure = ((pressure + p_var1 + p_var2) >> 8) + (((int64_t)calibration->dig_p7) << 4);
    compensated->pressure_pa = (uint32_t)((pressure + 128) >> 8);
    return OPENRF1_STATUS_OK;
}
