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

Current Phase 2.5 has no STM32 integration, ESP32 communication, WiFi sockets, mapping, SLAM, odometry, navigation, or obstacle avoidance.
