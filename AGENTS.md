# Agent Guide

This repository is the ENGR1000P2 Mars Scout Rover software and documentation baseline for a low-cost STM32 mecanum rover, ESP32 communication layer, multiple sensors, and PC visualization tools.

## Durable Rules

- Work only inside this repository.
- Inspect `git status`, this file, and any nested guidance before editing.
- Preserve working code and verified hardware facts.
- Distinguish `CONFIRMED`, `CONFIRMED_MODULE_EVIDENCE`, `PLANNED`, `SOFTWARE_VERIFIED`, `MANUAL_EVIDENCE_VERIFIED`, `MANUAL_ACTION_REQUIRED`, `UNVERIFIED`, and `BLOCKED`; do not invent hardware values.
- Keep hardware access separate from algorithms.
- Keep modules small and single-purpose.
- Use explicit measurement units in names.
- Do not use blocking operations in embedded runtime paths.
- Add or update tests with every implemented module.
- Do not claim tests passed unless they were actually run.
- Do not commit or push unless explicitly requested.
- Update relevant documentation and `CHANGELOG.md` when interfaces change.
- Stop at the requested phase.

## Current Scope

- Completed phases: Phase 0, Phase 1, Phase 2.1, Phase 2.2, automated verification foundation, Phase 2.3, Phase 2.4, Phase 2.5, Phase 3.1, Phase 3.2A, the Phase 3.2B software foundation, Phase 3.2C isolated BMP280 bring-up evidence, the Phase 3.2D isolated MPU6050 software foundation, the Phase 3.2E isolated HC-SR04 software foundation, and the Phase 3.2F isolated ground-sensor software foundation.
- Current state: Phase 2.5 software foundation is complete; physical C1 validation remains a manual UNVERIFIED activity.
- Phase 3.1 software work is complete: versioned STM32 low-rate sensor telemetry, deterministic PC simulator, strict parser, and recording bridge are implemented.
- Phase 3.2A software work is complete: OpenRF1 STM32F103RCT6 + GY-302/BH1750 firmware foundation, mocked PC serial capture, documentation, and verifier support are implemented. Recorded manual evidence verifies the BH1750-only flash, CH340/USART1 telemetry, configured `0x23` BH1750 communication, 500 ms telemetry period, and physical light response; absolute lux calibration remains UNVERIFIED.
- Phase 3.2B software work is complete: isolated OpenRF1 full-hardware firmware foundation, PC contracts, deterministic fixtures, documentation, and verifier support are implemented. Phase 3.2B physical sensor integration has not started.
- Phase 3.2C isolated BMP280 evidence is present: committed evidence verifies FlyMcu flashing of the isolated BMP280 firmware, USART1/CH340 JSONL telemetry, I2C ACK/address `0x76`, chip ID `0x58`, configuration readback, compensated live temperature/pressure telemetry, exact 500 ms periodicity, and a stable 30-second capture. Absolute temperature/pressure accuracy, long-duration operation, shared-I2C concurrency, and full-hardware operation remain UNVERIFIED.
- Phase 3.2D software work is complete: isolated OpenRF1 MPU6050-only firmware source, host-testable conversion/telemetry helpers, Keil target, documentation, tests, and verifier support are implemented. MPU6050 ACK, WHO_AM_I, configuration readback, live IMU telemetry, calibration, axis orientation, shared-I2C concurrency, and full-hardware operation remain UNVERIFIED until physical evidence is recorded.
- Phase 3.2E software work is complete: isolated OpenRF1 HC-SR04-only firmware source, host-testable timing/telemetry helpers, Keil target, documentation, tests, and verifier support are implemented. CN6 pin order, PA5 TRIG, PA4 ECHO, TIM6, and the external 10 kOhm / 15 kOhm ECHO divider requirement are AUTHORITATIVE_VENDOR_DOCUMENTED. Physical wiring, connector orientation, installed resistor values, trigger pulse, echo pulse, real distance data, timeout behavior, timer accuracy, temperature compensation, and absolute distance accuracy remain UNVERIFIED until physical evidence is recorded.
- Phase 3.2F software work is complete: isolated OpenRF1 ground-sensor-only firmware source, host-testable debounce/telemetry helpers, Keil target, documentation, tests, and verifier support are implemented. Tracking connector signal 1 / X1 / PC4, signal 2 / X2 / PC5, signal 3 / X3 / PB0, connector pin order, vendor floating-input mode, schematic X4 = PC14, and old example X4 = PB1 conflict are AUTHORITATIVE_VENDOR_DOCUMENTED. TCRT 3.3 V supply, Hall 5 V supply, Hall S external 10 kOhm / 15 kOhm divider, Hall S direct-to-PB0 prohibition, and signal 4 exclusion are DESIGN_LOCKED. Physical wiring, connector orientation, rail voltages, output voltages, active polarity, surface behavior, magnetic behavior, real debounce suitability, actual 50 ms serial periodicity, and full-hardware operation remain UNVERIFIED.
- Do not begin Phase 3.2B physical integration, additional physical sensor bring-up, motor/encoder work, ESP32/WiFi implementation, or hardware bring-up without an explicit request and the documented hardware-safety prerequisites.

