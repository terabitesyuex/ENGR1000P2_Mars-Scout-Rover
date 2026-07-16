#include "hcsr04.h"

#include "board_config.h"

void hcsr04_channel_init(Hcsr04Channel *channel, const char *sensor_id, uint8_t logical_channel) {
    if (channel == 0) {
        return;
    }
    channel->sensor_id = sensor_id;
    channel->logical_channel = logical_channel;
    channel->state = HCSR04_STATE_IDLE;
    channel->state_started_us = 0u;
    channel->echo_rise_us = 0u;
    channel->raw_echo_us = 0u;
    channel->distance_mm = 0u;
    channel->valid = 0u;
    channel->timeout_count = 0u;
}

OpenRf1Status hcsr04_start(Hcsr04Channel *channel, uint32_t now_us) {
    if (channel == 0) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    if (channel->state != HCSR04_STATE_IDLE) {
        return OPENRF1_STATUS_STALE;
    }
    channel->state = HCSR04_STATE_TRIGGER_HIGH;
    channel->state_started_us = now_us;
    channel->valid = 0u;
    channel->raw_echo_us = 0u;
    return OPENRF1_STATUS_OK;
}

OpenRf1Status hcsr04_on_echo_edge(Hcsr04Channel *channel, uint8_t high, uint32_t now_us) {
    if (channel == 0) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    if (channel->state == HCSR04_STATE_WAIT_RISING && high != 0u) {
        channel->echo_rise_us = now_us;
        channel->state = HCSR04_STATE_WAIT_FALLING;
        channel->state_started_us = now_us;
        return OPENRF1_STATUS_OK;
    }
    if (channel->state == HCSR04_STATE_WAIT_FALLING && high == 0u) {
        channel->raw_echo_us = now_us - channel->echo_rise_us;
        channel->distance_mm = hcsr04_echo_us_to_distance_mm(channel->raw_echo_us);
        channel->valid = 1u;
        channel->state = HCSR04_STATE_QUIET;
        channel->state_started_us = now_us;
        return OPENRF1_STATUS_OK;
    }
    return OPENRF1_STATUS_STALE;
}

OpenRf1Status hcsr04_poll(Hcsr04Channel *channel, uint32_t now_us) {
    if (channel == 0) {
        return OPENRF1_STATUS_INVALID_ARGUMENT;
    }
    if (channel->state == HCSR04_STATE_TRIGGER_HIGH &&
        (uint32_t)(now_us - channel->state_started_us) >= OPENRF1_HCSR04_TRIGGER_US) {
        channel->state = HCSR04_STATE_WAIT_RISING;
        channel->state_started_us = now_us;
        return OPENRF1_STATUS_OK;
    }
    if ((channel->state == HCSR04_STATE_WAIT_RISING || channel->state == HCSR04_STATE_WAIT_FALLING) &&
        (uint32_t)(now_us - channel->state_started_us) >= OPENRF1_HCSR04_TIMEOUT_US) {
        channel->valid = 0u;
        channel->raw_echo_us = 0u;
        channel->state = HCSR04_STATE_QUIET;
        channel->state_started_us = now_us;
        ++channel->timeout_count;
        return OPENRF1_STATUS_TIMEOUT;
    }
    if (channel->state == HCSR04_STATE_QUIET &&
        (uint32_t)(now_us - channel->state_started_us) >= OPENRF1_HCSR04_QUIET_TIME_US) {
        channel->state = HCSR04_STATE_IDLE;
        return OPENRF1_STATUS_OK;
    }
    return OPENRF1_STATUS_STALE;
}

uint16_t hcsr04_echo_us_to_distance_mm(uint32_t echo_us) {
    uint32_t distance_mm = (echo_us * 343u + 1000u) / 2000u;
    if (distance_mm > 0xFFFFu) {
        return 0xFFFFu;
    }
    return (uint16_t)distance_mm;
}
