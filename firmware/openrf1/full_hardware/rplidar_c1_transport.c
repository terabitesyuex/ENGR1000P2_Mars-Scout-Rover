#include "rplidar_c1_transport.h"

#include "board_config.h"
#include "uart_ring_buffer.h"

static uint8_t g_rplidar_storage[OPENRF1_RPLIDAR_RX_BUFFER_BYTES];
static OpenRf1RingBuffer g_rplidar_ring;
static RplidarC1TransportStats g_rplidar_stats;

void rplidar_c1_transport_init(void) {
    (void)openrf1_ring_init(&g_rplidar_ring, g_rplidar_storage, OPENRF1_RPLIDAR_RX_BUFFER_BYTES);
    g_rplidar_stats.rx_bytes = 0u;
    g_rplidar_stats.bytes_read = 0u;
    g_rplidar_stats.overflow_count = 0u;
    g_rplidar_stats.framing_error_count = 0u;
    g_rplidar_stats.last_rx_tick_ms = 0u;
}

OpenRf1Status rplidar_c1_transport_on_rx_byte(uint8_t value, uint32_t tick_ms) {
    OpenRf1Status status = openrf1_ring_push(&g_rplidar_ring, value);
    ++g_rplidar_stats.rx_bytes;
    g_rplidar_stats.last_rx_tick_ms = tick_ms;
    if (status == OPENRF1_STATUS_OVERFLOW) {
        ++g_rplidar_stats.overflow_count;
    }
    return status;
}

uint16_t rplidar_c1_transport_read_chunk(uint8_t *output, uint16_t max_length, uint32_t *last_tick_ms) {
    uint16_t limit = max_length;
    if (limit > OPENRF1_RPLIDAR_CHUNK_BYTES) {
        limit = OPENRF1_RPLIDAR_CHUNK_BYTES;
    }
    uint16_t count = openrf1_ring_read(&g_rplidar_ring, output, limit);
    g_rplidar_stats.bytes_read += count;
    if (last_tick_ms != 0) {
        *last_tick_ms = g_rplidar_stats.last_rx_tick_ms;
    }
    return count;
}

RplidarC1TransportStats rplidar_c1_transport_stats(void) {
    g_rplidar_stats.overflow_count = g_rplidar_ring.overflow_count;
    return g_rplidar_stats;
}