## Confirmed Inventory

- Ranging: RPLIDAR C1 x1 and HC-SR04 x3.
- Motion and pose: four wheel encoders and MPU6050 x1.
- Ground and landmark: TCRT5000 x2 for edge/drop detection and Hall sensor module x1 for magnetic landmark/checkpoint detection.
- Environment: BH1750 x1 for illuminance in lux and BMP280 x1 for temperature and atmospheric pressure.
- Controllers and chassis: STM32 controller board x1, ESP32 board x1, battery/power system, four encoded motors, four mecanum wheels, and existing rover chassis.
- Phase 3.2A controller target for BH1750 bring-up: OpenRF1 robot controller with STM32F103RCT6, software I2C on PB1/SCL and PC3/SDA, and USART1 PA9/PA10 at 115200 8N1.

Use neutral physical sensor IDs until mounting is physically verified: `c1_1`, `ultrasonic_1`, `ultrasonic_2`, `ultrasonic_3`, `tcrt5000_1`, `tcrt5000_2`, `bh1750_1`, `bmp280_1`, `mpu6050_1`, and `hall_1`. `c1_2` may remain in deterministic software fixtures and backward-compatibility tests only; it does not represent a second physical C1.

One physical C1 is available. Phase 2.5 physical acceptance applies only to `c1_1`, which is also the Phase 5 integration target. Dual-C1 hardware operation is outside the current inventory and baseline scope.

All three HC-SR04 modules physically exist. The Phase 3.2E PA5/PA4/CN6 design is an isolated one-module baseline only, currently assigned neutrally to `ultrasonic_1`; final GPIO and connector paths for simultaneous `ultrasonic_2` and `ultrasonic_3` operation remain UNVERIFIED.

## Responsibility Split

- STM32: planned low-level motor control, wheel encoders, local safety, low-rate sensor acquisition, basic odometry support, and local stop/turn state machine.
- ESP32: planned WiFi/data bridge between STM32, the physical `c1_1` in a later phase, and the PC.
- PC: visualization, recording, replay, experiment inspection, export, and later short-range accumulated mapping.

Do not claim real WiFi, serial, sensor acquisition, odometry, mapping, obstacle avoidance, or hardware that is not in the confirmed inventory.
Do not invent GPIO, UART, I2C address, active polarity, connector order, mounting offset, or power-topology values.
Do not invent COM ports. PC-direct C1 capture must use an explicit user-verified port or a test fixture byte stream.
OpenRF1 CH340 COM ports must be user-selected; automated tests may use only mock input files or injected readers.
No hardware result may be claimed without evidence.
Do not treat HC-SR04 timeout as a valid zero-distance obstacle.
Preserve raw TCRT5000 and Hall states until active polarity is physically verified.
The Hall sensor is for magnetic landmark/checkpoint detection, not odometry.
Do not treat BH1750 communication failures as zero-lux readings; valid darkness and invalid telemetry must remain distinct.

## Coordinates And Units

