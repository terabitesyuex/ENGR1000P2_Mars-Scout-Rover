#pragma once

#include <stdint.h>

uint8_t openrf1_encoder_platform_init(void);
uint32_t openrf1_encoder_millis(void);
void openrf1_encoder_read_raw(uint16_t raw_counts[4]);
uint8_t openrf1_encoder_console_write(const char *text);
