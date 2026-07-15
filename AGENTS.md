# Agent Guide

This repository is the ENGR1000P2 Mars Scout Rover software and documentation baseline for a low-cost STM32 mecanum rover, ESP32 communication layer, multiple sensors, and PC visualization tools.

## Durable Rules

- Work only inside this repository.
- Inspect `git status`, this file, and any nested guidance before editing.
- Preserve working code and verified hardware facts.
- Distinguish `CONFIRMED`, `PLANNED`, and `UNVERIFIED`; do not invent hardware values.
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

- Completed phases: Phase 0, Phase 1, Phase 2.1, Phase 2.2, automated verification foundation, Phase 2.3, Phase 2.4, and Phase 2.5.
- Current state: Phase 2.5 software support is complete; physical PC-direct C1 tests still require manual hardware execution and evidence.
- Do not begin Phase 3 or any STM32/ESP32/WiFi integration without an explicit request and the documented hardware-safety prerequisites.

## Confirmed Inventory

- Ranging: RPLIDAR C1 x2 and HC-SR04 x3.
- Motion and pose: four wheel encoders and MPU6050 x1.
- Ground and landmark: TCRT5000 x2 for edge/drop detection and Hall sensor module x1 for magnetic landmark/checkpoint detection.
- Environment: BH1750 x1 for illuminance in lux and BMP280 x1 for temperature and atmospheric pressure.
- Controllers and chassis: STM32 controller board x1, ESP32 board x1, battery/power system, four encoded motors, four mecanum wheels, and existing rover chassis.

Use neutral sensor IDs until mounting is physically verified: `c1_1`, `c1_2`, `ultrasonic_1`, `ultrasonic_2`, `ultrasonic_3`, `tcrt5000_1`, `tcrt5000_2`, `bh1750_1`, `bmp280_1`, `mpu6050_1`, and `hall_1`.

Two C1 units are available. Phase 2.5 must test both independently. One stable C1 is the baseline integration target; simultaneous dual-C1 operation is optional and remains UNVERIFIED until UART, GPIO, bandwidth, buffering, timing, and power feasibility are proven.

## Responsibility Split

- STM32: planned low-level motor control, wheel encoders, local safety, low-rate sensor acquisition, basic odometry support, and local stop/turn state machine.
- ESP32: planned WiFi/data bridge between STM32, at least one C1 in a later phase, and the PC.
- PC: visualization, recording, replay, experiment inspection, export, and later short-range accumulated mapping.

Do not claim real WiFi, serial, sensor acquisition, odometry, mapping, obstacle avoidance, or dual-C1 operation without test evidence.
Do not invent GPIO, UART, I2C address, active polarity, connector order, mounting offset, or power-topology values.
Do not invent COM ports. PC-direct C1 capture must use an explicit user-verified port or a test fixture byte stream.

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
- Phase 3: STM32 integration of HC-SR04, TCRT5000, Hall, BH1750, and BMP280.
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
```

Normal verification after commit and push:

```powershell
.\tools\verify_phase.cmd phase2.5
```

Generated recordings, logs, and figures belong under `.verification/` or ignored data directories and must not be committed.
