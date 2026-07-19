# Recording Format

Phase 2.4 implements a human-readable, streamable UTF-8 JSON Lines format. Phase 2.5 reuses the same schema for bounded PC-direct C1 captures. Phase 3.1 reuses the same schema for validated STM32 low-rate sensor telemetry converted by the PC bridge. Phase 3.2A reuses it for mocked or manually captured OpenRF1 BH1750 serial telemetry. Phase 3.2D adds isolated MPU6050 bring-up JSONL examples, but does not yet add a recording bridge for physical MPU6050 evidence.

## Rationale

JSONL allows incremental writing, lazy reading, line-number corruption reports, easy diffing, and simple test fixtures. It is not pickle, marshal, a database, ROS bag, or an opaque binary format.

The Phase 2.4 JSONL recording format is not the future on-wire protocol between ESP32 and PC.

## Schema

- Schema name: `mars_scout_multisensor_recording`.
- Schema version: `1`.
- Encoding: UTF-8.
- One complete JSON object per line.
- First line: `header`.
- Later lines: sensor or replay records.

## Header

Required fields:

- `record_type`: `header`.
- `schema_name`: `mars_scout_multisensor_recording`.
- `schema_version`: `1`.
- `created_unix_us`: integer.
- `sensor_inventory`: list of sensor definitions.
- `coordinate_convention`: object.
- `metadata`: object.

Example:

```json
{"record_type":"header","schema_name":"mars_scout_multisensor_recording","schema_version":1,"sensor_inventory":[{"sensor_id":"c1_1","sensor_type":"rplidar_c1","units":["angle_deg","distance_mm","quality"]}]}
```

## Sensor Inventory

Neutral IDs are used until mounting is physically verified:

- `c1_1`
- `c1_2`
- `ultrasonic_1`
- `ultrasonic_2`
- `ultrasonic_3`
- `tcrt5000_1`
- `tcrt5000_2`
- `bh1750_1`
- `bmp280_1`
- `mpu6050_1`
- `hall_1`
- `rover_pose`
- `stm32_subsystem`
- `esp32_link`

Duplicate sensor IDs are rejected. Unknown sensor IDs in later records are rejected.

## Common Record Fields

All non-header records include:

- `record_type`
- `schema_name`
- `schema_version`
- `sequence`
- `timestamp_us`
- `sensor_id`

`sequence` must increase. `timestamp_us` must be non-negative and nondecreasing in file order.

## Coordinate Convention And Units

- `ScanPoint.angle_deg`: rover-frame degrees, `0` forward, positive counterclockwise.
- `ScanPoint.distance_mm`: millimetres.
- Cartesian distances: metres.
- `+x`: rover forward.
- `+y`: rover left.
- Native C1 clockwise conversion must happen before `ScanFrame` creation.

## Record Types

### `lidar_scan`

Fields:

- `sensor_id`: `c1_1` or `c1_2`.
- `frame_id`
- `source`
- `metadata`
- `points`
- `rover_pose`

Each point stores `angle_deg`, `distance_mm`, and optional `quality`. Point order is preserved.

Phase 2.5 PC-direct captures store native C1 samples only after conversion into rover-frame `ScanPoint.angle_deg`. Metadata identifies `source` as `pc_direct_c1` and includes `physical_test_required` because automated fixture tests do not verify hardware.

Short example:

```json
{"record_type":"lidar_scan","sensor_id":"c1_1","timestamp_us":0,"sequence":1,"points":[{"angle_deg":0.0,"distance_mm":2000,"quality":100}]}
```

### `rover_pose`

Fields:

- `x_m`
- `y_m`
- `yaw_rad`
- `source`

Phase 2.4 pose records are optional replay data. They are not proof of encoder odometry.

### `imu`

Fields:

- `sensor_id`: `mpu6050_1`.
- `accel_x_mps2`
- `accel_y_mps2`
- `accel_z_mps2`
- `gyro_x_radps`
- `gyro_y_radps`
- `gyro_z_radps`
- optional `temperature_c`

### `ultrasonic`

Fields:

- `sensor_id`: `ultrasonic_1`, `ultrasonic_2`, or `ultrasonic_3`.
- `distance_mm`, nullable when invalid or timeout.
- `valid`
- optional `status`
- optional `raw_echo_us`
- optional `source_sequence`

Phase 3.1 timeout and invalid readings are explicit. Timeout is not represented as a valid zero-distance obstacle.

### `ground_edge`

Fields:

- `sensor_id`: `tcrt5000_1` or `tcrt5000_2`.
- `edge_detected`, nullable until active polarity is verified.
- optional `raw_state`
- optional `polarity_verified`
- optional `status`
- optional `reflectance_raw`
- optional `source_sequence`

### `hall_landmark`

Fields:

- `sensor_id`: `hall_1`.
- `detected`, nullable until active polarity is verified.
- optional `raw_state`
- optional `polarity_verified`
- optional `status`
- optional `raw_value`
- optional `source_sequence`

The Hall module is for magnetic landmark/checkpoint detection, not wheel odometry.

### `illuminance`

Fields:

- `sensor_id`: `bh1750_1`.
- `illuminance_lux`, nullable when invalid or not initialized.
- optional `status`
- optional `source_sequence`

Phase 3.2A serial capture writes `illuminance` records for `bh1750_1` only. Hardware errors such as timeout, not initialized, stale data, or hardware fault preserve `illuminance_lux: null`; they are not converted to zero. Zero lux is valid only when the telemetry status is valid and the BH1750 reading itself is zero.

### `barometer`

Fields:

