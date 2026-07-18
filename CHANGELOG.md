# Changelog

All notable subsystem changes are recorded here. Track protocol, GPIO, power, data-format, firmware, and calibration changes explicitly.

## 2026-07-18 - Phase 3.2F Ground-Sensor Bring-Up Foundation

- Added isolated OpenRF1 ground-sensor firmware under `firmware/openrf1/ground_sensors_bringup/`.
- Added dedicated Keil target `OpenRF1_GroundSensors_Bringup.uvprojx` with isolated output `Objects_GroundSensors_Bringup/OpenRF1_GroundSensors_Bringup.hex`.
- Locked the Phase 3.2F vendor-documented tracking-connector facts: pin 1: GND, pin 2: X4 / schematic PC14, pin 3: X3 / PB0, pin 4: X2 / PC5, pin 5: X1 / PC4, pin 6: VCC_5V; signal 1 / X1 / PC4, signal 2 / X2 / PC5, and signal 3 / X3 / PB0.
- Documented the X4 conflict: schematic says PC14 while the old tracking example maps X4 to PB1; signal 4 remains unused and PB1 is not initialized.
- Implemented 5 ms grouped GPIO sampling, independent 4-sample debounce with an effective 20 ms stable interval, startup initialization from observed raw levels, and 50 ms strict JSONL telemetry with numeric raw/debounced levels only.
- Recorded the design-locked power and protection contract: TCRT5000 modules from STM32 3.3 V, Hall module from 5 V, Hall S through an external 10 kOhm / 15 kOhm divider, and direct Hall S to PB0 prohibited.
- Added host-side ground-sensor contract helpers, focused tests, Phase 3.2F audit support, and phase verifier manifest support.
- Added a focused no-UTF-8-BOM check for `OpenRF1_GroundSensors_Bringup.uvprojx`.
- Updated README, PROJECT_SPEC, HARDWARE_LOCK, wiring, bring-up, current-state, and test-plan documentation.
- Kept physical connector orientation, wiring, rail voltages, TCRT output topology, active polarity, surface response, magnetic behavior, real debounce suitability, serial periodicity, and full-hardware operation UNVERIFIED.

## 2026-07-18 - Phase 3.2E HC-SR04 Bring-Up Foundation

- Added isolated OpenRF1 HC-SR04 firmware under `firmware/openrf1/hcsr04_bringup/`.
- Added dedicated Keil target `OpenRF1_HCSR04_Bringup.uvprojx` with isolated output `Objects_HCSR04_Bringup/OpenRF1_HCSR04_Bringup.hex`.
- Locked the Phase 3.2E HC-SR04 vendor-documented design facts: CN6 B4B-PH-K-S(LF)(SN), pin 1: VCC_5V, pin 2: GND, pin 3: PA5_TRIG, pin 4: PA4_ECHO; TRIG: PA5; ECHO: PA4; timer: TIM6.
- Recorded the external ECHO protection requirement: HC-SR04 ECHO -> 10 kOhm series resistor -> protected PA4 / CN6-pin-4 node; protected PA4 node -> 15 kOhm resistor -> GND; direct ECHO-to-CN6-pin-4 connection is prohibited.
- Implemented bounded wait-for-low, rising-edge timeout, falling-edge timeout, timer-wrap-safe pulse-width measurement, 100 ms scheduled attempts, nominal integer distance conversion, and strict JSONL identity/success/error telemetry.
- Added host-side HC-SR04 contract helpers, focused tests, Phase 3.2E audit support, and phase verifier manifest support.
- Updated README, PROJECT_SPEC, HARDWARE_LOCK, wiring, bring-up, and test-plan documentation.
- Kept physical wiring, connector orientation, resistor installation, ECHO voltage, trigger pulse, echo pulse, real distance data, timeout behavior, timer accuracy, temperature compensation, and absolute distance accuracy UNVERIFIED.

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
- Recorded the GY-302/BH1750 planned wiring table and configured public 7-bit address `0x23` with ADDR to GND; physical ACK and real lux readings were deferred to later manual evidence.
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

## 2026-07-17 - Phase 3.2B Electrical Evidence Revision And Phase 3.2A Physical Evidence

