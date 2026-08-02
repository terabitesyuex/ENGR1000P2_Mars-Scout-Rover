#include "ultrasonic_array.h"

#include "demo_config.h"

#define DEMO_NO_ACTIVE_CHANNEL ((uint8_t)0xffu)

static uint8_t time_reached_us(uint32_t now_us, uint32_t deadline_us) {
    return (uint8_t)((int32_t)(now_us - deadline_us) >= 0);
}

static uint32_t elapsed_us(uint32_t start_us, uint32_t now_us) {
    return (uint32_t)(now_us - start_us);
}

uint16_t demo_echo_us_to_distance_mm(uint32_t echo_us) {
    uint32_t distance_mm;
    if (echo_us == 0u || echo_us >= OPENRF1_DEMO_ECHO_TIMEOUT_US) {
        return 0u;
    }
    distance_mm = (echo_us * 343u + 1000u) / 2000u;
    return distance_mm > UINT16_MAX ? UINT16_MAX : (uint16_t)distance_mm;
}

uint8_t demo_ultrasonic_array_init(
    DemoUltrasonicArray *array,
    const DemoUltrasonicHardware *hardware,
    uint32_t now_us
) {
    uint8_t index;
    if (array == 0 || hardware == 0 ||
        hardware->trigger_write == 0 || hardware->echo_read == 0) {
        return 0u;
    }
    array->hardware = *hardware;
    array->active_channel = DEMO_NO_ACTIVE_CHANNEL;
    array->next_channel = 0u;
    array->next_start_us = now_us;
    for (index = 0u; index < 3u; ++index) {
        array->hardware.trigger_write(index, 0u);
        array->channels[index].state = DEMO_ULTRASONIC_IDLE;
        array->channels[index].status = DEMO_SENSOR_NOT_READY;
        array->channels[index].state_started_us = now_us;
        array->channels[index].echo_rise_us = 0u;
        array->channels[index].raw_echo_us = 0u;
        array->channels[index].distance_mm = 0u;
        array->channels[index].updated_ms = 0u;
    }
    return 1u;
}

static void complete_channel(
    DemoUltrasonicArray *array,
    DemoSensorStatus status,
    uint32_t now_us,
    uint32_t now_ms
) {
    DemoUltrasonicChannel *channel = &array->channels[array->active_channel];
    array->hardware.trigger_write(array->active_channel, 0u);
    channel->status = status;
    channel->updated_ms = now_ms;
    channel->state = DEMO_ULTRASONIC_IDLE;
    if (status != DEMO_SENSOR_OK) {
        channel->raw_echo_us = 0u;
        channel->distance_mm = 0u;
    }
    array->next_channel = (uint8_t)((array->active_channel + 1u) % 3u);
    array->active_channel = DEMO_NO_ACTIVE_CHANNEL;
    array->next_start_us = now_us + OPENRF1_DEMO_INTER_CHANNEL_GAP_US;
}

static void start_channel(DemoUltrasonicArray *array, uint32_t now_us) {
    DemoUltrasonicChannel *channel;
    array->active_channel = array->next_channel;
    channel = &array->channels[array->active_channel];
    /* Keep the last completed sample valid while this next ping is in flight. */
    channel->state_started_us = now_us;
    array->hardware.trigger_write(array->active_channel, 0u);
    channel->state = array->hardware.echo_read(array->active_channel) != 0u ?
        DEMO_ULTRASONIC_WAIT_LOW : DEMO_ULTRASONIC_SETTLE_LOW;
}

