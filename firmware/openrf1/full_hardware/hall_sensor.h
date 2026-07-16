#pragma once

#include <stdint.h>

#include "digital_filter.h"

typedef struct {
    const char *sensor_id;
    OpenRf1DigitalFilter filter;
} OpenRf1HallSensor;

void openrf1_hall_sensor_init(OpenRf1HallSensor *hall, uint32_t now_ms);
void openrf1_hall_sensor_update_raw(OpenRf1HallSensor *hall, uint8_t raw_state, uint32_t now_ms);
