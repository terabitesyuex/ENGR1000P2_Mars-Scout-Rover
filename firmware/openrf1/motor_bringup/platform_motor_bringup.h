#pragma once

#include <stdint.h>

typedef enum {
    MOTOR_CONSOLE_NO_LINE = 0,
    MOTOR_CONSOLE_LINE_READY,
    MOTOR_CONSOLE_FAULT
} MotorConsoleReadResult;

uint8_t openrf1_motor_platform_init(void);
uint32_t openrf1_motor_millis(void);
void openrf1_motor_stop_all(void);
uint8_t openrf1_motor_apply(
    uint8_t connector,
    int8_t electrical_direction,
    uint16_t duty_permille
);
void openrf1_motor_read_encoder_raw(uint16_t raw_counts[4]);
uint8_t openrf1_motor_console_write(const char *text);
MotorConsoleReadResult openrf1_motor_console_read_line(
    char *line,
    uint16_t line_bytes
);

