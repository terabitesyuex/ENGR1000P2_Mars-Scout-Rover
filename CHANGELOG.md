# Changelog

All notable subsystem changes are recorded here. Track protocol, GPIO, power, data-format, firmware, and calibration changes explicitly.

## 2026-07-14 - Phase 0 Skeleton

- Created repository skeleton for RPLIDAR C1 subsystem.
- Documented confirmed C1M1-R2 electrical and wiring constraints.
- Recorded unresolved GPIO and physical verification values.
- Added PC-side synthetic scan interface and coordinate conversion scaffolding.
- Did not implement live LiDAR communication.
- Did not implement the final C1 binary protocol parser.

## 2026-07-14 - Phase 1 Audit And Validation

- Aligned Phase 1 documentation with the current audit-only scope.
- Added `docs/phase1_hardware_audit.md` to record source-of-truth decisions, unverified values, and documentation conflicts.
- Added `docs/phase1_interface_inventory.md` to inventory current firmware and PC interfaces.
- Added standard-library hardware-lock validation tooling.
- Added focused pytest coverage for the hardware-lock validator.
- Kept ESP32 GPIO values unset pending physical verification.
- Kept live LiDAR communication out of scope.

## 2026-07-14 - Phase 2.1 Synthetic Scan Pipeline

- Added unified PC-side `ScanPoint` and `ScanFrame` data models.
- Implemented deterministic `generate_circle_scan()` and `generate_room_scan()` synthetic sources.
- Implemented `scan_builder.py` validation and frame construction helpers.
- Updated synthetic scan and scan-builder tests.
- Kept real LiDAR UART communication, serial access, mapping, SLAM, and visualization out of scope.

## 2026-07-14 - Phase 2.2 Coordinate Transforms

- Added `CartesianPoint` and `Transform2D` data models.
- Updated coordinate transforms to use the rover-frame `ScanPoint.angle_deg` convention directly.
- Added explicit `native_c1_angle_to_rover_deg()` for future clockwise-positive C1 packet input.
- Added scan point, scan frame, and 2D rigid transform conversion helpers.
- Updated coordinate-frame documentation with units, frame names, and unverified mounting-offset status.
- Added coordinate transform and synthetic integration tests.
- Kept hardware communication, plotting, mapping, odometry, and SLAM out of scope.

## 2026-07-15 - Phase 2.2.5 Automated Phase Verification

- Added a CMD wrapper and PowerShell phase verifier for `phase1`, `phase2.1`, and `phase2.2`.
- Added a data-driven phase manifest for targeted, regression, and full PC test sets.
- Added Git, Python, pytest import, working-tree, upstream, and tracked-file-change checks.
- Added ignored `.verification/` log output.
- Documented one-command phase verification and development-only `-AllowDirty`.
- Did not add Phase 2.3, hardware access, plotting, mapping, or GUI functionality.

## 2026-07-15 - Phase 2.3 Synthetic LiDAR Visualization

- Implemented headless-safe synthetic polar scan visualization.
- Implemented rover-centric Cartesian point-cloud visualization with forward-up and left-left display orientation.
- Added deterministic PNG export helpers for polar and point-cloud views.
- Added `render-synthetic` CLI export for circle, room, or both scenes.
- Added visualization tests for plotting semantics, PNG export, CLI smoke coverage, and synthetic integration.
- Extended automated phase verification to support `phase2.3` and generate manual acceptance images.
- Kept real LiDAR communication, serial access, mapping, SLAM, odometry, and hardware validation out of scope.

## 2026-07-15 - Phase 2.4 Multi-Sensor Recording Replay And Plan Rebaseline

- Added versioned UTF-8 JSONL schema `mars_scout_multisensor_recording` version `1`.
- Added streaming multi-sensor recorder support for existing `ScanFrame` objects.
- Added neutral two-C1 sensor ID support for `c1_1` and `c1_2`.
- Added optional rover-pose records.
- Added IMU, HC-SR04 ultrasonic, TCRT5000 ground/edge, Hall-landmark, BH1750 illuminance, and BMP280 temperature/pressure record support.
- Added lazy recording reading, line-number corruption errors, deterministic replay, recording inspection, and replay-to-visualization export.
- Added CLI commands `record-synthetic`, `inspect-recording`, `replay-recording`, and `render-recording`.
- Added current-plan consistency validation.
- Updated hardware inventory to include RPLIDAR C1 x2, HC-SR04 x3, TCRT5000 x2, BH1750 x1, BMP280 x1, MPU6050 x1, Hall sensor module x1, STM32 x1, ESP32 x1, battery/power system, four encoded motors, and four mecanum wheels.
- Rebaselined project guidance around WiFi, one-C1 baseline integration, optional dual-C1 feasibility, environmental-change indication, and the revised Phase 2.4 through Phase 8 plan.
- Preserved verified C1 voltage, current, UART, connector, wire, and no-external-motor-PWM facts.
- Kept real hardware access, WiFi sockets, firmware changes, mapping, SLAM, odometry, ROS, and obstacle-avoidance implementation out of scope.