- `ScanPoint.angle_deg`: rover-frame degrees, `0` forward, positive counterclockwise.
- `ScanPoint.distance_mm`: millimetres.
- Cartesian distances: metres.
- `+x`: rover forward.
- `+y`: rover left.
- Native C1 clockwise angles must be converted before `ScanFrame` creation; do not apply native-C1 conversion after a value is already a `ScanPoint`.
- Do not invent mounting offsets, final orientations, GPIOs, UART assignments, I2C addresses, active polarities, voltage interfaces, or connector order.

## Phase Order

- Phase 2.4: multi-sensor recording, replay, reproducible datasets, inventory update, and plan rebaseline.
- Phase 2.5: PC-direct testing of the single physical C1 as `c1_1`, real scan acquisition, device identification, recording, and visualization. Any `c1_2` coverage is synthetic compatibility testing only.
- Phase 3.1: STM32 low-rate sensor telemetry software foundation, simulator, parser, recording bridge, and manual bring-up checklist.
- Phase 3.2A: OpenRF1 STM32F103RCT6 + GY-302/BH1750 firmware foundation and mocked PC serial-capture workflow.
- Phase 3.2B: OpenRF1 multisensor and communications software foundation for proposed wiring; physical validation remains manual and UNVERIFIED.
- Phase 3.2C: OpenRF1 BMP280-only bring-up firmware, Keil target, and isolated BMP280 physical evidence; absolute accuracy, long-duration operation, shared-I2C concurrency, and full-hardware operation remain UNVERIFIED.
- Phase 3.2D: OpenRF1 MPU6050-only bring-up firmware foundation and tests; physical ACK, WHO_AM_I, configuration readback, live IMU telemetry, calibration, and axis orientation remain UNVERIFIED.
- Phase 3.2E: OpenRF1 HC-SR04-only bring-up firmware foundation and tests; physical wiring, pulses, real distance data, timeout behavior, and accuracy remain UNVERIFIED.
- Phase 3.2F: OpenRF1 ground-sensor-only bring-up firmware foundation and tests; physical wiring, voltage levels, active polarity, surface behavior, magnetic behavior, serial periodicity, and full-hardware operation remain UNVERIFIED.
- Phase 4: wheel encoders, MPU6050, mecanum kinematics, closed-loop motion, and odometry.
- Phase 5: STM32-ESP32-PC communication, WiFi transport, and single-C1 (`c1_1`) integration.
- Phase 6: real-time PC visualization, rover trajectory, and short-range encoder/IMU-assisted accumulated 2D mapping.
- Phase 7: local autonomous obstacle stop/turn behavior.
- Phase 8: Mars-like venue integration, environmental experiments, validation, reliability testing, and final presentation evidence.

ROS, ROS 2, Nav2, AMCL, Gmapping, `slam_toolbox`, Raspberry Pi, Jetson, and a vehicle-mounted Linux computer are not baseline requirements.

## Verification

Run targeted tests, regression tests, the complete PC suite, and the phase verifier before declaring a phase complete. Development verification for the latest phase:

```powershell
.\tools\verify_phase.cmd phase2.5 -AllowDirty
.\tools\verify_phase.cmd phase3.1 -AllowDirty
.\tools\verify_phase.cmd phase3.2a -AllowDirty
.\tools\verify_phase.cmd phase3.2b -AllowDirty
.\tools\verify_phase.cmd phase3.2c -AllowDirty
.\tools\verify_phase.cmd phase3.2d -AllowDirty
.\tools\verify_phase.cmd phase3.2e -AllowDirty
.\tools\verify_phase.cmd phase3.2f -AllowDirty
```

Normal verification after commit and push:

```powershell
.\tools\verify_phase.cmd phase2.5
.\tools\verify_phase.cmd phase3.1
.\tools\verify_phase.cmd phase3.2a
.\tools\verify_phase.cmd phase3.2b
.\tools\verify_phase.cmd phase3.2c
.\tools\verify_phase.cmd phase3.2d
.\tools\verify_phase.cmd phase3.2e
.\tools\verify_phase.cmd phase3.2f
```

Generated recordings, logs, and figures belong under `.verification/` or ignored data directories and must not be committed.
