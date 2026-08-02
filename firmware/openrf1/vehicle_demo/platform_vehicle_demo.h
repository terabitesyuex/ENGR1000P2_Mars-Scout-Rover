#pragma once

#include <stdint.h>

#include "obstacle_control.h"

typedef enum {
    DEMO_CONSOLE_NO_LINE = 0,
    DEMO_CONSOLE_LINE_READY,
    DEMO_CONSOLE_FAULT
} DemoConsoleReadResult;

typedef struct {
    uint16_t ccr1;
    uint16_t ccr2;
    uint16_t ccr3;
    uint16_t ccr4;
    uint32_t timer_cr1;
    uint32_t timer_ccer;
    uint32_t timer_bdtr;
    uint32_t gpio_c_crl;
    uint32_t gpio_c_crh;
    uint32_t afio_mapr;
} DemoMotorDiagnostics;

uint8_t demo_platform_init(void);
uint32_t demo_platform_millis(void);
uint32_t demo_platform_micros(void);
void demo_platform_trigger_write(uint8_t channel, uint8_t high);
uint8_t demo_platform_echo_read(uint8_t channel);
uint8_t demo_platform_hall_read(void);
void demo_platform_encoder_read_raw(uint16_t raw_counts[4]);
void demo_platform_set_motion(DemoMotion motion);
void demo_platform_stop_all(void);
void demo_platform_read_motor_diagnostics(DemoMotorDiagnostics *diagnostics);
DemoConsoleReadResult demo_platform_console_read_line(char *line, uint16_t line_bytes);
uint8_t demo_platform_console_write(const char *text);
