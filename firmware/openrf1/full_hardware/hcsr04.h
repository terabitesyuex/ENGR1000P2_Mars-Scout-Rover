#pragma once

#include <stdint.h>

#include "openrf1_status.h"

typedef enum {
    HCSR04_STATE_IDLE = 0,
    HCSR04_STATE_TRIGGER_HIGH,
    HCSR04_STATE_WAIT_RISING,
    HCSR04_STATE_WAIT_FALLING,
    HCSR04_STATE_QUIET
} Hcsr04State;

typedef struct {
    const char *sensor_id;
    uint8_t logical_channel;
    Hcsr04State state;
    uint32_t state_started_us;
    uint32_t echo_rise_us;
    uint32_t raw_echo_us;
    uint16_t distance_mm;
    uint8_t valid;
    uint32_t timeout_count;
} Hcsr04Channel;

void hcsr04_channel_init(Hcsr04Channel *channel, const char *sensor_id, uint8_t logical_channel);
OpenRf1Status hcsr04_start(Hcsr04Channel *channel, uint32_t now_us);
OpenRf1Status hcsr04_on_echo_edge(Hcsr04Channel *channel, uint8_t high, uint32_t now_us);
OpenRf1Status hcsr04_poll(Hcsr04Channel *channel, uint32_t now_us);
uint16_t hcsr04_echo_us_to_distance_mm(uint32_t echo_us);
