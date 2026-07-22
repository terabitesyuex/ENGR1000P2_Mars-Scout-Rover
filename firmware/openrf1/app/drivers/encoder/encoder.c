#include "encoder.h"

#include <limits.h>

static uint8_t encoder_id_is_valid(EncoderId encoder_id) {
    return (uint8_t)((int)encoder_id >= 0 && encoder_id < ENCODER_ID_COUNT);
}

static EncoderStatus encoder_read_raw(
    EncoderBank *bank,
    EncoderId encoder_id,
    int32_t *raw_count
) {
    EncoderStatus backend_status;

    backend_status = bank->hardware.read_count(
        bank->hardware_context,
        encoder_id,
        raw_count
    );
    if (backend_status != ENCODER_STATUS_OK) {
        return ENCODER_STATUS_BACKEND_ERROR;
    }
    return ENCODER_STATUS_OK;
}

static uint8_t int64_fits_int32(int64_t value) {
    return (uint8_t)(value >= (int64_t)INT32_MIN && value <= (int64_t)INT32_MAX);
}

static int64_t encoder_wrapped_delta(int32_t current_count, int32_t previous_count) {
    uint32_t unsigned_delta = (uint32_t)current_count - (uint32_t)previous_count;

    if (unsigned_delta <= (uint32_t)INT32_MAX) {
        return (int64_t)unsigned_delta;
    }
    return (int64_t)unsigned_delta - ((int64_t)UINT32_MAX + 1);
}

EncoderStatus encoder_bank_init(
    EncoderBank *bank,
    const EncoderHardwareOps *hardware,
    void *hardware_context
) {
    EncoderId encoder_id;

    if (bank == 0 || hardware == 0 || hardware->read_count == 0) {
        return ENCODER_STATUS_INVALID_ARGUMENT;
    }

    bank->hardware = *hardware;
    bank->hardware_context = hardware_context;
    bank->initialized = 1u;
    for (encoder_id = ENCODER_ID_FRONT_LEFT; encoder_id < ENCODER_ID_COUNT; ++encoder_id) {
        EncoderChannelState *channel = &bank->channels[encoder_id];
        channel->raw_count = 0;
        channel->zero_offset_count = 0;
        channel->count = 0;
        channel->speed_counts_per_second = 0;
        channel->last_sample_ms = 0u;
        channel->count_valid = 0u;
        channel->sample_valid = 0u;
        channel->speed_valid = 0u;
    }
    return ENCODER_STATUS_OK;
}

EncoderStatus encoder_update(EncoderBank *bank, EncoderId encoder_id, uint32_t timestamp_ms) {
    EncoderChannelState *channel;
    EncoderStatus status;
    int32_t raw_count;
    int64_t delta_count;
    int64_t next_count;

    if (bank == 0) {
        return ENCODER_STATUS_INVALID_ARGUMENT;
    }
    if (bank->initialized == 0u) {
        return ENCODER_STATUS_NOT_INITIALIZED;
    }
    if (!encoder_id_is_valid(encoder_id)) {
        return ENCODER_STATUS_INVALID_ENCODER_ID;
    }

    status = encoder_read_raw(bank, encoder_id, &raw_count);
    if (status != ENCODER_STATUS_OK) {
        return status;
    }

    channel = &bank->channels[encoder_id];
    if (channel->count_valid == 0u) {
        channel->zero_offset_count = raw_count;
        channel->raw_count = raw_count;
        channel->count = 0;
        channel->speed_counts_per_second = 0;
        channel->last_sample_ms = timestamp_ms;
        channel->count_valid = 1u;
        channel->sample_valid = 1u;
        channel->speed_valid = 0u;
        return ENCODER_STATUS_OK;
    }

    delta_count = encoder_wrapped_delta(raw_count, channel->raw_count);
    next_count = (int64_t)channel->count + delta_count;
    if (!int64_fits_int32(next_count)) {
        return ENCODER_STATUS_COUNT_RANGE_ERROR;
    }

    if (channel->sample_valid == 0u) {
        channel->raw_count = raw_count;
        channel->count = (int32_t)next_count;
        channel->speed_counts_per_second = 0;
        channel->last_sample_ms = timestamp_ms;
        channel->sample_valid = 1u;
        channel->speed_valid = 0u;
        return ENCODER_STATUS_OK;
    }

    {
        uint32_t elapsed_ms = timestamp_ms - channel->last_sample_ms;
        int64_t speed_counts_per_second;

        if (elapsed_ms == 0u) {
            return ENCODER_STATUS_ZERO_SAMPLE_INTERVAL;
        }

        speed_counts_per_second = (delta_count * 1000) / (int64_t)elapsed_ms;
        if (!int64_fits_int32(speed_counts_per_second)) {
            return ENCODER_STATUS_COUNT_RANGE_ERROR;
        }

        channel->raw_count = raw_count;
        channel->count = (int32_t)next_count;
        channel->speed_counts_per_second = (int32_t)speed_counts_per_second;
        channel->last_sample_ms = timestamp_ms;
        channel->count_valid = 1u;
        channel->speed_valid = 1u;
    }
    return ENCODER_STATUS_OK;
}

