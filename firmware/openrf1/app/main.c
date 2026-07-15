#include "main.h"

#include "bh1750.h"
#include "board_config.h"
#include "telemetry.h"

int main(void) {
    Bh1750Context bh1750;
    Bh1750Sample sample;
    uint32_t sequence = 0u;
    char telemetry_buffer[OPENRF1_TELEMETRY_BUFFER_BYTES];

    openrf1_platform_init();
    bh1750_context_init(&bh1750);

    while (1) {
        uint32_t now_ms = openrf1_millis();
        if (bh1750_task(&bh1750, now_ms, &sample)) {
            if (telemetry_format_bh1750(telemetry_buffer, sizeof(telemetry_buffer), sequence, &sample) == TELEMETRY_FORMAT_OK) {
                openrf1_usart1_write(telemetry_buffer);
                ++sequence;
            }
        }
    }
}
