#include "uart_ring_buffer.h"

static uint8_t is_power_of_two(uint16_t value) {
    return value != 0u && (value & (uint16_t)(value - 1u)) == 0u;
}

OpenRf1Status openrf1_ring_init(OpenRf1RingBuffer *ring, uint8_t *storage, uint16_t capacity) {
    if (ring == 0 || storage == 0 || !is_power_of_two(capacity)) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    ring->storage = storage;
    ring->capacity = capacity;
    ring->head = 0u;
    ring->tail = 0u;
    ring->bytes_in = 0u;
    ring->bytes_out = 0u;
    ring->overflow_count = 0u;
    return OPENRF1_STATUS_OK;
}

uint16_t openrf1_ring_available(const OpenRf1RingBuffer *ring) {
    if (ring == 0 || ring->capacity == 0u) {
        return 0u;
    }
    return (uint16_t)((ring->head - ring->tail) & (uint16_t)(ring->capacity - 1u));
}

uint16_t openrf1_ring_free(const OpenRf1RingBuffer *ring) {
    if (ring == 0 || ring->capacity == 0u) {
        return 0u;
    }
    return (uint16_t)(ring->capacity - 1u - openrf1_ring_available(ring));
}

OpenRf1Status openrf1_ring_push(OpenRf1RingBuffer *ring, uint8_t value) {
    if (ring == 0 || ring->storage == 0 || ring->capacity == 0u) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    uint16_t next = (uint16_t)((ring->head + 1u) & (uint16_t)(ring->capacity - 1u));
    if (next == ring->tail) {
        ++ring->overflow_count;
        return OPENRF1_STATUS_OVERFLOW;
    }
    ring->storage[ring->head] = value;
    ring->head = next;
    ++ring->bytes_in;
    return OPENRF1_STATUS_OK;
}

OpenRf1Status openrf1_ring_pop(OpenRf1RingBuffer *ring, uint8_t *value) {
    if (ring == 0 || value == 0 || ring->storage == 0 || ring->capacity == 0u) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    if (ring->tail == ring->head) {
        return OPENRF1_STATUS_STALE;
    }
    *value = ring->storage[ring->tail];
    ring->tail = (uint16_t)((ring->tail + 1u) & (uint16_t)(ring->capacity - 1u));
    ++ring->bytes_out;
    return OPENRF1_STATUS_OK;
}

uint16_t openrf1_ring_read(OpenRf1RingBuffer *ring, uint8_t *output, uint16_t max_bytes) {
    if (ring == 0 || output == 0 || max_bytes == 0u) {
        return 0u;
    }
    uint16_t count = 0u;
    while (count < max_bytes) {
        if (openrf1_ring_pop(ring, &output[count]) != OPENRF1_STATUS_OK) {
            break;
        }
        ++count;
    }
    return count;
}

uint16_t openrf1_ring_write(OpenRf1RingBuffer *ring, const uint8_t *data, uint16_t length) {
    if (ring == 0 || data == 0) {
        return 0u;
    }
    uint16_t written = 0u;
    while (written < length) {
        if (openrf1_ring_push(ring, data[written]) != OPENRF1_STATUS_OK) {
            break;
        }
        ++written;
    }
    return written;
}
