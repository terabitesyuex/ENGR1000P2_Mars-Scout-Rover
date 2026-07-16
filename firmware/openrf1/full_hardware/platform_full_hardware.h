#pragma once

#include <stdint.h>

void openrf1_full_platform_init(void);
uint32_t openrf1_full_millis(void);
void openrf1_debug_write_bounded(const char *text, uint16_t max_bytes);
