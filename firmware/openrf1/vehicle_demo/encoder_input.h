#pragma once

#include <stdint.h>

#define DEMO_ENCODER_CHANNEL_COUNT ((uint8_t)4u)

typedef enum {
    DEMO_ENCODER_CN1 = 0,
    DEMO_ENCODER_CN2,
    DEMO_ENCODER_CN3,
    DEMO_ENCODER_CN4
} DemoEncoderChannelId;

typedef struct {
    uint16_t raw_count;
    int32_t delta_count;
    int32_t cumulative_count;
} DemoEncoderChannel;

typedef struct {
    DemoEncoderChannel channels[DEMO_ENCODER_CHANNEL_COUNT];
    uint32_t timestamp_ms;
    uint32_t interval_ms;
    uint8_t initialized;
    uint8_t sample_valid;
    uint8_t count_range_error;
} DemoEncoderInput;

int32_t demo_encoder_wrapped_delta(uint16_t current_count, uint16_t previous_count);
void demo_encoder_input_init(
    DemoEncoderInput *input,
    const uint16_t raw_counts[DEMO_ENCODER_CHANNEL_COUNT],
    uint32_t now_ms
);
uint8_t demo_encoder_input_update(
    DemoEncoderInput *input,
    const uint16_t raw_counts[DEMO_ENCODER_CHANNEL_COUNT],
    uint32_t now_ms
);
