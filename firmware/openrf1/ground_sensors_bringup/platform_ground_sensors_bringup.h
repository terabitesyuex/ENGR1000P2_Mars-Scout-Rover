#pragma once

#include <stdint.h>

#include "../full_hardware/openrf1_status.h"
#include "ground_sensors.h"

OpenRf1Status openrf1_ground_platform_init(void);
uint32_t openrf1_ground_millis(void);
GroundSensorsRawLevels openrf1_ground_read_levels(void);
void openrf1_ground_debug_write_bounded(const char *text, uint16_t max_bytes);
