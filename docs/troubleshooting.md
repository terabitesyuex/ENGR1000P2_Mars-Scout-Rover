# Troubleshooting

## Phase 2.4 Recording And Replay

Malformed JSONL:

- Each line must contain exactly one JSON object.
- Blank lines are invalid.
- Parser errors include line numbers when a line is involved.

Unsupported schema:

- `schema_name` must be `mars_scout_multisensor_recording`.
- `schema_version` must be `1`.
- Later schema versions must be handled explicitly in a future phase.

Missing header:

- The first line must be a `header` record.
- A second header record is rejected.

Duplicate sensor ID:

- Sensor IDs in `sensor_inventory` must be unique.
- Use neutral IDs such as `c1_1` and `c1_2`.

Unknown sensor ID:

- Every non-header record must reference a sensor ID declared in the header.
- Do not use semantic names such as `front_lidar` before mounting is physically verified.

Sequence or timestamp errors:

- `sequence` must increase.
- `timestamp_us` must be non-negative and nondecreasing in file order.

Truncated recording:

- Re-run `inspect-recording`.
- If the last line is incomplete, keep the file as failure evidence and create a new recording.

Overwrite refusal:

- `record-synthetic` refuses to replace an existing file unless `--overwrite` is provided.

Replay timing:

- `replay-recording` is immediate by default.
- Timed replay is available for tests and experiments, but tests should inject fake sleep functions.

Two-C1 filtering:

- Use `--sensor-id c1_1` or `--sensor-id c1_2` for single-sensor replay.
- Simultaneous dual-C1 hardware operation remains UNVERIFIED.

Visualization from replay:

- Use `render-recording` to export final replayed frames.
- These figures are not maps and do not prove physical mounting orientation.

pytest basetemp:

- The verifier passes repository-local `--basetemp` directories under `.verification/pytest_tmp/`.
- Do not set global `TEMP`, `TMP`, `PATH`, or Windows execution policies to fix tests.

## Phase 2.5 PC-Direct Capture

Missing capture source:

- `capture-c1` requires either `--port` or `--sample-hex`.
- Use `--sample-hex` for automated verification.
- Use `--port` only after the port is manually identified and wiring checks are complete.

No C1 scan data received:

- Fixture tests: confirm enough valid sample bytes exist for `--frames * --points-per-frame`.
- Manual hardware: confirm power, scan command, correct serial port, 460800 baud, and USB adapter ownership.

Invalid scan nodes:

- The Phase 2.5 parser supports the standard 5-byte scan-node path.
- Additional scan modes require separate parser support and tests.

Recording integration:

- Captures are saved as `lidar_scan` records in the Phase 2.4 JSONL format.
- Use `inspect-recording`, `replay-recording`, and `render-recording` after capture.

Dual-C1:

- Test `c1_1` and `c1_2` independently.
- Do not run simultaneous dual-C1 operation in Phase 2.5.

## Phase 3.1 STM32 Telemetry

Telemetry parser rejects a line:

- Confirm each line is one complete JSON object.
- Confirm `protocol` is `mars_scout_stm32_sensor_telemetry`.
- Confirm `version` is `1`.
- Confirm sequence increases and `timestamp_ms` is nondecreasing.
- Confirm NaN and Infinity are not present.

Ultrasonic timeout appears as zero distance:

- This is invalid for Phase 3.1.
- Timeout must use status `timeout`, `valid: false`, and no valid `distance_mm`.

Ground or Hall detection appears before polarity verification:

- Check that `polarity_verified` is true before trusting interpreted fields.
- Until then, use only `raw_state`.

Telemetry converts to recording but replay shows no LiDAR scans:

- STM32 low-rate sensor messages are auxiliary records, not `lidar_scan` records.
- Use `inspect-recording` to verify counts for `ultrasonic`, `ground_edge`, `hall_landmark`, `illuminance`, and `barometer`.

## Phase 3.2A OpenRF1 BH1750

Mocked capture fails:

- Confirm `capture-stm32-serial --mock-input` points to newline-delimited BH1750 telemetry.
- Confirm each line uses `message_type: illuminance` and `sensor_id: bh1750_1`.
- Confirm invalid readings use explicit status and `illuminance_lux: null`, not zero.

Live capture has no COM port:

- Identify the CH340 COM port manually in Device Manager.
- Do not guess a COM port.
- Do not run live capture from automated tests.

No data at 115200 8N1:

- Confirm firmware was built for STM32F103RC/F1 and flashed by the documented method.
- Confirm USART1 PA9 TX / PA10 RX and CH340 path in the vendor OpenRF1 documentation.
- Keep debug text out of the JSON telemetry stream.

No ACK at `0x23`:

- Power off before changing wiring.
- Recheck GY-302 ADDR to GND, VCC to OpenRF1 I2C 5V, GND, SCL to PB1, and SDA to PC3.
- The committed Phase 3.2A evidence verifies one successful configured-address run. For any new wiring or rerun, do not mark the address verified again until fresh ACK or valid telemetry evidence is recorded.

All-zero lux:

- Distinguish valid darkness from bus failure.
- Cover and uncover the sensor and compare against ACK/status evidence.
- Do not convert timeout or hardware fault into zero lux.

Malformed JSON:

- Ensure firmware uses the bounded telemetry formatter and one JSON object per line.
- Disable or route human-readable diagnostics away from the telemetry UART stream.

## Future Hardware Items

No power or motor does not start:

- Future hardware check: confirm regulated 5 V supply and current margin.
- Future hardware check: confirm common ground between supply, LiDAR, and controller.
- Future hardware check: confirm scan has been commanded; the C1M1-R2 does not use an external motor PWM wire.

