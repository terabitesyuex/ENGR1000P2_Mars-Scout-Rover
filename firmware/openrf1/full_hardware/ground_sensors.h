#pragma once

#include <stdint.h>

#include "digital_filter.h"

#define OPENRF1_GROUND_SENSOR_COUNT ((uint8_t)2u)

typedef struct {
    const char *sensor_id;
    OpenRf1DigitalFilter filter;
} OpenRf1GroundSensor;

typedef struct {
    OpenRf1GroundSensor sensors[OPENRF1_GROUND_SENSOR_COUNT];
} OpenRf1GroundSensors;

void openrf1_ground_sensors_init(OpenRf1GroundSensors *ground, uint32_t now_ms);
void openrf1_ground_sensors_update_raw_mask(OpenRf1GroundSensors *ground, uint8_t raw_mask, uint32_t now_ms);
