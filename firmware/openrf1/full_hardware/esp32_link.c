#include "esp32_link.h"

#include "board_config.h"

static void write_u16_le(uint8_t *output, uint16_t value) {
    output[0] = (uint8_t)(value & 0xFFu);
    output[1] = (uint8_t)((value >> 8u) & 0xFFu);
}

static void write_u32_le(uint8_t *output, uint32_t value) {
    output[0] = (uint8_t)(value & 0xFFu);
    output[1] = (uint8_t)((value >> 8u) & 0xFFu);
    output[2] = (uint8_t)((value >> 16u) & 0xFFu);
    output[3] = (uint8_t)((value >> 24u) & 0xFFu);
}

uint16_t esp32_link_crc16_ccitt_false(const uint8_t *data, uint16_t length) {
    uint16_t crc = 0xFFFFu;
    for (uint16_t index = 0u; index < length; ++index) {
        crc ^= (uint16_t)data[index] << 8u;
        for (uint8_t bit = 0u; bit < 8u; ++bit) {
            if ((crc & 0x8000u) != 0u) {
                crc = (uint16_t)((crc << 1u) ^ 0x1021u);
            } else {
                crc = (uint16_t)(crc << 1u);
            }
        }
    }
    return crc;
}

OpenRf1Status esp32_link_encode(
    const Esp32LinkFrame *frame,
    uint8_t *output,
    uint16_t output_capacity,
    uint16_t *written
) {
    if (frame == 0 || output == 0 || written == 0 ||
        (frame->payload_length > 0u && frame->payload == 0) ||
        frame->payload_length > OPENRF1_ESP32_MAX_PAYLOAD_BYTES) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    uint16_t total = (uint16_t)(ESP32_LINK_HEADER_BYTES + frame->payload_length + ESP32_LINK_CRC_BYTES);
    if (output_capacity < total) {
        return OPENRF1_STATUS_OVERFLOW;
    }
    output[0] = ESP32_LINK_MAGIC_0;
    output[1] = ESP32_LINK_MAGIC_1;
    output[2] = ESP32_LINK_VERSION;
    output[3] = frame->message_type;
    output[4] = frame->flags;
    output[5] = 0u;
    write_u16_le(&output[6], frame->sequence);
    write_u32_le(&output[8], frame->timestamp_ms);
    write_u16_le(&output[12], frame->payload_length);
    for (uint16_t index = 0u; index < frame->payload_length; ++index) {
        output[ESP32_LINK_HEADER_BYTES + index] = frame->payload[index];
    }
    uint16_t crc_region_len = (uint16_t)(ESP32_LINK_HEADER_BYTES - 2u + frame->payload_length);
    uint16_t crc = esp32_link_crc16_ccitt_false(&output[2], crc_region_len);
    write_u16_le(&output[ESP32_LINK_HEADER_BYTES + frame->payload_length], crc);
    *written = total;
    return OPENRF1_STATUS_OK;
}

void esp32_link_stats_init(Esp32LinkStats *stats) {
    if (stats == 0) {
        return;
    }
    stats->frames_encoded = 0u;
    stats->frames_decoded = 0u;
    stats->crc_error_count = 0u;
    stats->malformed_count = 0u;
    stats->sequence_gap_count = 0u;
    stats->expected_rx_sequence = 0u;
    stats->have_sequence = 0u;
}

OpenRf1Status esp32_link_validate_sequence(Esp32LinkStats *stats, uint16_t sequence) {
    if (stats == 0) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    if (stats->have_sequence == 0u) {
        stats->expected_rx_sequence = (uint16_t)(sequence + 1u);
        stats->have_sequence = 1u;
        return OPENRF1_STATUS_OK;
    }
    if (sequence != stats->expected_rx_sequence) {
        ++stats->sequence_gap_count;
        stats->expected_rx_sequence = (uint16_t)(sequence + 1u);
        return OPENRF1_STATUS_STALE;
    }
    stats->expected_rx_sequence = (uint16_t)(stats->expected_rx_sequence + 1u);
    return OPENRF1_STATUS_OK;
}
