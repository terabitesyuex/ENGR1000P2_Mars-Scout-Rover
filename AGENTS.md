# Agent Guide

This repository is the ENGR1000P2 Mars Scout Rover software and documentation baseline for a low-cost STM32 mecanum rover, ESP32 communication layer, multiple sensors, and PC visualization tools.

## Durable Rules

- Work only inside this repository.
- Inspect `git status`, this file, and any nested guidance before editing.
- Preserve working code and verified hardware facts.
- Distinguish `CONFIRMED`, `CONFIRMED_MODULE_EVIDENCE`, `SELLER_DOCUMENTED`, `SELLER_FAMILY_DOCUMENTED`, `PLANNED`, `SOFTWARE_VERIFIED`, `MANUAL_EVIDENCE_VERIFIED`, `MANUAL_ACTION_REQUIRED`, `UNVERIFIED`, and `BLOCKED`; do not invent hardware values.
- Keep hardware access separate from algorithms.
- Keep modules small and single-purpose.
- Use explicit measurement units in names.
- Do not use blocking operations in embedded runtime paths.
- Add or update tests with every implemented module.
- Do not claim tests passed unless they were actually run.
- Do not commit or push unless explicitly requested.
- Update relevant documentation and `CHANGELOG.md` when interfaces change.
- Whenever the user supplies new hardware material, archive source evidence when
  redistribution is appropriate and reconcile every affected current source of
  truth: this file, `HARDWARE_LOCK.md`, `TODO_HARDWARE.md`, the assembly wiring
  plan, BOM/checklists, README/project specification, validators, tests, and
  changelog. Preserve historical phase evidence as historical rather than
  silently rewriting it.
- Stop at the requested phase.

## Current Scope

