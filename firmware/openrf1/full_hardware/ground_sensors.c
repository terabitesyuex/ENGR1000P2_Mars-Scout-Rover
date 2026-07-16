#include "ground_sensors.h"

#include "board_config.h"

void openrf1_ground_sensors_init(OpenRf1GroundSensors *ground, uint32_t now_ms) {
    if (ground == 0) {
        return;
    }
    ground->sensors[0].sensor_id = "tcrt5000_1";
    ground->sensors[1].sensor_id = "tcrt5000_2";
    for (uint8_t index = 0u; index < OPENRF1_GROUND_SENSOR_COUNT; ++index) {
        openrf1_digital_filter_init(
            &ground->sensors[index].filter,
            0u,
            OPENRF1_DIGITAL_FILTER_STABLE_SAMPLES,
            now_ms
        );
    }
}

void openrf1_ground_sensors_update_raw_mask(OpenRf1GroundSensors *ground, uint8_t raw_mask, uint32_t now_ms) {
    if (ground == 0) {
        return;
    }
    for (uint8_t index = 0u; index < OPENRF1_GROUND_SENSOR_COUNT; ++index) {
        uint8_t raw = (uint8_t)((raw_mask >> index) & 0x01u);
        (void)openrf1_digital_filter_update(&ground->sensors[index].filter, raw, now_ms);
    }
}