- Integrated sanitized recorded Phase 3.2A BH1750 physical evidence for frozen firmware commit `ba2024b`.
- Recorded firmware flash, CH340/USART1 telemetry, BH1750 communication at configured address `0x23`, a 500 ms telemetry period, and physical cover/illumination response as MANUAL_EVIDENCE_VERIFIED.
- Preserved absolute illuminance calibration as UNVERIFIED.
- Revised Phase 3.2B module power domains from module-specific evidence: GY-302/BH1750 and GY-521/MPU6050 module VCC on 5 V, BMP280-3.3 and TCRT5000 modules on 3.3 V, Hall module on 5 V, and common ground for all modules.
- Removed the old all-I2C-VCC-together and TCRT5000/Hall-common-VCC assumptions.
- Replaced unconditional HC-SR04 Echo divider language with a conditional requirement based on module supply, measured Echo VOH, or established MCU pin tolerance.
- Added ESP32-C3 USB/external-power exclusion and recommended a removable 5 V jumper or switch for integration.
- Added focused evidence tests for the committed BH1750 JSONL and revised electrical documentation.
- Did not change RPLIDAR C1 transport assumptions, implement new hardware pin mappings, open real COM ports in automation, or claim full-system power/current validation.

## 2026-07-17 - Phase 3.2C OpenRF1 BMP280 Bring-Up Firmware

- Added isolated BMP280-only firmware source under `firmware/openrf1/bmp280_bringup/` without modifying the Phase 3.2A BH1750 runtime or enabling BMP280 in the Phase 3.2B full-hardware runtime.
- Added Keil target `OpenRF1_BMP280_Bringup.uvprojx` with output directory `Objects_BMP280_Bringup/` and HEX name `OpenRF1_BMP280_Bringup.hex`.
- Added BMP280 driver configuration writes for `config = 0x80` and `ctrl_meas = 0x27`, plus configuration readback support.
- Recorded Phase 3.2C planned BMP280 wiring: VCC -> OpenRF1 3.3 V, GND -> GND, SCL -> PB1/B1, SDA -> PC3/C3, CSB -> 3.3 V, SDO -> GND, expected address `0x76`, and expected chip ID `0x58`.
- Added host-testable BMP280 bring-up helpers for chip ID validation, calibration parsing, raw sample decoding, register configuration values, environmental telemetry, and error telemetry.
- Added Phase 3.2C tests and verifier audit support for target isolation, telemetry formatting, configuration register values, compensation behavior, and generated-artifact hygiene.
- Did not flash hardware, open COM ports, access USB devices, verify I2C ACKs, prove chip ID readback, prove live temperature/pressure, run other sensors, implement ESP32 communication, or begin Phase 4.

## 2026-07-18 - Phase 3.2C BMP280 Physical Evidence

- Added the committed raw Phase 3.2C BMP280 physical evidence file `evidence/phase3.2c/bmp280_physical_adef636_20260718_002346.jsonl` with SHA-256 `1BB0C5BE149DC7C49A3C63432D1CAE4AACAE3D5A80265FE879CA06D1E1A74805`.
- Added `evidence/phase3.2c/bmp280_physical_evidence.md` documenting source firmware commit `adef636`, formal Keil HEX SHA-256 `85101B9F76C27FDFA019E382FC7285F239F78FA78FB0722B0400F8DDFF67E27E`, capture structure, identity/configuration results, environmental ranges, physical conclusions, and remaining limitations.
- Marked isolated Phase 3.2C FlyMcu flashing, USART1/CH340 JSONL telemetry, BMP280 ACK/address `0x76`, chip ID `0x58`, calibration-register path sufficient for compensated output, `ctrl_meas = 0x27` and `config = 0x80` readback, compensated live temperature/pressure telemetry, exact 500 ms periodicity, stable 30-second capture, and no I2C errors in the formal capture as PHYSICAL_EVIDENCE_VERIFIED.
- Added `rplidar_c1_tools.phase32c_evidence` and focused pytest coverage to validate the evidence file SHA-256, all 61 JSON records, sequence range 0 through 60, one identity record, 60 environmental records, all `status:"ok"`, identity fields, 500 ms intervals, numeric temperature/pressure values, observed min/max values, and absence of private local information.
- Updated Phase 3.2C audit/verifier support to validate the committed physical evidence offline while keeping generated Keil artifacts ignored.
- Preserved absolute temperature accuracy, absolute pressure accuracy, environmental-reference comparison, long-duration operation beyond this capture, shared-I2C concurrency, and complete full-hardware operation as UNVERIFIED.
- Did not flash hardware, open COM ports, access USB devices, run GPIO/I2C, modify the raw evidence bytes, push changes, or begin Phase 4.

