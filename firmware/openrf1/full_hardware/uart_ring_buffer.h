#pragma once

#include <stdint.h>

#include "openrf1_status.h"

typedef struct {
    uint8_t *storage;
    uint16_t capacity;
    volatile uint16_t head;
    volatile uint16_t tail;
    volatile uint32_t bytes_in;
    volatile uint32_t bytes_out;
    volatile uint32_t overflow_count;
} OpenRf1RingBuffer;

OpenRf1Status openrf1_ring_init(OpenRf1RingBuffer *ring, uint8_t *storage, uint16_t capacity);
uint16_t openrf1_ring_available(const OpenRf1RingBuffer *ring);
uint16_t openrf1_ring_free(const OpenRf1RingBuffer *ring);
OpenRf1Status openrf1_ring_push(OpenRf1RingBuffer *ring, uint8_t value);
OpenRf1Status openrf1_ring_pop(OpenRf1RingBuffer *ring, uint8_t *value);
uint16_t openrf1_ring_read(OpenRf1RingBuffer *ring, uint8_t *output, uint16_t max_bytes);
uint16_t openrf1_ring_write(OpenRf1RingBuffer *ring, const uint8_t *data, uint16_t length);
