#pragma once

#include <stdint.h>

void openrf1_bmp280_platform_init(void);
uint32_t openrf1_bmp280_millis(void);
void openrf1_bmp280_debug_write_bounded(const char *text, uint16_t max_bytes);
