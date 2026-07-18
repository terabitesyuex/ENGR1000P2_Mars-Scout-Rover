#pragma once

#include <stdint.h>

#include "../full_hardware/openrf1_status.h"

OpenRf1Status openrf1_hcsr04_platform_init(void);
uint32_t openrf1_hcsr04_millis(void);
uint32_t openrf1_hcsr04_timer_now_us(void);
void openrf1_hcsr04_delay_us(uint16_t delay_us);
void openrf1_hcsr04_trigger_write(uint8_t high);
uint8_t openrf1_hcsr04_echo_read(void);
void openrf1_hcsr04_debug_write_bounded(const char *text, uint16_t max_bytes);
