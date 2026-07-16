#include "platform_full_hardware.h"

#include "../app/bh1750.h"
#include "board_config.h"
#include "ground_sensors.h"
#include "hall_sensor.h"
#include "hcsr04.h"
#include "memory_budget.h"
#include "mpu6050.h"
#include "rplidar_c1_transport.h"
#include "scheduler.h"
#include "telemetry_full.h"

typedef struct {
    Bh1750Context bh1750;
    OpenRf1GroundSensors ground;
    OpenRf1HallSensor hall;
    Hcsr04Channel ultrasonic[OPENRF1_HCSR04_SENSOR_COUNT];
    uint32_t telemetry_sequence;
    uint8_t ultrasonic_index;
} OpenRf1FullApp;

static OpenRf1FullApp g_app;
static char g_telemetry_buffer[OPENRF1_TELEMETRY_BUFFER_BYTES];

static void task_ground_hall(void *context, uint32_t now_ms);
static void task_mpu6050(void *context, uint32_t now_ms);
static void task_bmp280(void *context, uint32_t now_ms);
static void task_bh1750(void *context, uint32_t now_ms);
static void task_ultrasonic(void *context, uint32_t now_ms);
static void task_status(void *context, uint32_t now_ms);

int main(void) {
    openrf1_full_platform_init();
    rplidar_c1_transport_init();

    bh1750_context_init(&g_app.bh1750);
    openrf1_ground_sensors_init(&g_app.ground, 0u);
    openrf1_hall_sensor_init(&g_app.hall, 0u);
    hcsr04_channel_init(&g_app.ultrasonic[0], "ultrasonic_1", 0u);
    hcsr04_channel_init(&g_app.ultrasonic[1], "ultrasonic_2", 1u);
    hcsr04_channel_init(&g_app.ultrasonic[2], "ultrasonic_3", 2u);

    OpenRf1Task tasks[] = {
        {0},
        {0},
        {0},
        {0},
        {0},
        {0}
    };
    openrf1_task_init(&tasks[0], task_ground_hall, &g_app, OPENRF1_TASK_GROUND_HALL_PERIOD_MS, 0u, OPENRF1_ENABLE_GROUND_SENSORS || OPENRF1_ENABLE_HALL);
    openrf1_task_init(&tasks[1], task_mpu6050, &g_app, OPENRF1_TASK_MPU6050_PERIOD_MS, 0u, OPENRF1_ENABLE_MPU6050);
    openrf1_task_init(&tasks[2], task_bmp280, &g_app, OPENRF1_TASK_BMP280_PERIOD_MS, 0u, OPENRF1_ENABLE_BMP280);
    openrf1_task_init(&tasks[3], task_bh1750, &g_app, OPENRF1_TASK_BH1750_PERIOD_MS, 0u, OPENRF1_ENABLE_BH1750);
    openrf1_task_init(&tasks[4], task_ultrasonic, &g_app, OPENRF1_TASK_ULTRASONIC_PERIOD_MS, 0u, OPENRF1_ENABLE_ULTRASONIC);
    openrf1_task_init(&tasks[5], task_status, &g_app, OPENRF1_TASK_STATUS_PERIOD_MS, 0u, 1u);

    while (1) {
        openrf1_scheduler_service(tasks, sizeof(tasks) / sizeof(tasks[0]), openrf1_full_millis());
    }
}

static void task_ground_hall(void *context, uint32_t now_ms) {
    OpenRf1FullApp *app = (OpenRf1FullApp *)context;
    openrf1_ground_sensors_update_raw_mask(&app->ground, 0u, now_ms);
    openrf1_hall_sensor_update_raw(&app->hall, 0u, now_ms);
}

static void task_mpu6050(void *context, uint32_t now_ms) {
    (void)context;
    (void)now_ms;
}

static void task_bmp280(void *context, uint32_t now_ms) {
    (void)context;
    (void)now_ms;
}

static void task_bh1750(void *context, uint32_t now_ms) {
    OpenRf1FullApp *app = (OpenRf1FullApp *)context;
    Bh1750Sample sample;
    (void)bh1750_task(&app->bh1750, now_ms, &sample);
}

static void task_ultrasonic(void *context, uint32_t now_ms) {
    OpenRf1FullApp *app = (OpenRf1FullApp *)context;
    Hcsr04Channel *channel = &app->ultrasonic[app->ultrasonic_index];
    uint32_t now_us = now_ms * 1000u;
    if (channel->state == HCSR04_STATE_IDLE) {
        (void)hcsr04_start(channel, now_us);
    } else {
        (void)hcsr04_poll(channel, now_us);
    }
    if (channel->state == HCSR04_STATE_IDLE) {
        app->ultrasonic_index = (uint8_t)((app->ultrasonic_index + 1u) % OPENRF1_HCSR04_SENSOR_COUNT);
    }
}

static void task_status(void *context, uint32_t now_ms) {
    OpenRf1FullApp *app = (OpenRf1FullApp *)context;
    RplidarC1TransportStats stats = rplidar_c1_transport_stats();
    if (openrf1_format_lidar_transport_stats(
            g_telemetry_buffer,
            sizeof(g_telemetry_buffer),
            app->telemetry_sequence,
            now_ms,
            &stats
        ) == OPENRF1_FULL_TELEMETRY_OK) {
        openrf1_debug_write_bounded(g_telemetry_buffer, OPENRF1_TELEMETRY_BUFFER_BYTES);
        ++app->telemetry_sequence;
    }
}
