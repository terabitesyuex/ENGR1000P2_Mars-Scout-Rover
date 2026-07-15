# Project Specification

This is the authoritative scope document for the ENGR1000P2 Mars Scout Rover repository.

## Current Objective

Build a low-cost Mars Scout Rover using an STM32 mecanum-wheel chassis, an ESP32 communication layer, multiple sensors, and PC visualization tools. The system must support safe beginner integration, reproducible test evidence, and clear separation between verified hardware facts, planned responsibilities, and unverified implementation details.

## Mandatory Requirements

- Detect nearby obstacles.
- Stop or turn automatically to avoid collision.
- Acquire rover, ranging, ground, landmark, motion, and environmental data.
- Transmit data wirelessly to a computer using WiFi as the current communication baseline.
- Display real-time single-frame 2D LiDAR/radar-style information on the computer.
- Preserve data for testing, replay, validation, and presentation evidence.
- Remain safe when communication or sensors fail.

## Major Enhancements

- Encoder/IMU-assisted rover pose estimation.
- Short-range accumulated 2D environment mapping.
- Use of two RPLIDAR C1 units if hardware feasibility is verified.
- Environmental-change indication using illuminance, temperature, and atmospheric-pressure measurements.

## Optional Future Extensions

These are not baseline requirements: reusable global SLAM mapping, loop closure, global path planning, autonomous frontier exploration, ROS, ROS 2, Nav2, AMCL, Gmapping, `slam_toolbox`, Raspberry Pi, Jetson, and a vehicle-mounted Linux computer.

## Non-Goals

- Reliable real-world dust-storm detection is not claimed.
- ROS and a vehicle-mounted Linux computer are not required.
- Reusable global SLAM mapping is not mandatory.
- Simultaneous dual-C1 operation is not required until feasibility is proven.
- Final GPIO, UART, I2C address, connector order, voltage-interface, polarity, and mounting-offset values are not invented.

## Confirmed Inventory

Ranging:

- RPLIDAR C1 x2.
- HC-SR04 ultrasonic sensor x3.

Motion and pose:

- Four wheel encoders associated with the four drive motors.
- MPU6050 inertial measurement unit x1.

Ground and landmark:

- TCRT5000 reflective infrared sensor x2 for edge/drop detection.
- Hall sensor module x1 for magnetic landmark/checkpoint detection.

Environment:

- BH1750 illuminance sensor x1.
- BMP280 temperature/pressure sensor x1.

Controllers and chassis:

- STM32 controller board x1.
- ESP32 board x1.
- Battery/power system.
- Four encoded motors.
- Four mecanum wheels.
- Existing rover chassis.

## Confirmed Electrical Facts

Preserved verified RPLIDAR C1 facts:

- Exact model in earlier verified files: SLAMTEC RPLIDAR C1M1-R2.
- Connector: XH2.54-5P, four active conductors and one unused position.
- UART: 3.3 V TTL, 460800 baud, 8 data bits, no parity, 1 stop bit.
- Supply: 4.8 V to 5.2 V, typical 5.0 V.
- Startup current: approximately 800 mA.
- Typical operating current: approximately 230 mA at 10 Hz.
- Maximum normal operating current: approximately 260 mA.
- Maximum specified supply ripple: 150 mV.
- External motor PWM conductor: not present.

These facts do not verify the wiring, mounting, serial identifiers, revisions, or operation of either physical C1 unit.

## Planned Architecture

- STM32 planned responsibilities: existing four-mecanum-wheel motor control, wheel encoder acquisition, low-level motor safety, command-timeout stop, MPU6050 acquisition, HC-SR04 acquisition, TCRT5000 edge/drop detection, Hall landmark detection, BH1750 and BMP280 acquisition unless later interface testing requires a different assignment, low-rate sensor preprocessing, basic odometry support, and local stop/turn obstacle-avoidance state machine.
- ESP32 planned responsibilities: WiFi communication with the computer, receive STM32 rover and sensor information, package and transmit data, receive limited configuration/control messages, and interface with at least one RPLIDAR C1 in a later phase.
- PC responsibilities: real-time polar visualization, real-time Cartesian visualization, recording, replay, experiment inspection, later short-range accumulated mapping, and data/figure export.

## Two-C1 Policy

- Sensor IDs remain neutral: `c1_1` and `c1_2`.
- Both C1 units must be tested independently in Phase 2.5.
- One stable C1 is required for the baseline integration target.
- Simultaneous dual-C1 operation is optional pending UART, GPIO, bandwidth, buffering, timing, and power feasibility.
- No final front/rear/upper/lower mounting names may be used until installation is physically verified.

## Environmental-Sensing Policy

- BH1750 records illuminance in lux.
- BMP280 records temperature in degrees Celsius and atmospheric pressure in pascals.
- Simulated environmental-anomaly experiments are allowed.
- Reliable real-world dust-storm detection is not claimed.

## Unverified Integration Details

