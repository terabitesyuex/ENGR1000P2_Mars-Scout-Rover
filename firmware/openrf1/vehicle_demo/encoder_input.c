#include "encoder_input.h"

#include <limits.h>

int32_t demo_encoder_wrapped_delta(uint16_t current_count, uint16_t previous_count) {
    uint16_t unsigned_delta = (uint16_t)(current_count - previous_count);
    if (unsigned_delta <= (uint16_t)INT16_MAX) {
        return (int32_t)unsigned_delta;
    }
    return (int32_t)unsigned_delta - 65536;
}

void demo_encoder_input_init(
    DemoEncoderInput *input,
    const uint16_t raw_counts[DEMO_ENCODER_CHANNEL_COUNT],
    uint32_t now_ms
) {
    uint8_t index;
    if (input == 0 || raw_counts == 0) {
        return;
    }
    for (index = 0u; index < DEMO_ENCODER_CHANNEL_COUNT; ++index) {
        input->channels[index].raw_count = raw_counts[index];
        input->channels[index].delta_count = 0;
        input->channels[index].cumulative_count = 0;
    }
    input->timestamp_ms = now_ms;
    input->interval_ms = 0u;
    input->initialized = 1u;
    input->sample_valid = 0u;
    input->count_range_error = 0u;
}

uint8_t demo_encoder_input_update(
    DemoEncoderInput *input,
    const uint16_t raw_counts[DEMO_ENCODER_CHANNEL_COUNT],
    uint32_t now_ms
) {
    int32_t deltas[DEMO_ENCODER_CHANNEL_COUNT];
    int64_t cumulative[DEMO_ENCODER_CHANNEL_COUNT];
    uint32_t elapsed_ms;
    uint8_t index;

    if (input == 0 || raw_counts == 0 || input->initialized == 0u) {
        return 0u;
    }
    elapsed_ms = now_ms - input->timestamp_ms;
    if (elapsed_ms == 0u) {
        return 0u;
    }
    for (index = 0u; index < DEMO_ENCODER_CHANNEL_COUNT; ++index) {
        deltas[index] = demo_encoder_wrapped_delta(
            raw_counts[index],
            input->channels[index].raw_count
        );
        cumulative[index] = (int64_t)input->channels[index].cumulative_count +
                            (int64_t)deltas[index];
        if (cumulative[index] < (int64_t)INT32_MIN ||
            cumulative[index] > (int64_t)INT32_MAX) {
            input->count_range_error = 1u;
            input->sample_valid = 0u;
            return 0u;
        }
    }
    for (index = 0u; index < DEMO_ENCODER_CHANNEL_COUNT; ++index) {
        input->channels[index].raw_count = raw_counts[index];
        input->channels[index].delta_count = deltas[index];
        input->channels[index].cumulative_count = (int32_t)cumulative[index];
    }
    input->timestamp_ms = now_ms;
    input->interval_ms = elapsed_ms;
    input->sample_valid = 1u;
    return 1u;
}