- Completed phases: Phase 0, Phase 1, Phase 2.1, Phase 2.2, automated verification foundation, Phase 2.3, Phase 2.4, Phase 2.5, Phase 3.1, Phase 3.2A, the Phase 3.2B software foundation, Phase 3.2C isolated BMP280 bring-up evidence, the Phase 3.2D isolated MPU6050 software foundation, the Phase 3.2E isolated HC-SR04 software foundation, the Phase 3.2F isolated ground-sensor software foundation, Phase 4A, and the Phase 4B software-only closed-loop wheel-speed control and motion-safety foundation.
- Current state: Phase 2.5 software and committed physical-evidence validation are complete. The one physical `c1_1` has MANUAL_EVIDENCE_VERIFIED PC-direct capture, repository replay/rendering, bounded 50 x 360 acquisition, target/direction smoke response, and external ROS2/RViz `/scan` visualization. Electrical measurements, vendor health, wall-clock timing, absolute accuracy, final mounting, STM32/ESP32 transport, and full-rover operation remain UNVERIFIED.
- Phase 3.1 software work is complete: versioned STM32 low-rate sensor telemetry, deterministic PC simulator, strict parser, and recording bridge are implemented.
- Phase 3.2A software work is complete: OpenRF1 STM32F103RCT6 + GY-302/BH1750 firmware foundation, mocked PC serial capture, documentation, and verifier support are implemented. Recorded manual evidence verifies the BH1750-only flash, CH340/USART1 telemetry, configured `0x23` BH1750 communication, 500 ms telemetry period, and physical light response; absolute lux calibration remains UNVERIFIED.
- Phase 3.2B software work is complete: isolated OpenRF1 full-hardware firmware foundation, PC contracts, deterministic fixtures, documentation, and verifier support are implemented. Phase 3.2B physical sensor integration has not started.
- Phase 3.2C isolated BMP280 evidence is present: committed evidence verifies FlyMcu flashing of the isolated BMP280 firmware, USART1/CH340 JSONL telemetry, I2C ACK/address `0x76`, chip ID `0x58`, configuration readback, compensated live temperature/pressure telemetry, exact 500 ms periodicity, and a stable 30-second capture. Absolute temperature/pressure accuracy, long-duration operation, shared-I2C concurrency, and full-hardware operation remain UNVERIFIED.
- Phase 3.2D software work is complete: isolated OpenRF1 MPU6050-only firmware source, host-testable conversion/telemetry helpers, Keil target, documentation, tests, and verifier support are implemented. MPU6050 ACK, WHO_AM_I, configuration readback, live IMU telemetry, calibration, axis orientation, shared-I2C concurrency, and full-hardware operation remain UNVERIFIED until physical evidence is recorded.
- Phase 3.2E software work is complete: isolated OpenRF1 HC-SR04-only firmware source, bounded telemetry framing, strict parser, dedicated mockable capture, deterministic fixtures, evidence-candidate lifecycle, A/B handoffs, Keil target, documentation, tests, and verifier support are implemented. CN6 pin order, PA5 TRIG, PA4 ECHO, TIM6, and the external 10 kOhm / 15 kOhm ECHO divider requirement are AUTHORITATIVE_VENDOR_DOCUMENTED. Physical wiring, connector orientation, installed resistor values, trigger pulse, echo pulse, real distance data, timeout behavior, timer accuracy, temperature compensation, and absolute distance accuracy remain UNVERIFIED until physical evidence is recorded.
- Phase 3.2F software work and isolated TCRT5000 evidence closeout are complete. A's sanitized evidence verifies the isolated firmware build/flash, installed PC4 and PC5 TCRT signal connections, labelled 3.3 V/common-GND connections, live raw/debounced response from both TCRT modules, four 100-frame captures without sequence gaps, and exact 50 ms steady-state timestamps. This is MANUAL_EVIDENCE_VERIFIED only for the tested isolated setup. Actual rail/output voltages, output topology, semantic polarity, black/white classification, calibrated distance/threshold, drop safety, Hall behavior, long-duration operation, final mounting, motor-vibration behavior, shared buses, and full-rover operation remain UNVERIFIED.
- Phase 4A software work is complete: typed standard X-layout mecanum kinematics, explicit wheel-side encoder conversion and signs, forward body-twist estimation, exact constant-twist SE(2) integration, deterministic scenarios, version-1 telemetry/recording additions, documentation, tests, and verifier support are implemented. Actual geometry, encoder resolution, gear ratio, counter width, signs, roller orientation, acquisition timing, wheel slip, motor behavior, and physical odometry accuracy remain UNVERIFIED.
- Phase 4B software work is complete: validated body commands, proportional four-wheel desaturation, angular-acceleration limiting, independent discrete PID controllers with conditional anti-windup, deterministic reset/disable, command watchdog, explicit local safety arbitration, synthetic first-order wheel plants, version-1 telemetry/recording additions, CLI, tests, documentation, and verifier support are implemented. Motor rotation, encoder acquisition, physical directions, PWM mapping, usable physical gains, roller orientation, trajectory following, stopping distance, and real closed-loop performance remain UNVERIFIED.
- The OpenRF1 rover-control firmware boundary is present under `firmware/openrf1/app/`: centralized UNKNOWN mappings, injected Motor and Encoder HALs, fixed-point mecanum inverse kinematics, and an inert ARM Compiler 6 link target are SOFTWARE_VERIFIED. It does not select GPIO, PWM, timers, UARTs, connectors, or physical geometry and must not be flashed as operational rover firmware.
- Do not begin Phase 3.2B physical integration, additional physical sensor bring-up, motor/encoder hardware work, ESP32/WiFi implementation, or other hardware bring-up without an explicit request and the documented hardware-safety prerequisites.

## Confirmed Inventory

- Ranging: RPLIDAR C1M1-R2 x1 and HC-SR04 x3.
- Motion and pose: four wheel encoders and MPU6050 x1.
- Ground and landmark: TCRT5000 x2 for edge/drop detection and Hall sensor module x1 for magnetic landmark/checkpoint detection.
- Environment: BH1750 x1 for illuminance in lux and BMP280 x1 for temperature and atmospheric pressure.
- Controllers and chassis: STM32 controller board x1, ESP32 board x1, one
  seller-documented Li-ion pack advertised as 11.1 V, 7800 mAh, 5C, 12.6 V
  fully charged, 70 x 55 x 23 mm, with a DC 5.5 x 2.5 mm male connector; one
  seller-documented 12.6 V/1 A charger with a mating female connector; four
  encoded motors; four mecanum wheels; and the existing rover chassis. Barrel
  polarity and BMS continuous/peak current remain UNVERIFIED.
- Phase 3.2A controller target for BH1750 bring-up: OpenRF1 robot controller with STM32F103RCT6, software I2C on PB1/SCL and PC3/SDA, and USART1 PA9/PA10 at 115200 8N1.

Use neutral sensor IDs until mounting is physically verified: `c1_1`, `ultrasonic_1`, `ultrasonic_2`, `ultrasonic_3`, `tcrt5000_1`, `tcrt5000_2`, `bh1750_1`, `bmp280_1`, `mpu6050_1`, and `hall_1`. Historical version-1 recordings and explicitly synthetic compatibility fixtures may still contain `c1_2`.

