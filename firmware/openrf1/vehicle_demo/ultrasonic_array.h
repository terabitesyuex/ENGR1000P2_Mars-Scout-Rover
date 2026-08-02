#pragma once

#include <stdint.h>

#include "obstacle_control.h"

typedef enum {
    DEMO_ULTRASONIC_IDLE = 0,
    DEMO_ULTRASONIC_WAIT_LOW,
    DEMO_ULTRASONIC_SETTLE_LOW,
    DEMO_ULTRASONIC_TRIGGER_HIGH,
    DEMO_ULTRASONIC_WAIT_RISE,
    DEMO_ULTRASONIC_WAIT_FALL
} DemoUltrasonicState;

typedef struct {
    DemoUltrasonicState state;
    DemoSensorStatus status;
    uint32_t state_started_us;
    uint32_t echo_rise_us;
    uint32_t raw_echo_us;
    uint16_t distance_mm;
    uint32_t updated_ms;
} DemoUltrasonicChannel;

typedef void (*DemoUltrasonicTriggerWriteFn)(uint8_t channel, uint8_t high);
typedef uint8_t (*DemoUltrasonicEchoReadFn)(uint8_t channel);

typedef struct {
    DemoUltrasonicTriggerWriteFn trigger_write;
    DemoUltrasonicEchoReadFn echo_read;
} DemoUltrasonicHardware;

typedef struct {
    DemoUltrasonicChannel channels[3];
    DemoUltrasonicHardware hardware;
    uint32_t next_start_us;
    uint8_t active_channel;
    uint8_t next_channel;
} DemoUltrasonicArray;

uint8_t demo_ultrasonic_array_init(
    DemoUltrasonicArray *array,
    const DemoUltrasonicHardware *hardware,
    uint32_t now_us
);
void demo_ultrasonic_array_service(
    DemoUltrasonicArray *array,
    uint32_t now_us,
    uint32_t now_ms
);
void demo_ultrasonic_copy_samples(
    const DemoUltrasonicArray *array,
    DemoObstacleSample samples[3]
);
uint16_t demo_echo_us_to_distance_mm(uint32_t echo_us);
const char *demo_sensor_status_name(DemoSensorStatus status);
