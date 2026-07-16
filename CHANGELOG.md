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

## 2026-07-15 - Phase 3.2A OpenRF1 BH1750 Firmware Foundation

- Corrected the STM32 controller target for the BH1750 bring-up path to OpenRF1 with STM32F103RCT6, 64 pins, Cortex-M3, 256 KB flash, and 48 KB SRAM.
- Recorded the intended vendor toolchain as Keil MDK/uVision 5 with STM32F10x Standard Peripheral Library, target STM32F103RC, `STM32F10X_HD`, `USE_STDPERIPH_DRIVER`, and `startup_stm32f10x_hd.s`.
- Recorded confirmed OpenRF1 software-I2C pins PB1/SCL and PC3/SDA, 10 kOhm pull-ups to 3.3 V, duplicated 2x4 I2C header signals, and USART1 PA9/PA10 at 115200 baud 8N1.
- Recorded the GY-302/BH1750 planned wiring table and configured public 7-bit address `0x23` with ADDR to GND; ACK and real lux readings remain UNVERIFIED.
- Added `firmware/openrf1/app/` application-layer source for board configuration, bounded software I2C, BH1750 conversion/state machine, and versioned telemetry formatting.
- Added host-testable OpenRF1/BH1750 Python logic, deterministic BH1750 telemetry generation, mocked STM32 serial capture, and `python -m rplidar_c1_tools` CLI entrypoint.
- Added CLI commands `simulate-bh1750-telemetry` and `capture-stm32-serial`.
- Added tests for BH1750 conversion, address derivation, nonblocking state-machine behavior, firmware source constraints, mocked serial capture, invalid serial data, no-overwrite behavior, and CLI workflow.
- Added OpenRF1 BH1750 bring-up documentation and a build-audit helper for verifier artifacts.
- Did not run Keil, flash STM32, open real COM ports, access USB devices, run I2C/GPIO, or implement BMP280, HC-SR04, TCRT5000, Hall, MPU6050, motors, encoders, ESP32/WiFi, C1 hardware integration, mapping, SLAM, navigation, obstacle avoidance, or Phase 3.2B.

## 2026-07-16 - Phase 3.2B OpenRF1 Multisensor And Communications Software Foundation

- Frozen the Phase 3.2A BH1750 HEX externally before source changes; physical hardware testing remains independent.
- Added isolated Phase 3.2B firmware source under `firmware/openrf1/full_hardware/` without modifying the BH1750-only `firmware/openrf1/app/` scope.
- Added a separate Keil project `OpenRF1_FullHardware.uvprojx` with output directory `Objects_FullHardware/` and output name `OpenRF1_FullHardware`.
- Added feature flags for BH1750, BMP280, MPU6050, HC-SR04, TCRT5000, Hall, RPLIDAR C1 transport, and ESP32 link foundations.
- Added bounded ring buffers, cooperative scheduler, shared software-I2C wrapper, BMP280 compensation foundation, MPU6050 raw conversion foundation, digital debounce, HC-SR04 timeout state machine, RPLIDAR byte transport counters, and STM32-to-ESP32 binary frame encoding.
- Extended `mars_scout_stm32_sensor_telemetry` version `1` with `imu_raw`, `subsystem_status`, `link_status`, and `lidar_transport_stats`.
- Extended deterministic PC simulation, strict parsing, recording bridge support, and tests for Phase 3.2B contracts.
- Added Phase 3.2B architecture, wiring, protocol, memory-budget, bring-up, troubleshooting, and verification documentation.
- Added `phase3.2b` verifier manifest support and `tools/audit_phase32b.py`.
- Recorded proposed USART2/USART3, HC-SR04, I2C strap, TCRT5000, and Hall wiring as UNVERIFIED or MANUAL_ACTION_REQUIRED, not confirmed hardware facts.
- Did not flash hardware, open COM ports, access USB devices, verify I2C ACKs, prove ESP32/RPLIDAR operation, implement WiFi firmware, implement motor/encoder control, or claim real sensor data.

## Change Categories

- Protocol changes: Phase 2.5 adds a PC-direct standard scan-node parser boundary for C1 capture; Phase 3.1 adds the PC-side `mars_scout_stm32_sensor_telemetry` v1 diagnostic protocol; Phase 3.2A emits the existing v1 `illuminance` message for `bh1750_1`; Phase 3.2B extends v1 telemetry with raw IMU and status/transport diagnostics and defines a separate STM32-to-ESP32 binary frame contract; no ESP32 WiFi protocol implementation.
- GPIO changes: Phase 3.2A locks OpenRF1 software-I2C PB1/SCL and PC3/SDA for BH1750 only; other GPIO values remain unset.
- Power changes: hardware values documented; supply model unverified.
- Data-format changes: Phase 2.1 adds the PC-side `ScanFrame` software interface; Phase 2.2 adds Cartesian transform models; Phase 2.3 adds PNG visualization export; Phase 2.4 adds the multi-sensor JSONL recording format; Phase 2.5 reuses that JSONL format for PC-direct C1 captures; Phase 3.1 reuses it for STM32 low-rate sensor telemetry recordings with optional status/raw fields; Phase 3.2A reuses the same recording format for mocked BH1750 serial capture.
- Firmware changes: Phase 3.2A adds OpenRF1 application-layer STM32F103RCT6 BH1750 source, not a complete standalone Keil build tree.
- Calibration changes: calibration process documented only.