Serial port opens but no data arrives:

- Future hardware check: confirm LiDAR TX goes to receiver RX and LiDAR RX goes to transmitter TX.
- Future hardware check: confirm 460800 baud and 8N1.
- Future hardware check: confirm USB adapter and ESP32 are not both driving LiDAR RX.

Data looks corrupt:

- Future hardware check: ground continuity.
- Future hardware check: UART wire length and routing.
- Future hardware check: supply ripple.
- Future software check: parser must use official SLAMTEC packet format for the selected scan mode.

PC-direct port remains locked:

- Future hardware check: close the official SDK probe cleanly.
- Future hardware check: unplug and reconnect the USB adapter if the operating system still holds the port.

Current Phase 3.2A automated work has no real COM-port access, STM32 flashing, GPIO, I2C, ESP32 communication, WiFi sockets, mapping, SLAM, odometry, navigation, obstacle avoidance, motors, encoders, or additional sensors.

Current Phase 3.2B automated work also has no real COM-port access, STM32 flashing, GPIO, I2C, ESP32 WiFi, USB device access, or sensors. For Phase 3.2B bring-up:

- Do not tie all I2C module VCC pins together: BH1750 and MPU6050 use 5 V module VCC, while BMP280 uses 3.3 V.
- HC-SR04 timeout remains invalid data, not distance zero.
- HC-SR04 Echo level protection is conditional on module supply and measured Echo VOH; direct connection is not approved until measured or exact MCU pin tolerance is established.
- TCRT5000 and Hall raw state must be preserved until polarity is physically verified.
- TCRT5000 modules use 3.3 V for first integration; Hall uses 5 V and requires Hall `S` voltage measurement before STM32 input connection.
- Disconnect the STM32/OpenRF1 5 V feed before plugging the ESP32-C3 SuperMini into USB.
- BMP280 and MPU6050 bad ID or NACK must be recorded as status, not converted into readings.
- RPLIDAR overflow and ESP32 CRC errors are transport diagnostics only, not proof of working physical links.
- Follow `docs/phase3_2b_full_hardware_foundation.md` before attaching additional hardware.

## Phase 3.2C OpenRF1 BMP280

No identity line:

- Confirm the `OpenRF1_BMP280_Bringup.hex` image was flashed, not the BH1750 or FullHardware target.
- Confirm USART1 PA9/PA10 CH340 capture at 115200 8N1.
- Do not record the COM port number in committed evidence.

NACK at `0x76`:

- Power off before changing wiring.
- Confirm BMP280 VCC is connected to 3.3 V, not the OpenRF1 I2C 5 V pin.
- Confirm GND is common, SCL is PB1/B1, SDA is PC3/C3, CSB is 3.3 V, and SDO is GND.
- Treat NACK as failed communication; do not fabricate temperature or pressure.

Bad chip ID:

- Record the observed chip ID and stop.
- Do not mark the BMP280 verified unless register `0xD0` returns `0x58` from the wired module.

Temperature or pressure is null:

- Check the `status`, `initialization_stage`, and `error_code` fields.
- Null values indicate invalid data, not zero temperature or zero pressure.

The Phase 3.2C automated verifier does not flash, open a COM port, access USB, GPIO, I2C, or sensors. It validates the committed sanitized evidence offline. Isolated BMP280 ACK, chip ID, calibration-register path, configuration readback, live compensated samples, and 500 ms cadence are PHYSICAL_EVIDENCE_VERIFIED for the formal 30-second capture; absolute accuracy, long-duration operation, shared-I2C concurrency, and full-hardware operation remain UNVERIFIED.

## Phase 3.2D OpenRF1 MPU6050

No identity line:

- Confirm the `OpenRF1_MPU6050_Bringup.hex` image was flashed, not the BH1750, BMP280, or FullHardware target.
- Confirm USART1 PA9/PA10 CH340 capture at 115200 8N1.
- Do not record the port number in committed evidence.

NACK at `0x68`:

- Power off before changing wiring.
- Confirm the GY-521/MPU6050 VCC is connected to the intended 5 V module supply, GND is common, SCL is PB1/B1, SDA is PC3/C3, and AD0 is GND.
- Treat NACK as failed communication; do not fabricate acceleration, angular-rate, or temperature readings.

Bad WHO_AM_I:

- Record the observed WHO_AM_I value and stop.
- Do not mark the MPU6050 verified unless register `0x75` returns `0x68` from the wired module.

Configuration readback mismatch:

- Record the register, expected value, and observed value.
- Do not continue to interpret IMU samples as valid bring-up evidence until `PWR_MGMT_1`, `SMPLRT_DIV`, `CONFIG`, `GYRO_CONFIG`, and `ACCEL_CONFIG` read back as expected.

IMU values are null:

- Check the `status`, `initialization_stage`, `operation`, `register`, and `error_code` fields.
- Null values indicate invalid data, not zero acceleration or zero angular rate.

Live values are present:

- Treat them as raw-register conversion evidence only.
- Do not claim calibrated acceleration, gyro bias, axis orientation, yaw, pitch, roll, odometry, navigation, or sensor fusion without later calibrated tests.

The Phase 3.2D automated verifier does not flash, open a COM port, access USB, GPIO, I2C, or sensors. MPU6050 ACK, WHO_AM_I, configuration readback, live IMU telemetry, calibration, axis orientation, shared-I2C concurrency, and full-hardware operation remain UNVERIFIED until recorded physical evidence exists.