- `sensor_id`: `bmp280_1`.
- `temperature_c`, nullable when invalid or not initialized.
- `pressure_pa`, nullable when invalid or not initialized.
- optional `status`
- optional `source_sequence`

BH1750 and BMP280 support environmental-change indication. Reliable real-world dust-storm detection is not claimed.

### `subsystem_status`

Fields:

- `sensor_id`: `stm32_subsystem`.
- `subsystem`
- `health`
- `error_count`
- optional `detail`
- optional `status`
- optional `source_sequence`

This records software health only; it is not physical hardware evidence.

### `link_status`

Fields:

- `sensor_id`: `esp32_link`.
- `link_name`
- `healthy`
- `rx_bytes`
- `tx_bytes`
- `malformed_frames`
- `crc_errors`
- `sequence_gaps`
- optional `last_rx_ms`
- optional `status`
- optional `source_sequence`

### `lidar_transport_stats`

Fields:

- `sensor_id`: `c1_1` or `c1_2`.
- `rx_bytes`
- `bytes_read`
- `overflow_count`
- `framing_error_count`
- `chunks_forwarded`
- `last_rx_tick_ms`
- optional `status`
- optional `source_sequence`

These counters do not imply successful physical RPLIDAR operation.

### `wheel_encoder_delta`

Fields:

- `sensor_id`: `wheel_encoders`;
- positive `interval_ms`;
- four `*_raw_count_delta` fields;
- four `*_signed_count_delta` fields after explicit direction multipliers;
- `status`, which is `simulated` for Phase 4A fixtures;
- optional `source_sequence`.

Physical encoder polarity, resolution, counter width, and timing remain UNVERIFIED.

### `wheel_angular_velocity`

Fields are `front_left_rad_s`, `front_right_rad_s`, `rear_left_rad_s`, and `rear_right_rad_s` for sensor ID `mecanum_wheels`, plus `status: software_derived` and optional `source_sequence`.

### `body_twist`

Fields are `vx_m_s`, `vy_m_s`, and `yaw_rate_rad_s` for sensor ID `rover_body`, plus `status: software_derived` and optional `source_sequence`. The rover convention remains `+x` forward, `+y` left, and positive counterclockwise yaw.

### `odometry_pose`

Fields are `x_m`, `y_m`, `yaw_rad`, and `integration_method: se2_constant_twist_exponential` for sensor ID `rover_odometry`, plus `status: software_derived` and optional `source_sequence`. This record is not sensor fusion or physical odometry accuracy evidence.

## Corruption Behavior

Readers reject:

- Missing header.
- Duplicate header.
- Unsupported schema name or version.
- Blank lines.
- Non-object JSON values.
- Invalid JSON.
- Duplicate sensor IDs.
- Unknown sensor IDs.
- Non-increasing sequence numbers.
- Decreasing timestamps.
- Invalid scan points.

Errors include useful line numbers when a line is involved.

## Forward Compatibility

The version-1 container permits additive record types whose sensor IDs are declared in the header inventory; Phase 4A uses that existing rule. Existing record types and semantics are unchanged. Readers still reject unsupported schema versions instead of silently guessing.

## Phase 4B Additive Control Records

Phase 4B keeps `mars_scout_multisensor_recording` at version `1`. The telemetry bridge writes `body_motion_command`, `wheel_speed_setpoint`, `wheel_speed_measurement`, `wheel_control_effort`, `motion_safety_state`, and `motion_control_snapshot` records. Their declared sensor IDs are `motion_command`, `mecanum_wheel_setpoints`, `mecanum_wheel_measurements`, `mecanum_wheel_control`, `motion_safety`, and `motion_control`.

Each record has `status: software_derived`, `origin: synthetic_phase4b_motion_control`, a source sequence, and validated `control_data`. Synthetic measurements and poses are not encoder, motor, or physical-motion evidence. Existing recordings need none of these record types or inventory entries, and inspection/replay retain their existing version-1 behavior.

## CLI Examples

Create a deterministic two-C1 room session with auxiliary streams:

```powershell
python -m rplidar_c1_tools.cli record-synthetic --scene room --frames 3 --lidar-count 2 --include-aux --output .verification\phase2.4\synthetic_multisensor_room.jsonl
```

Inspect:

```powershell
python -m rplidar_c1_tools.cli inspect-recording .verification\phase2.4\synthetic_multisensor_room.jsonl --output .verification\phase2.4\inspection.txt
```

Replay:

```powershell
python -m rplidar_c1_tools.cli replay-recording .verification\phase2.4\synthetic_multisensor_room.jsonl
```

Render final replayed frames:

```powershell
python -m rplidar_c1_tools.cli render-recording .verification\phase2.4\synthetic_multisensor_room.jsonl --output-dir .verification\phase2.4
```

## Limitations

- Phase 2.4 data is synthetic; Phase 2.5 can write PC-direct C1 records only when fixture bytes or an explicit user-verified serial port are provided; Phase 3.1 can write STM32 telemetry records only from deterministic files or injected streams; Phase 3.2A can write BH1750 records from mock input or a future explicit user-selected COM port; Phase 3.2B can write deterministic raw-IMU and transport-status records from software fixtures only; Phase 3.2D MPU6050 bring-up JSONL is for isolated future manual evidence; Phase 4A adds deterministic software-only wheel/odometry records; Phase 4B adds deterministic software-only command/control/safety/synthetic-plant records.
- No WiFi, live Phase 4 encoder firmware, motor control, physical wheel odometry, mapping, SLAM, navigation, or obstacle avoidance is implemented.
- No mounting transforms are recorded or applied.
- No sensor calibration is implied.