EncoderStatus encoder_update_all(EncoderBank *bank, uint32_t timestamp_ms) {
    EncoderStatus first_error = ENCODER_STATUS_OK;
    EncoderId encoder_id;

    if (bank == 0) {
        return ENCODER_STATUS_INVALID_ARGUMENT;
    }
    for (encoder_id = ENCODER_ID_FRONT_LEFT; encoder_id < ENCODER_ID_COUNT; ++encoder_id) {
        EncoderStatus status = encoder_update(bank, encoder_id, timestamp_ms);
        if (status != ENCODER_STATUS_OK && first_error == ENCODER_STATUS_OK) {
            first_error = status;
        }
    }
    return first_error;
}

EncoderStatus encoder_get_count(const EncoderBank *bank, EncoderId encoder_id, int32_t *count) {
    const EncoderChannelState *channel;

    if (bank == 0 || count == 0) {
        return ENCODER_STATUS_INVALID_ARGUMENT;
    }
    if (bank->initialized == 0u) {
        return ENCODER_STATUS_NOT_INITIALIZED;
    }
    if (!encoder_id_is_valid(encoder_id)) {
        return ENCODER_STATUS_INVALID_ENCODER_ID;
    }

    channel = &bank->channels[encoder_id];
    if (channel->count_valid == 0u) {
        return ENCODER_STATUS_NOT_READY;
    }
    *count = channel->count;
    return ENCODER_STATUS_OK;
}

EncoderStatus encoder_reset(EncoderBank *bank, EncoderId encoder_id) {
    EncoderChannelState *channel;
    EncoderStatus status;
    int32_t raw_count;

    if (bank == 0) {
        return ENCODER_STATUS_INVALID_ARGUMENT;
    }
    if (bank->initialized == 0u) {
        return ENCODER_STATUS_NOT_INITIALIZED;
    }
    if (!encoder_id_is_valid(encoder_id)) {
        return ENCODER_STATUS_INVALID_ENCODER_ID;
    }

    status = encoder_read_raw(bank, encoder_id, &raw_count);
    if (status != ENCODER_STATUS_OK) {
        return status;
    }

    channel = &bank->channels[encoder_id];
    channel->raw_count = raw_count;
    channel->zero_offset_count = raw_count;
    channel->count = 0;
    channel->speed_counts_per_second = 0;
    channel->count_valid = 1u;
    channel->sample_valid = 0u;
    channel->speed_valid = 0u;
    return ENCODER_STATUS_OK;
}

EncoderStatus encoder_reset_all(EncoderBank *bank) {
    EncoderStatus first_error = ENCODER_STATUS_OK;
    EncoderId encoder_id;

    if (bank == 0) {
        return ENCODER_STATUS_INVALID_ARGUMENT;
    }
    for (encoder_id = ENCODER_ID_FRONT_LEFT; encoder_id < ENCODER_ID_COUNT; ++encoder_id) {
        EncoderStatus status = encoder_reset(bank, encoder_id);
        if (status != ENCODER_STATUS_OK && first_error == ENCODER_STATUS_OK) {
            first_error = status;
        }
    }
    return first_error;
}

EncoderStatus encoder_get_speed(
    const EncoderBank *bank,
    EncoderId encoder_id,
    int32_t *speed_counts_per_second
) {
    const EncoderChannelState *channel;

    if (bank == 0 || speed_counts_per_second == 0) {
        return ENCODER_STATUS_INVALID_ARGUMENT;
    }
    if (bank->initialized == 0u) {
        return ENCODER_STATUS_NOT_INITIALIZED;
    }
    if (!encoder_id_is_valid(encoder_id)) {
        return ENCODER_STATUS_INVALID_ENCODER_ID;
    }

    channel = &bank->channels[encoder_id];
    if (channel->speed_valid == 0u) {
        return ENCODER_STATUS_NOT_READY;
    }
    *speed_counts_per_second = channel->speed_counts_per_second;
    return ENCODER_STATUS_OK;
}
