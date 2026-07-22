#pragma once

#include <stdint.h>

typedef enum {
    ENCODER_ID_FRONT_LEFT = 0,
    ENCODER_ID_FRONT_RIGHT,
    ENCODER_ID_REAR_LEFT,
    ENCODER_ID_REAR_RIGHT,
    ENCODER_ID_COUNT
} EncoderId;

typedef enum {
    ENCODER_STATUS_OK = 0,
    ENCODER_STATUS_INVALID_ARGUMENT,
    ENCODER_STATUS_INVALID_ENCODER_ID,
    ENCODER_STATUS_NOT_INITIALIZED,
    ENCODER_STATUS_NOT_READY,
    ENCODER_STATUS_ZERO_SAMPLE_INTERVAL,
    ENCODER_STATUS_COUNT_RANGE_ERROR,
    ENCODER_STATUS_BACKEND_ERROR
} EncoderStatus;

typedef EncoderStatus (*EncoderReadCountFn)(
    void *context,
    EncoderId encoder_id,
    int32_t *count
);

typedef struct {
    EncoderReadCountFn read_count;
} EncoderHardwareOps;

typedef struct {
    int32_t raw_count;
    int32_t zero_offset_count;
    int32_t count;
    int32_t speed_counts_per_second;
    uint32_t last_sample_ms;
    uint8_t count_valid;
    uint8_t sample_valid;
    uint8_t speed_valid;
} EncoderChannelState;

typedef struct {
    EncoderHardwareOps hardware;
    void *hardware_context;
    EncoderChannelState channels[ENCODER_ID_COUNT];
    uint8_t initialized;
} EncoderBank;

EncoderStatus encoder_bank_init(
    EncoderBank *bank,
    const EncoderHardwareOps *hardware,
    void *hardware_context
);
EncoderStatus encoder_update(EncoderBank *bank, EncoderId encoder_id, uint32_t timestamp_ms);
EncoderStatus encoder_update_all(EncoderBank *bank, uint32_t timestamp_ms);
EncoderStatus encoder_get_count(const EncoderBank *bank, EncoderId encoder_id, int32_t *count);
EncoderStatus encoder_reset(EncoderBank *bank, EncoderId encoder_id);
EncoderStatus encoder_reset_all(EncoderBank *bank);
EncoderStatus encoder_get_speed(
    const EncoderBank *bank,
    EncoderId encoder_id,
    int32_t *speed_counts_per_second
);
