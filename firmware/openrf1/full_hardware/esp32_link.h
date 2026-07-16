#pragma once

#include <stdint.h>

#include "openrf1_status.h"

#define ESP32_LINK_MAGIC_0 ((uint8_t)0xA5u)
#define ESP32_LINK_MAGIC_1 ((uint8_t)0x5Au)
#define ESP32_LINK_VERSION ((uint8_t)1u)
#define ESP32_LINK_HEADER_BYTES ((uint16_t)14u)
#define ESP32_LINK_CRC_BYTES ((uint16_t)2u)

typedef enum {
    ESP32_LINK_MSG_HEARTBEAT = 1,
    ESP32_LINK_MSG_COMMAND_ACK = 2,
    ESP32_LINK_MSG_SUBSYSTEM_STATUS = 3,
    ESP32_LINK_MSG_LINK_STATUS = 4,
    ESP32_LINK_MSG_LIDAR_CHUNK = 5
} Esp32LinkMessageType;

typedef struct {
    uint8_t message_type;
    uint8_t flags;
    uint16_t sequence;
    uint32_t timestamp_ms;
    const uint8_t *payload;
    uint16_t payload_length;
} Esp32LinkFrame;

typedef struct {
    uint32_t frames_encoded;
    uint32_t frames_decoded;
    uint32_t crc_error_count;
    uint32_t malformed_count;
    uint32_t sequence_gap_count;
    uint16_t expected_rx_sequence;
    uint8_t have_sequence;
} Esp32LinkStats;

uint16_t esp32_link_crc16_ccitt_false(const uint8_t *data, uint16_t length);
OpenRf1Status esp32_link_encode(
    const Esp32LinkFrame *frame,
    uint8_t *output,
    uint16_t output_capacity,
    uint16_t *written
);
void esp32_link_stats_init(Esp32LinkStats *stats);
OpenRf1Status esp32_link_validate_sequence(Esp32LinkStats *stats, uint16_t sequence);