Exactly one physical RPLIDAR C1M1-R2 is available. `c1_1` is the only current physical LiDAR sensor and the only active LiDAR integration target. Physical acceptance remains UNVERIFIED. There is no current requirement to compare two physical units, no current dual-C1 integration phase, and no current dual-C1 feasibility evaluation. A future second C1 would require an explicit inventory change plus new electrical, power, UART, bandwidth, buffering, timing, mounting, synchronization, and safety validation.

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
- Phase 4A internal angles and yaw are radians; linear velocity is metres per second and angular velocity is radians per second.
- Phase 4A wheel order is `front_left`, `front_right`, `rear_left`, `rear_right`; mathematical positive rotation is independent of physical wiring and encoder polarity.
- Phase 4B normalized control effort is dimensionless and mathematical; it is not PWM duty, motor voltage, or verified polarity.
- Require explicit finite positive wheel geometry and wheel-side counts per revolution plus four explicit `+1`/`-1` direction multipliers; do not default physical values or signs.
- Native C1 clockwise angles must be converted before `ScanFrame` creation; do not apply native-C1 conversion after a value is already a `ScanPoint`.
- Do not invent mounting offsets, final orientations, GPIOs, UART assignments, I2C addresses, active polarities, voltage interfaces, or connector order.

## Phase Order

- Phase 2.4: multi-sensor recording, replay, reproducible datasets, inventory update, and plan rebaseline.
- Phase 2.5: PC-direct acquisition for the one physical `c1_1`, recording, replay, visualization, and committed evidence validation. Physical scan acquisition is MANUAL_EVIDENCE_VERIFIED; electrical, calibration, final-mounting, and integrated-rover acceptance remain UNVERIFIED.
- Phase 3.1: STM32 low-rate sensor telemetry software foundation, simulator, parser, recording bridge, and manual bring-up checklist.
- Phase 3.2A: OpenRF1 STM32F103RCT6 + GY-302/BH1750 firmware foundation and mocked PC serial-capture workflow.
- Phase 3.2B: OpenRF1 multisensor and communications software foundation for proposed wiring; physical validation remains manual and UNVERIFIED.
- Phase 3.2C: OpenRF1 BMP280-only bring-up firmware, Keil target, and isolated BMP280 physical evidence; absolute accuracy, long-duration operation, shared-I2C concurrency, and full-hardware operation remain UNVERIFIED.
- Phase 3.2D: OpenRF1 MPU6050-only bring-up firmware foundation and tests; physical ACK, WHO_AM_I, configuration readback, live IMU telemetry, calibration, and axis orientation remain UNVERIFIED.
- Phase 3.2E: OpenRF1 HC-SR04-only bring-up firmware foundation and tests; physical wiring, pulses, real distance data, timeout behavior, and accuracy remain UNVERIFIED.
- Phase 3.2F: OpenRF1 ground-sensor-only firmware, tests, and isolated TCRT5000 evidence; voltage measurements, polarity semantics, black/white/drop classification, Hall behavior, long-duration operation, and full-hardware operation remain UNVERIFIED.
- Phase 4A: software-only standard X-layout mecanum kinematics, explicit encoder conversion, deterministic body-twist estimation, and SE(2) odometry foundation; physical values and accuracy remain UNVERIFIED.
- Phase 4B: software-only wheel-speed closed-loop control, command shaping, watchdog, safety arbitration, and deterministic synthetic plant foundation; physical motor/encoder behavior remains UNVERIFIED.
- Phase 4C: future real motor and encoder hardware bring-up, direction discovery, electrical checks, and timer/interrupt/PWM validation; not started.
- Later Phase 4 work: encoder hardware acquisition, measured geometry/signs, MPU6050 integration, motor control, closed-loop motion, calibration, and physical odometry validation.
- Phase 5: STM32-ESP32-PC communication, WiFi transport, and one-C1 baseline integration. A second C1 is a future out-of-scope extension requiring a new inventory and feasibility review.
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
.\tools\verify_phase.cmd phase4a -AllowDirty
.\tools\verify_phase.cmd phase4b -AllowDirty
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
.\tools\verify_phase.cmd phase4a
.\tools\verify_phase.cmd phase4b
```

Generated recordings, logs, and figures belong under `.verification/` or ignored data directories and must not be committed.
