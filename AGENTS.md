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

- Completed phases: Phase 0, Phase 1, Phase 2.1, Phase 2.2, automated verification foundation, Phase 2.3, Phase 2.4, Phase 2.5, Phase 3.1, Phase 3.2A, and the Phase 3.2B software foundation.
- Current state: Phase 2.5 software foundation is complete; physical C1 validation remains a manual UNVERIFIED activity.
- Phase 3.1 software work is complete: versioned STM32 low-rate sensor telemetry, deterministic PC simulator, strict parser, and recording bridge are implemented.
- Phase 3.2A software work is complete: OpenRF1 STM32F103RCT6 + GY-302/BH1750 firmware foundation, mocked PC serial capture, documentation, and verifier support are implemented. Recorded manual evidence verifies the BH1750-only flash, CH340/USART1 telemetry, configured `0x23` BH1750 communication, 500 ms telemetry period, and physical light response; absolute lux calibration remains UNVERIFIED.
- Phase 3.2B software work is complete: isolated OpenRF1 full-hardware firmware foundation, PC contracts, deterministic fixtures, documentation, and verifier support are implemented. Phase 3.2B physical sensor integration has not started.
- Do not begin Phase 3.2B physical integration, additional physical sensor bring-up, motor/encoder work, ESP32/WiFi implementation, or hardware bring-up without an explicit request and the documented hardware-safety prerequisites.

## Confirmed Inventory

- Ranging: RPLIDAR C1 x2 and HC-SR04 x3.
- Motion and pose: four wheel encoders and MPU6050 x1.
- Ground and landmark: TCRT5000 x2 for edge/drop detection and Hall sensor module x1 for magnetic landmark/checkpoint detection.
- Environment: BH1750 x1 for illuminance in lux and BMP280 x1 for temperature and atmospheric pressure.
- Controllers and chassis: STM32 controller board x1, ESP32 board x1, battery/power system, four encoded motors, four mecanum wheels, and existing rover chassis.
- Phase 3.2A controller target for BH1750 bring-up: OpenRF1 robot controller with STM32F103RCT6, software I2C on PB1/SCL and PC3/SDA, and USART1 PA9/PA10 at 115200 8N1.

Use neutral sensor IDs until mounting is physically verified: `c1_1`, `c1_2`, `ultrasonic_1`, `ultrasonic_2`, `ultrasonic_3`, `tcrt5000_1`, `tcrt5000_2`, `bh1750_1`, `bmp280_1`, `mpu6050_1`, and `hall_1`.

Two C1 units are available. Phase 2.5 must test both independently. One stable C1 is the baseline integration target; simultaneous dual-C1 operation is optional and remains UNVERIFIED until UART, GPIO, bandwidth, buffering, timing, and power feasibility are proven.

## Responsibility Split

- STM32: planned low-level motor control, wheel encoders, local safety, low-rate sensor acquisition, basic odometry support, and local stop/turn state machine.
- ESP32: planned WiFi/data bridge between STM32, at least one C1 in a later phase, and the PC.
- PC: visualization, recording, replay, experiment inspection, export, and later short-range accumulated mapping.

Do not claim real WiFi, serial, sensor acquisition, odometry, mapping, obstacle avoidance, or dual-C1 operation without test evidence.
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
- Phase 2.5: PC-direct testing of both C1 units separately, real scan acquisition, device identification, recording, and visualization.
- Phase 3.1: STM32 low-rate sensor telemetry software foundation, simulator, parser, recording bridge, and manual bring-up checklist.
- Phase 3.2A: OpenRF1 STM32F103RCT6 + GY-302/BH1750 firmware foundation and mocked PC serial-capture workflow.
- Phase 3.2B: OpenRF1 multisensor and communications software foundation for proposed wiring; physical validation remains manual and UNVERIFIED.
- Phase 4: wheel encoders, MPU6050, mecanum kinematics, closed-loop motion, and odometry.
- Phase 5: STM32-ESP32-PC communication, WiFi transport, one-C1 baseline integration, then optional dual-C1 feasibility evaluation.
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
```

Normal verification after commit and push:

```powershell
.\tools\verify_phase.cmd phase2.5
.\tools\verify_phase.cmd phase3.1
.\tools\verify_phase.cmd phase3.2a
.\tools\verify_phase.cmd phase3.2b
```

Generated recordings, logs, and figures belong under `.verification/` or ignored data directories and must not be committed.