- Individual C1 serial IDs.
- Individual C1 revisions.
- Operational status of either physical C1.
- Final C1 placement and orientation.
- Simultaneous dual-C1 architecture.
- Exact ESP32 GPIOs.
- Exact UART assignment.
- Exact STM32-ESP32 connector.
- Exact HC-SR04 level-shifting requirements on the physical board.
- Actual BH1750, BMP280, and MPU6050 I2C addresses.
- Physical TCRT5000 and Hall active polarity.
- Battery voltage and capacity unless measured.
- Final power-distribution topology.
- Final sensor mounting offsets.

## Phase Order

- Phase 2.4: multi-sensor recording, replay, reproducible datasets, current hardware inventory update, and project-plan rebaseline.
- Phase 2.5: PC-direct testing of both RPLIDAR C1 units separately, real scan acquisition, distance/orientation checks, device identification, recording, and visualization.
- Phase 3.1: STM32 low-rate sensor telemetry software foundation, deterministic simulator, strict PC parser, Phase 2.4 recording bridge, and manual bring-up checklist.
- Phase 3.2A: OpenRF1 STM32F103RCT6 + GY-302/BH1750 firmware foundation, mocked PC serial-capture workflow, and manual bring-up procedure.
- Phase 3.2B: future physical STM32 integration of remaining HC-SR04, TCRT5000, Hall, BMP280, and additional validated sensors, including low-level sensor safety and environmental-data acquisition.
- Phase 4: wheel encoders, MPU6050, mecanum kinematics, closed-loop motion, and odometry.
- Phase 5: STM32-ESP32-computer communication, WiFi transport, one-C1 baseline integration, then optional dual-C1 feasibility evaluation.
- Phase 6: real-time computer visualization, rover trajectory, and short-range encoder/IMU-assisted accumulated 2D mapping.
- Phase 7: local autonomous obstacle stop/turn behavior.
- Phase 8: full Mars-like venue integration, environmental experiments, validation, reliability testing, and final presentation evidence.

## Phase 2.4 Acceptance Philosophy

Phase 2.4 is software-only. It accepts deterministic synthetic recordings and replay as evidence that the PC data interfaces are ready for later real hardware drivers. It does not prove wiring, physical safety, sensor calibration, WiFi operation, odometry, mapping, SLAM, or autonomous avoidance.

## Phase 2.5 Acceptance Philosophy

Phase 2.5 adds PC-direct C1 software acquisition boundaries and safe integration into the existing `ScanFrame`, JSONL recording, replay, and visualization pipeline. Automated tests use mocked byte streams and do not open serial ports. Manual hardware acceptance still requires independent tests for `c1_1` and `c1_2`, redacted device identity, health, bounded capture, distance/orientation checks, and saved replay/visualization evidence.

Phase 2.5 does not implement STM32 integration, ESP32 communication, WiFi, ROS, SLAM, navigation, obstacle avoidance, or simultaneous dual-C1 operation.

## Phase 3.1 Acceptance Philosophy

Phase 3.1 is a software-foundation phase. It defines `mars_scout_stm32_sensor_telemetry` version `1`, validates deterministic software telemetry for HC-SR04, TCRT5000, Hall, BH1750, and BMP280, and bridges validated messages into the existing Phase 2.4 recording format. It does not prove any real STM32 pin, connector, voltage, polarity, timing, I2C address, or physical sensor behavior.

Phase 3.1 does not implement real hardware access, serial-port access, GPIO, I2C, timers, STM32 flashing, ESP32 communication, WiFi, motor control, wheel encoders, MPU6050 integration, mapping, SLAM, navigation, obstacle avoidance, or autonomous motion.

## Phase 3.2A Acceptance Philosophy

Phase 3.2A is the first real-firmware preparation step for one low-rate sensor only: GY-302/BH1750 as `bh1750_1` on the OpenRF1 STM32F103RCT6 controller. It records the confirmed board, MCU, PB1/PC3 software-I2C pins, USART1 serial reference, planned GY-302 wiring, and BH1750 public 7-bit address `0x23`. It adds application-layer firmware source for the vendor Keil STM32F103RC project, but does not vendor the STM32F10x library or claim a standalone firmware build tree.

Phase 3.2A automated evidence is software-only: pure conversion/state-machine tests, file-backed mocked serial capture, strict Phase 3.1 parser reuse, Phase 2.4 recording conversion, and verifier smoke artifacts. It does not access real COM ports, USB devices, GPIO, I2C, flashing tools, or sensors. Keil build, flash, ACK at `0x23`, COM-port identity, and real lux response remain MANUAL_ACTION_REQUIRED.

Phase 3.2A does not implement BMP280, HC-SR04, TCRT5000, Hall, MPU6050, motors, encoders, mecanum kinematics, ESP32/WiFi, C1 hardware integration, mapping, SLAM, navigation, obstacle avoidance, or Phase 3.2B.

## Course Validation Evidence

Evidence should include software test logs, deterministic JSONL recordings, replay output, rendered figures, future bench hardware logs, future stationary physical tests, future moving-rover tests, safety test outcomes, and final presentation artifacts. Physical validations must not be marked complete until they are actually performed.