## 2026-07-15 - Phase 2.5 PC-Direct C1 Acquisition Boundary

- Added a transport-injected PC-direct RPLIDAR C1 driver boundary with `connect()`, `disconnect()`, `start_scan()`, and `iter_scan_points()`.
- Added standard 5-byte scan-node parsing for bounded PC-direct capture sessions, with native clockwise C1 angles converted before `ScanFrame` creation.
- Added deterministic byte-buffer transport support for automated tests and verifier smoke workflows without opening serial ports.
- Added an explicit PySerial-backed transport for manual PC-direct capture only; ports must be supplied by the user and are not invented by software.
- Added `capture-c1` CLI support for recording one C1 stream as the existing Phase 2.4 JSONL `lidar_scan` format.
- Reused `ScanFrame`, `MultiSensorRecorder`, replay, inspection, and render-recording paths without redesigning the recording schema.
- Added mocked driver, parser, timeout, invalid-data, CLI, and recording integration tests.
- Extended automated phase verification to support `phase2.5`.
- Recorded that `c1_1` and `c1_2` remain neutral sensor IDs, one stable C1 is the Phase 2.5 baseline, and simultaneous dual-C1 operation remains UNVERIFIED.
- Did not implement STM32 integration, ESP32 communication, WiFi, ROS, SLAM, navigation, obstacle avoidance, or simultaneous dual-C1 operation.

## 2026-07-15 - Phase 3.1 STM32 Sensor Telemetry Foundation

- Added `mars_scout_stm32_sensor_telemetry` version `1` as a newline-delimited UTF-8 JSON diagnostic protocol for future low-rate STM32 sensor data.
- Added PC-side typed STM32 telemetry models, strict line parser, stream validator, deterministic simulator, and Phase 2.4 recording bridge.
- Added CLI commands `simulate-stm32-sensors`, `inspect-stm32-telemetry`, and `record-stm32-telemetry`.
- Added backward-compatible optional recording fields for auxiliary sensor status, raw echo/state values, polarity verification, and source telemetry sequence.
- Added tests for STM32 telemetry models, protocol validation, simulator scenarios, recording bridge behavior, CLI workflows, and Phase 3.1 current-plan anchors.
- Added STM32 sensor protocol, bring-up, and hardware-checklist documentation.
- Recorded the user-confirmed planned PH2.0-6P line-tracking connector usage for TCRT5000 and Hall as PLANNED, not electrically verified.
- Preserved HC-SR04 ECHO voltage compatibility, TCRT5000/Hall polarity, BH1750/BMP280 addresses, STM32 MCU identity, GPIOs, timers, UARTs, I2C peripherals, and physical bring-up status as UNVERIFIED.
- Did not implement real hardware access, serial-port access, STM32 flashing, GPIO, I2C, ESP32 communication, WiFi, motor control, encoders, MPU6050 integration, mapping, SLAM, navigation, obstacle avoidance, or Phase 3.2.

## Change Categories

- Protocol changes: Phase 2.5 adds a PC-direct standard scan-node parser boundary for C1 capture; Phase 3.1 adds the PC-side `mars_scout_stm32_sensor_telemetry` v1 diagnostic protocol; no ESP32 or WiFi protocol changes.
- GPIO changes: GPIO values remain unset.
- Power changes: hardware values documented; supply model unverified.
- Data-format changes: Phase 2.1 adds the PC-side `ScanFrame` software interface; Phase 2.2 adds Cartesian transform models; Phase 2.3 adds PNG visualization export; Phase 2.4 adds the multi-sensor JSONL recording format; Phase 2.5 reuses that JSONL format for PC-direct C1 captures; Phase 3.1 reuses it for STM32 low-rate sensor telemetry recordings with optional status/raw fields.
- Firmware changes: PlatformIO structure created only; no live hardware behavior added.
- Calibration changes: calibration process documented only.
