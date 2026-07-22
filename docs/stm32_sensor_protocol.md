# STM32 Sensor Telemetry Protocol

Phase 3.1 defines `mars_scout_stm32_sensor_telemetry` version `1`.

This is a newline-delimited UTF-8 JSON diagnostic protocol for software bring-up, deterministic simulation, and future STM32-to-ESP32 forwarding. It is not the Phase 2.4 recording format and does not implement serial, WiFi, GPIO, I2C, timers, or real sensor access.

## Required Fields

Each line is one JSON object with:

- `protocol`: `mars_scout_stm32_sensor_telemetry`
- `version`: `1`
- `sequence`: non-negative integer
- `timestamp_ms`: non-negative integer
- `message_type`
- `sensor_id`
- `payload`
- `status`

Sequences must increase within a stream. Timestamps must be nondecreasing. NaN, Infinity, booleans substituted for integers, missing required fields, unknown top-level fields, unknown message types, and sensor/message mismatches are rejected.

## Status Values

Supported statuses:

- `ok`
- `timeout`
- `out_of_range`
- `invalid_reading`
- `not_initialized`
- `stale`
- `hardware_fault`
- `simulated`

Not every sensor is expected to use every status.

## Message Types

### `ultrasonic`

Sensor IDs:

- `ultrasonic_1`
- `ultrasonic_2`
- `ultrasonic_3`

Payload:

- `distance_mm` when valid
- optional `raw_echo_us`
- `valid`

Ultrasonic timeout must not be represented as a valid zero-distance obstacle. Timeout uses status `timeout`, `valid: false`, and no valid `distance_mm`.

### `ground_edge`

Sensor IDs:

- `tcrt5000_1`
- `tcrt5000_2`

Payload:

- `raw_state`
- `polarity_verified`
- `interpreted_edge_detected`

Until polarity is physically verified, `raw_state` is authoritative and `interpreted_edge_detected` must be null.

### `hall_landmark`

Sensor ID:

- `hall_1`

Payload:

- `raw_state`
- `polarity_verified`
- `interpreted_landmark_detected`

Hall sensor is for magnetic landmark/checkpoint detection, not odometry. Until polarity is physically verified, `raw_state` is authoritative and `interpreted_landmark_detected` must be null.

### `illuminance`

Sensor ID:

- `bh1750_1`

Payload:

- `illuminance_lux`

Values must be finite and non-negative when valid. BH1750 supports controlled illuminance-change experiments only; reliable dust-storm detection is not claimed.

Phase 3.2A uses this message for the OpenRF1 GY-302/BH1750 firmware foundation. Valid firmware readings use status `ok`; deterministic software fixtures may use status `simulated`. `timeout`, `not_initialized`, `stale`, and `hardware_fault` must not be represented as valid zero-lux readings. Recorded manual evidence verifies BH1750 communication at configured public 7-bit address `0x23`, 500 ms telemetry, and physical light response. Absolute lux calibration remains UNVERIFIED.

### `barometer`

Sensor ID:

- `bmp280_1`

Payload:

- `temperature_c`
- `pressure_pa`

Temperature and pressure must be finite when valid. Pressure is in pascals. Altitude is not part of Phase 3.1 and must not be inferred.

### `imu_raw`

Sensor ID:

- `mpu6050_1`

Payload:

- `accel_x_raw`, `accel_y_raw`, `accel_z_raw`
- `gyro_x_raw`, `gyro_y_raw`, `gyro_z_raw`
- `temperature_raw`
- `accel_range_g`
- `gyro_range_dps`
- `calibration_state`

Phase 3.2B records raw MPU6050 samples and deterministic conversion helpers only. It does not claim calibration, sensor fusion, orientation, odometry, SLAM, or navigation.

Phase 3.2D also defines an isolated MPU6050 bring-up JSONL stream with `sensor_identity` and `imu` records for future manual USART1 capture. That stream is validated by dedicated Phase 3.2D helpers/tests and is not a calibrated rover-frame IMU, odometry, or sensor-fusion contract. MPU6050 ACK, WHO_AM_I, configuration readback, live telemetry, calibration, and axis orientation remain UNVERIFIED.

### `subsystem_status`

Sensor ID:

- `stm32_subsystem`

Payload:

- `subsystem`
- `health`
- `error_count`
- optional `detail`

This is software status. It is not a physical sensor reading.

### `link_status`

Sensor ID:

- `esp32_link`

Payload:

- `link_name`
- `healthy`
- `rx_bytes`
- `tx_bytes`
- `malformed_frames`
- `crc_errors`
- `sequence_gaps`
- `last_rx_ms`

Phase 3.2B uses this for the STM32-side USART3 foundation. It is not proof that a real ESP32-C3 link is operating.

### `lidar_transport_stats`

Sensor IDs:

- `c1_1`
- `c1_2` (schema/backward-compatibility fixtures only; no second physical C1)

Payload:

- `rx_bytes`
- `bytes_read`
- `overflow_count`
- `framing_error_count`
- `chunks_forwarded`
- `last_rx_tick_ms`

These are byte-transport counters only. They do not claim RPLIDAR packet parsing, mapping, or a successful physical C1 connection.

## Recording Bridge

The PC bridge converts validated messages into `mars_scout_multisensor_recording` version `1`.

- `ultrasonic` -> `ultrasonic`
- `ground_edge` -> `ground_edge`
- `hall_landmark` -> `hall_landmark`
- `illuminance` -> `illuminance`
- `barometer` -> `barometer`
- `imu_raw` -> `imu`
- `subsystem_status` -> `subsystem_status`
- `link_status` -> `link_status`
- `lidar_transport_stats` -> `lidar_transport_stats`

The bridge preserves sensor IDs, timestamps, status, raw values, and source telemetry sequence where supported. It does not create LiDAR scans.
