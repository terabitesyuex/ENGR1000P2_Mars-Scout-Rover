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

An optional top-level `error` object is permitted only for message types whose strict subtype contract defines it. Existing messages without `error` remain unchanged.

Sequences must increase within a stream. Timestamps must be nondecreasing. NaN, Infinity, booleans substituted for integers, missing required fields, unknown top-level fields, unknown message types, and sensor/message mismatches are rejected.

## Status Values

Supported statuses:

- `ok`
- `error`
- `timeout`
- `out_of_range`
- `invalid_reading`
- `not_initialized`
- `stale`
- `hardware_fault`
- `simulated`
- `software_derived`

Not every sensor is expected to use every status. Phase 4A uses `simulated` for synthetic raw encoder deltas and `software_derived` for values calculated from those deltas. Neither status is physical evidence.

## Message Types

### `sensor_identity`

Phase 3.2E uses this type for the isolated HC-SR04 startup configuration record. Its sensor ID is one of the neutral `ultrasonic_1` through `ultrasonic_3` IDs; isolated capture defaults to `ultrasonic_1`. The strict payload records `hc-sr04`, CN6, PA5, PA4, TIM6, nominal timing, `mm`, and `nominal_343_m_per_s_uncalibrated`. It describes software configuration, not proof that a sensor responded.

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

The Phase 3.2E isolated subtype instead preserves `echo_pulse_us`, `distance_mm`, and `distance_model`. A successful pulse is in the inclusive range 1 through 29999 us and its rounded distance must match the fixed 343 m/s integer model. A 1 us pulse legitimately rounds to 0 mm and remains distinguishable from failure by `status: ok` and its non-null raw pulse. Diagnostic failure uses `status: error`, null pulse and distance, plus strict `code`, `operation`, and `timeout_us` metadata. This additive subtype does not change the original Phase 3.1 ultrasonic shape.

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

Phase 3.2D also defines an isolated MPU6050 bring-up JSONL stream with `sensor_identity` and `imu` records for manual USART1 capture. That stream is validated offline by dedicated Phase 3.2D helpers, fixtures, and tests and is not a calibrated rover-frame IMU, odometry, or sensor-fusion contract. A's sanitized report verifies isolated MPU6050 ACK/address, WHO_AM_I, configuration readback, live telemetry, startup gyro-bias semantics, approximately 10 Hz output during a 15-second isolated test with no reported sequence loss, and isolated sensor-axis response. Exact electrical, build, timing, bias/noise, absolute-accuracy, calibration-motion-rejection, rover-frame-alignment, shared-I2C, and complete-rover claims remain UNVERIFIED.

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

### `wheel_encoder_delta`

Sensor ID: `wheel_encoders`.

Payload:

- `interval_ms`, a strictly positive integer;
- `front_left_raw_count_delta`, `front_right_raw_count_delta`, `rear_left_raw_count_delta`, `rear_right_raw_count_delta`;
- matching `*_signed_count_delta` fields after explicit direction multipliers.

Phase 4A emits this message with `status: simulated`. Raw and mathematical signs remain separate because physical encoder polarity is UNVERIFIED. Encoder resolution, counter width, GPIO, timers, and timestamps are not inferred by the protocol.

### `wheel_angular_velocity`

Sensor ID: `mecanum_wheels`.

Payload contains finite `front_left_rad_s`, `front_right_rad_s`, `rear_left_rad_s`, and `rear_right_rad_s`. Phase 4A uses `status: software_derived`.

### `body_twist`

Sensor ID: `rover_body`.

Payload contains finite `vx_m_s`, `vy_m_s`, and `yaw_rate_rad_s`. The convention is `+x` forward, `+y` left, and positive counterclockwise yaw. Phase 4A uses `status: software_derived`.

### `odometry_pose`

Sensor ID: `rover_odometry`.

Payload contains finite `x_m`, `y_m`, `yaw_rad`, and `integration_method: se2_constant_twist_exponential`. Phase 4A uses `status: software_derived`. This is wheel-odometry mathematics, not MPU6050 fusion or physical accuracy evidence.

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
- `wheel_encoder_delta` -> `wheel_encoder_delta`
- `wheel_angular_velocity` -> `wheel_angular_velocity`
- `body_twist` -> `body_twist`
- `odometry_pose` -> `odometry_pose`

The bridge preserves sensor IDs, timestamps, status, raw values, and source telemetry sequence where supported. It does not create LiDAR scans.

## Phase 4B Additive Software-Control Messages

Phase 4B keeps `mars_scout_stm32_sensor_telemetry` at version `1` and adds `body_motion_command`, `wheel_speed_setpoint`, `wheel_speed_measurement`, `wheel_control_effort`, `motion_safety_state`, and `motion_control_snapshot`. Every Phase 4B message uses `status: software_derived` and requires `origin: synthetic_phase4b_motion_control`; it is not hardware evidence.

- `body_motion_command` preserves validated body values, command timestamp/identity, source, and the requested-motion flag.
- `wheel_speed_setpoint` distinguishes requested, proportionally desaturated, acceleration-limited, and safety-applied four-wheel targets and includes shaping flags.
- `wheel_speed_measurement` contains finite synthetic first-order plant speeds.
- `wheel_control_effort` contains dimensionless mathematical efforts explicitly labelled as not PWM.
- `motion_safety_state` contains permission, forced-stop reason, command age/staleness, non-latched state, and target replacement.
- `motion_control_snapshot` combines requested motion, every wheel stage, synthetic measurements, efforts, estimated body twist, synthetic pose, and safety result.

The recording bridge maps each message to the identically named additive record type. Existing version-1 message fields, status meanings, ordering rules, and parser behavior are unchanged; older telemetry requires no Phase 4B messages.
