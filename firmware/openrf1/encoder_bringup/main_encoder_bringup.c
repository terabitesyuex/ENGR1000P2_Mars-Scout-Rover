#include "board_config.h"
#include "platform_encoder_bringup.h"

#include "encoder_input.h"

#include <stdio.h>

static DemoEncoderInput g_encoders;
static uint16_t g_raw_counts[DEMO_ENCODER_CHANNEL_COUNT];
static char g_telemetry[OPENRF1_ENCODER_BRINGUP_TELEMETRY_BUFFER_BYTES];
static uint32_t g_sequence;
static uint32_t g_next_sample_ms;

static uint8_t emit_identity(uint32_t now_ms) {
    int written = snprintf(
        g_telemetry,
        sizeof(g_telemetry),
        "{\"sequence\":%lu,\"timestamp_ms\":%lu,"
        "\"message_type\":\"vehicle_demo_identity\","
        "\"status\":\"software_ready\","
        "\"payload\":{\"target\":\"OpenRF1_Encoder_Bringup\","
        "\"board\":\"%s\",\"mapping_status\":\"%s\","
        "\"counter_bits\":%u,\"sample_period_ms\":%lu,"
        "\"motor_outputs_present\":false}}\r\n",
        (unsigned long)g_sequence,
        (unsigned long)now_ms,
        OPENRF1_ENCODER_BRINGUP_BOARD,
        OPENRF1_ENCODER_BRINGUP_MAPPING_STATUS,
        (unsigned int)OPENRF1_ENCODER_BRINGUP_COUNTER_BITS,
        (unsigned long)OPENRF1_ENCODER_BRINGUP_SAMPLE_PERIOD_MS
    );
    if (written <= 0 || written >= (int)sizeof(g_telemetry)) {
        return 0u;
    }
    if (openrf1_encoder_console_write(g_telemetry) == 0u) {
        return 0u;
    }
    ++g_sequence;
    return 1u;
}

static uint8_t emit_sample(void) {
    const DemoEncoderChannel *cn1 = &g_encoders.channels[DEMO_ENCODER_CN1];
    const DemoEncoderChannel *cn2 = &g_encoders.channels[DEMO_ENCODER_CN2];
    const DemoEncoderChannel *cn3 = &g_encoders.channels[DEMO_ENCODER_CN3];
    const DemoEncoderChannel *cn4 = &g_encoders.channels[DEMO_ENCODER_CN4];
    int written = snprintf(
        g_telemetry,
        sizeof(g_telemetry),
        "{\"sequence\":%lu,\"timestamp_ms\":%lu,"
        "\"message_type\":\"vehicle_demo_encoder\",\"status\":\"raw_counts\","
        "\"payload\":{\"mapping_status\":\"%s\",\"counter_bits\":%u,"
        "\"interval_ms\":%lu,\"direction_signs_verified\":false,"
        "\"cn1_raw_count\":%u,\"cn1_delta_count\":%ld,\"cn1_cumulative_count\":%ld,"
        "\"cn2_raw_count\":%u,\"cn2_delta_count\":%ld,\"cn2_cumulative_count\":%ld,"
        "\"cn3_raw_count\":%u,\"cn3_delta_count\":%ld,\"cn3_cumulative_count\":%ld,"
        "\"cn4_raw_count\":%u,\"cn4_delta_count\":%ld,\"cn4_cumulative_count\":%ld}}\r\n",
        (unsigned long)g_sequence,
        (unsigned long)g_encoders.timestamp_ms,
        OPENRF1_ENCODER_BRINGUP_MAPPING_STATUS,
        (unsigned int)OPENRF1_ENCODER_BRINGUP_COUNTER_BITS,
        (unsigned long)g_encoders.interval_ms,
        (unsigned int)cn1->raw_count, (long)cn1->delta_count, (long)cn1->cumulative_count,
        (unsigned int)cn2->raw_count, (long)cn2->delta_count, (long)cn2->cumulative_count,
        (unsigned int)cn3->raw_count, (long)cn3->delta_count, (long)cn3->cumulative_count,
        (unsigned int)cn4->raw_count, (long)cn4->delta_count, (long)cn4->cumulative_count
    );
    if (written <= 0 || written >= (int)sizeof(g_telemetry)) {
        return 0u;
    }
    if (openrf1_encoder_console_write(g_telemetry) == 0u) {
        return 0u;
    }
    ++g_sequence;
    return 1u;
}

int main(void) {
    uint32_t now_ms;
    if (openrf1_encoder_platform_init() == 0u) {
        for (;;) {
        }
    }
    now_ms = openrf1_encoder_millis();
    openrf1_encoder_read_raw(g_raw_counts);
    demo_encoder_input_init(&g_encoders, g_raw_counts, now_ms);
    g_sequence = 0u;
    g_next_sample_ms = now_ms + OPENRF1_ENCODER_BRINGUP_SAMPLE_PERIOD_MS;
    (void)emit_identity(now_ms);

    for (;;) {
        now_ms = openrf1_encoder_millis();
        if ((int32_t)(now_ms - g_next_sample_ms) >= 0) {
            g_next_sample_ms = now_ms + OPENRF1_ENCODER_BRINGUP_SAMPLE_PERIOD_MS;
            openrf1_encoder_read_raw(g_raw_counts);
            if (demo_encoder_input_update(&g_encoders, g_raw_counts, now_ms) != 0u) {
                (void)emit_sample();
            }
        }
    }
}