## 2026-07-18 - Phase 3.2D OpenRF1 MPU6050 Bring-Up Firmware Foundation

- Added isolated MPU6050-only firmware source under `firmware/openrf1/mpu6050_bringup/` without modifying the Phase 3.2A BH1750 runtime, Phase 3.2C BMP280 runtime, or Phase 3.2B full-hardware runtime.
- Added Keil target `OpenRF1_MPU6050_Bringup.uvprojx` with output directory `Objects_MPU6050_Bringup/` and HEX name `OpenRF1_MPU6050_Bringup.hex`.
- Extended the shared MPU6050 driver with address/register constants, WHO_AM_I validation, register write/readback helpers, wake/configuration helpers, and 14-byte burst sample decoding for the isolated bring-up target.
- Recorded Phase 3.2D planned MPU6050 wiring: GY-521/MPU6050 VCC -> OpenRF1 5 V, GND -> GND, SCL -> PB1/B1, SDA -> PC3/C3, AD0 -> GND, expected address `0x68`, and expected WHO_AM_I `0x68`.
- Added host-testable MPU6050 bring-up helpers for WHO_AM_I validation, register configuration values, burst decoding, raw-to-g/dps/temperature conversion, identity telemetry, IMU telemetry, and error telemetry.
- Added Phase 3.2D tests and verifier audit support for target isolation, telemetry formatting, configuration register values, previous evidence hash preservation, and generated-artifact hygiene.
- Did not flash hardware, open COM ports, access USB devices, verify I2C ACKs, prove WHO_AM_I readback, prove live IMU data, calibrate the sensor, determine axis orientation, run other sensors, implement ESP32 communication, or begin Phase 4.

## Change Categories

- Protocol changes: Phase 2.5 adds a PC-direct standard scan-node parser boundary for C1 capture; Phase 3.1 adds the PC-side `mars_scout_stm32_sensor_telemetry` v1 diagnostic protocol; Phase 3.2A emits the existing v1 `illuminance` message for `bh1750_1`; Phase 3.2B extends v1 telemetry with raw IMU and status/transport diagnostics and defines a separate STM32-to-ESP32 binary frame contract; Phase 3.2C emits BMP280 bring-up `sensor_identity` and `environmental` JSONL on USART1; Phase 3.2D emits MPU6050 bring-up `sensor_identity` and `imu` JSONL on USART1; no ESP32 WiFi protocol implementation.
- GPIO changes: Phase 3.2A locks OpenRF1 software-I2C PB1/SCL and PC3/SDA for BH1750 only; Phase 3.2C reuses PB1/SCL, PC3/SDA, and USART1 PA9/PA10 for an isolated BMP280-only target; Phase 3.2D reuses PB1/SCL, PC3/SDA, and USART1 PA9/PA10 for an isolated MPU6050-only target; other GPIO values remain unset.
- Power changes: hardware values documented; Phase 3.2B module-specific evidence defines proposed 5 V and 3.3 V domains, but full-system power budget and physical integration remain unverified.
- Data-format changes: Phase 2.1 adds the PC-side `ScanFrame` software interface; Phase 2.2 adds Cartesian transform models; Phase 2.3 adds PNG visualization export; Phase 2.4 adds the multi-sensor JSONL recording format; Phase 2.5 reuses that JSONL format for PC-direct C1 captures; Phase 3.1 reuses it for STM32 low-rate sensor telemetry recordings with optional status/raw fields; Phase 3.2A reuses the same recording format for mocked BH1750 serial capture; Phase 3.2C adds BMP280 bring-up JSONL examples and committed BMP280 physical evidence validation; Phase 3.2D adds MPU6050 bring-up JSONL examples for future manual capture.
- Firmware changes: Phase 3.2A adds OpenRF1 application-layer STM32F103RCT6 BH1750 source, Phase 3.2B adds an isolated full-hardware foundation, Phase 3.2C adds an isolated BMP280-only bring-up Keil target, and Phase 3.2D adds an isolated MPU6050-only bring-up Keil target.
- Calibration changes: calibration process documented only.
