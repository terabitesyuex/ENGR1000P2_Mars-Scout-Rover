#pragma once

#include <stdint.h>

#include "openrf1_status.h"

typedef struct {
    uint32_t rx_bytes;
    uint32_t bytes_read;
    uint32_t overflow_count;
    uint32_t framing_error_count;
    uint32_t last_rx_tick_ms;
} RplidarC1TransportStats;

void rplidar_c1_transport_init(void);
OpenRf1Status rplidar_c1_transport_on_rx_byte(uint8_t value, uint32_t tick_ms);
uint16_t rplidar_c1_transport_read_chunk(uint8_t *output, uint16_t max_length, uint32_t *last_tick_ms);
RplidarC1TransportStats rplidar_c1_transport_stats(void);
