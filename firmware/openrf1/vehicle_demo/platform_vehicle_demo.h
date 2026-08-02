#pragma once

#include <stdint.h>

#include "obstacle_control.h"

typedef enum {
    DEMO_CONSOLE_NO_LINE = 0,
    DEMO_CONSOLE_LINE_READY,
    DEMO_CONSOLE_FAULT
} DemoConsoleReadResult;

uint8_t demo_platform_init(void);
uint32_t demo_platform_millis(void);
uint32_t demo_platform_micros(void);
void demo_platform_trigger_write(uint8_t channel, uint8_t high);
uint8_t demo_platform_echo_read(uint8_t channel);
void demo_platform_set_motion(DemoMotion motion);
void demo_platform_stop_all(void);
DemoConsoleReadResult demo_platform_console_read_line(char *line, uint16_t line_bytes);
uint8_t demo_platform_console_write(const char *text);