void demo_ultrasonic_array_service(
    DemoUltrasonicArray *array,
    uint32_t now_us,
    uint32_t now_ms
) {
    DemoUltrasonicChannel *channel;
    uint32_t duration_us;

    if (array == 0) {
        return;
    }
    if (array->active_channel == DEMO_NO_ACTIVE_CHANNEL) {
        if (time_reached_us(now_us, array->next_start_us) != 0u) {
            start_channel(array, now_us);
        }
        return;
    }

    channel = &array->channels[array->active_channel];
    duration_us = elapsed_us(channel->state_started_us, now_us);

    switch (channel->state) {
        case DEMO_ULTRASONIC_WAIT_LOW:
            if (array->hardware.echo_read(array->active_channel) == 0u) {
                channel->state = DEMO_ULTRASONIC_SETTLE_LOW;
                channel->state_started_us = now_us;
            } else if (duration_us >= OPENRF1_DEMO_ECHO_TIMEOUT_US) {
                complete_channel(array, DEMO_SENSOR_ECHO_NOT_LOW, now_us, now_ms);
            }
            break;
        case DEMO_ULTRASONIC_SETTLE_LOW:
            if (duration_us >= OPENRF1_DEMO_TRIGGER_SETTLE_US) {
                array->hardware.trigger_write(array->active_channel, 1u);
                channel->state = DEMO_ULTRASONIC_TRIGGER_HIGH;
                channel->state_started_us = now_us;
            }
            break;
        case DEMO_ULTRASONIC_TRIGGER_HIGH:
            if (duration_us >= OPENRF1_DEMO_TRIGGER_PULSE_US) {
                array->hardware.trigger_write(array->active_channel, 0u);
                channel->state = DEMO_ULTRASONIC_WAIT_RISE;
                channel->state_started_us = now_us;
            }
            break;
        case DEMO_ULTRASONIC_WAIT_RISE:
            if (array->hardware.echo_read(array->active_channel) != 0u) {
                channel->echo_rise_us = now_us;
                channel->state = DEMO_ULTRASONIC_WAIT_FALL;
                channel->state_started_us = now_us;
            } else if (duration_us >= OPENRF1_DEMO_ECHO_TIMEOUT_US) {
                complete_channel(array, DEMO_SENSOR_RISE_TIMEOUT, now_us, now_ms);
            }
            break;
        case DEMO_ULTRASONIC_WAIT_FALL:
            if (array->hardware.echo_read(array->active_channel) == 0u) {
                channel->raw_echo_us = elapsed_us(channel->echo_rise_us, now_us);
                channel->distance_mm = demo_echo_us_to_distance_mm(channel->raw_echo_us);
                if (channel->raw_echo_us == 0u ||
                    channel->raw_echo_us >= OPENRF1_DEMO_ECHO_TIMEOUT_US) {
                    complete_channel(
                        array,
                        DEMO_SENSOR_PULSE_OUT_OF_BOUNDS,
                        now_us,
                        now_ms
                    );
                } else {
                    complete_channel(array, DEMO_SENSOR_OK, now_us, now_ms);
                }
            } else if (duration_us >= OPENRF1_DEMO_ECHO_TIMEOUT_US) {
                complete_channel(array, DEMO_SENSOR_FALL_TIMEOUT, now_us, now_ms);
            }
            break;
        case DEMO_ULTRASONIC_IDLE:
        default:
            complete_channel(array, DEMO_SENSOR_NOT_READY, now_us, now_ms);
            break;
    }
}

void demo_ultrasonic_copy_samples(
    const DemoUltrasonicArray *array,
    DemoObstacleSample samples[3]
) {
    uint8_t index;
    if (array == 0 || samples == 0) {
        return;
    }
    for (index = 0u; index < 3u; ++index) {
        samples[index].status = array->channels[index].status;
        samples[index].distance_mm = array->channels[index].distance_mm;
        samples[index].updated_ms = array->channels[index].updated_ms;
    }
}

const char *demo_sensor_status_name(DemoSensorStatus status) {
    static const char *const names[] = {
        "ok", "echo_not_low_before_trigger", "echo_rise_timeout",
        "echo_fall_timeout", "pulse_width_out_of_bounds", "not_ready"
    };
    return (unsigned int)status < (sizeof(names) / sizeof(names[0])) ?
        names[status] : "internal_state_error";
}
