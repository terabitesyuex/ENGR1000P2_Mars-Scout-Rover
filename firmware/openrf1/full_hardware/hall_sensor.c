#include "hall_sensor.h"

#include "board_config.h"

void openrf1_hall_sensor_init(OpenRf1HallSensor *hall, uint32_t now_ms) {
    if (hall == 0) {
        return;
    }
    hall->sensor_id = "hall_1";
    openrf1_digital_filter_init(
        &hall->filter,
        0u,
        OPENRF1_DIGITAL_FILTER_STABLE_SAMPLES,
        now_ms
    );
}

void openrf1_hall_sensor_update_raw(OpenRf1HallSensor *hall, uint8_t raw_state, uint32_t now_ms) {
    if (hall == 0) {
        return;
    }
    (void)openrf1_digital_filter_update(&hall->filter, raw_state, now_ms);
}
