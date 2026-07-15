#pragma once

#include <stdint.h>

uint32_t openrf1_millis(void);
void openrf1_platform_init(void);
void openrf1_usart1_write(const char *text);
