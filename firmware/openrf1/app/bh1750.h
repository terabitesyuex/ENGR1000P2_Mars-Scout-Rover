#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    BH1750_STATUS_OK = 0,
    BH1750_STATUS_TIMEOUT,
    BH1750_STATUS_NOT_INITIALIZED,
    BH1750_STATUS_HARDWARE_FAULT,
    BH1750_STATUS_STALE
} Bh1750Status;

typedef enum {
    BH1750_STATE_NOT_INITIALIZED = 0,
    BH1750_STATE_START_MEASUREMENT,
    BH1750_STATE_WAIT_MEASUREMENT,
    BH1750_STATE_READ_MEASUREMENT,
    BH1750_STATE_RETRY_BACKOFF
} Bh1750State;

typedef struct {
    Bh1750State state;
    uint32_t next_action_ms;
    uint32_t publish_period_ms;
    uint32_t measurement_time_ms;
    uint32_t retry_backoff_ms;
    uint32_t last_publish_ms;
    uint8_t initialized;
} Bh1750Context;

typedef struct {
    uint32_t timestamp_ms;
    Bh1750Status status;
    uint32_t illuminance_centilux;
    uint8_t has_illuminance;
} Bh1750Sample;

void bh1750_context_init(Bh1750Context *context);
uint8_t bh1750_write_address_from_7bit(uint8_t address_7bit);
uint8_t bh1750_read_address_from_7bit(uint8_t address_7bit);
uint16_t bh1750_raw_from_bytes(uint8_t msb, uint8_t lsb);
uint32_t bh1750_raw_to_centilux(uint16_t raw_count);
Bh1750Status bh1750_power_on(void);
Bh1750Status bh1750_power_down(void);
Bh1750Status bh1750_start_high_resolution_measurement(void);
Bh1750Status bh1750_read_raw_count(uint16_t *raw_count);
bool bh1750_task(Bh1750Context *context, uint32_t now_ms, Bh1750Sample *sample);
const char *bh1750_status_to_telemetry(Bh1750Status status);
