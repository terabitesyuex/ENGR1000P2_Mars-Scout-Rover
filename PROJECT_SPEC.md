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
- Use of one physical RPLIDAR C1 as the baseline LiDAR integration target.
- Environmental-change indication using illuminance, temperature, and atmospheric-pressure measurements.

## Optional Future Extensions

These are not baseline requirements: reusable global SLAM mapping, loop closure, global path planning, autonomous frontier exploration, ROS, ROS 2, Nav2, AMCL, Gmapping, `slam_toolbox`, Raspberry Pi, Jetson, and a vehicle-mounted Linux computer.

## Non-Goals

- Reliable real-world dust-storm detection is not claimed.
- ROS and a vehicle-mounted Linux computer are not required.
- Reusable global SLAM mapping is not mandatory.
- A second C1 is not current scope; adding one requires an explicit inventory change and new feasibility review.
- Final GPIO, UART, I2C address, connector order, voltage-interface, polarity, and mounting-offset values are not invented.

## Confirmed Inventory

Ranging:

- RPLIDAR C1M1-R2 x1.
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
- The user reports complete vehicle assembly according to the repository wiring
  plan. Physical installation, electrical acceptance, and full-rover operation
  remain UNVERIFIED until evidence is recorded.
- ESP32 board x1.
- Li-ion battery pack x1: seller-documented 11.1 V, 7800 mAh, 5C, 12.6 V fully
  charged, 70 x 55 x 23 mm, DC 5.5 x 2.5 mm male connector.
- Battery charger x1: seller-documented 12.6 V/1 A with DC 5.5 x 2.5 mm female
  connector; charging requires the pack to be disconnected from the rover.
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

These facts do not verify the wiring, mounting, serial identifier, revision, or operation of the one physical C1 unit.

## Planned Architecture

- STM32 planned responsibilities: existing four-mecanum-wheel motor control, wheel encoder acquisition, low-level motor safety, command-timeout stop, MPU6050 acquisition, HC-SR04 acquisition, TCRT5000 edge/drop detection, Hall landmark detection, BH1750 and BMP280 acquisition unless later interface testing requires a different assignment, low-rate sensor preprocessing, basic odometry support, and local stop/turn obstacle-avoidance state machine.
- ESP32 planned responsibilities: WiFi communication with the computer, receive STM32 rover and sensor information, package and transmit data, receive limited configuration/control messages, and interface with at least one RPLIDAR C1 in a later phase.
- PC responsibilities: real-time polar visualization, real-time Cartesian visualization, recording, replay, experiment inspection, later short-range accumulated mapping, and data/figure export.

## Single-C1 Policy

- The current physical LiDAR inventory is exactly one RPLIDAR C1M1-R2 with ID `c1_1`.
- Phase 2.5 acceptance covers `c1_1` only. PC-direct acquisition and visualization are MANUAL_EVIDENCE_VERIFIED; electrical, calibration, mounting, and integrated-rover acceptance remain UNVERIFIED.
- There is no current requirement to compare two devices or evaluate dual-C1 feasibility.
- Historical version-1 recordings and explicitly synthetic compatibility fixtures may contain `c1_2`; this does not indicate current hardware.
- A future second C1 requires an explicit inventory change and new electrical, power, UART, bandwidth, buffering, timing, mounting, synchronization, and safety validation.
- No final front/rear/upper/lower mounting names may be used until installation is physically verified.

## Environmental-Sensing Policy

- BH1750 records illuminance in lux.
- BMP280 records temperature in degrees Celsius and atmospheric pressure in pascals.
- Simulated environmental-anomaly experiments are allowed.
- Reliable real-world dust-storm detection is not claimed.

## Unverified Integration Details

- C1 serial ID.
- C1 revision.
- Complete operational acceptance of the physical C1 beyond the recorded PC-direct acquisition evidence.
- Final C1 placement and orientation.
- ESP32 module UART pins have CONFIRMED_MODULE_EVIDENCE for GPIO21 TX and GPIO20 RX; physical link operation remains UNVERIFIED.
- OpenRF1 USART2 PA2/PA3 and USART3 PB10/PB11 mappings are
  AUTHORITATIVE_VENDOR_DOCUMENTED; installed harness operation remains
  UNVERIFIED.
- STM32-ESP32 H6/USART3 is DESIGN_LOCKED; installed operation remains
  UNVERIFIED.
- HC-SR04 Phase 3.2E isolated CN6 pin order, PA5 TRIG, PA4 ECHO, TIM6, and required external 10 kOhm / 15 kOhm ECHO divider are AUTHORITATIVE_VENDOR_DOCUMENTED. Physical installation, voltages, pulses, and distance data remain UNVERIFIED.
- Ground-sensor Phase 3.2F isolated tracking-connector mappings are AUTHORITATIVE_VENDOR_DOCUMENTED: signal 1 / X1 / PC4, signal 2 / X2 / PC5, signal 3 / X3 / PB0, connector pin 1: GND, pin 2: X4 / schematic PC14, pin 3: X3 / PB0, pin 4: X2 / PC5, pin 5: X1 / PC4, pin 6: VCC_5V. The old example maps X4 to PB1, so signal 4 / X4 remains unused. Installed PC4/PC5 TCRT connections, live response, and exact 50 ms steady-state capture timing are MANUAL_EVIDENCE_VERIFIED. Rail/output voltages, polarity semantics, black/white/drop classification, Hall behavior, final mounting, and full-rover operation remain UNVERIFIED.
- BH1750 communication at configured address `0x23` is MANUAL_EVIDENCE_VERIFIED for the recorded Phase 3.2A run. BMP280 ACK/address `0x76`, chip ID `0x58`, configuration readback, compensated live temperature/pressure telemetry, and 500 ms periodicity are PHYSICAL_EVIDENCE_VERIFIED for the isolated Phase 3.2C capture. MPU6050 ACK/address `0x68`, WHO_AM_I `0x68`, isolated configuration readback, live IMU JSON telemetry, startup gyro-bias calibration, approximately 10 Hz output, 15-second no-sequence-loss capture, and isolated axis response are MANUAL_EVIDENCE_VERIFIED for the isolated Phase 3.2D bring-up. BMP280/MPU6050 shared-I2C concurrency, MPU6050 absolute accuracy, final rover-frame alignment, and complete full-hardware operation remain UNVERIFIED.
- Physical TCRT5000 and Hall active polarity.
- Battery advertised values are seller-documented; actual voltage/capacity,
  connector polarity, BMS limits, charger behavior, and installed power
  performance remain unverified.
- Final power-distribution topology.
- Final sensor mounting offsets.

## Phase Order

- Phase 2.4: multi-sensor recording, replay, reproducible datasets, current hardware inventory update, and project-plan rebaseline.
- Phase 2.5: PC-direct acquisition, recording, replay, visualization, and evidence validation for one physical `c1_1`; electrical and calibration closeout remain future manual work.
- Phase 3.1: STM32 low-rate sensor telemetry software foundation, deterministic simulator, strict PC parser, Phase 2.4 recording bridge, and manual bring-up checklist.
- Phase 3.2A: OpenRF1 STM32F103RCT6 + GY-302/BH1750 firmware foundation, mocked PC serial-capture workflow, and manual bring-up procedure.
- Phase 3.2B: OpenRF1 multisensor and communications software foundation for proposed wiring; physical STM32 integration and validation remain manual future work.
- Phase 3.2C: isolated OpenRF1 BMP280-only physical bring-up firmware, Keil target, and recorded BMP280-only physical evidence; absolute accuracy, long-duration operation, shared-I2C concurrency, and full-hardware operation remain unverified.
- Phase 3.2D: isolated OpenRF1 MPU6050-only software bring-up firmware, Keil target, host-side tests, verifier support, startup gyro-bias calibration software, and isolated manual evidence; absolute accuracy, calibration motion rejection, long-duration drift, final rover-frame axis alignment, shared-I2C operation, and complete rover integration remain unverified.
- Phase 3.2E: isolated OpenRF1 HC-SR04-only software bring-up firmware, PA5/PA4/TIM6 vendor-documented design lock, external ECHO divider requirement, Keil target, host-side tests, and verifier support; physical wiring, pulses, real distance data, timeout behavior, and absolute accuracy remain unverified.
- Phase 3.2F: isolated OpenRF1 ground-sensor-only firmware, X1/PC4 and X2/PC5 TCRT5000 mappings, protected X3/PB0 Hall design, host-side tests, verifier support, and sanitized isolated TCRT5000 evidence. A's evidence verifies build/flash, installed PC4/PC5 signal connections, labelled 3.3 V/common-GND connections, live raw/debounced response, four gap-free 100-frame captures, and exact 50 ms steady-state timestamps. Electrical measurements, semantic polarity, black/white/drop classification, Hall behavior, long-duration behavior, and full-rover operation remain unverified.
- Phase 4A: software-only mecanum kinematics, encoder conversion, and odometry foundation.
- Phase 4B: software-only wheel-speed control, command shaping, watchdog, safety arbitration, and synthetic plant foundation.
- Phase 4C: future real motor/encoder hardware bring-up and physical direction/timer/interrupt/PWM validation.
- Later Phase 4: physical PID tuning, MPU6050-assisted pose estimation, real closed-loop motion, and physical odometry validation.
- Phase 5: STM32-ESP32-computer communication, WiFi transport, and one-C1 baseline integration.
- Phase 6: real-time computer visualization, rover trajectory, and short-range encoder/IMU-assisted accumulated 2D mapping.
- Phase 7: local autonomous obstacle stop/turn behavior.
- Phase 8: full Mars-like venue integration, environmental experiments, validation, reliability testing, and final presentation evidence.

## Phase 2.4 Acceptance Philosophy

Phase 2.4 is software-only. It accepts deterministic synthetic recordings and replay as evidence that the PC data interfaces are ready for later real hardware drivers. It does not prove wiring, physical safety, sensor calibration, WiFi operation, odometry, mapping, SLAM, or autonomous avoidance.

## Phase 2.5 Acceptance Philosophy

Phase 2.5 adds PC-direct C1 software acquisition boundaries and safe integration into the existing `ScanFrame`, JSONL recording, replay, and visualization pipeline. Automated tests use mocked byte streams and do not open serial ports. Committed manual evidence verifies physical `c1_1` acquisition, bounded JSONL recording, replay/render output, target/direction smoke response, and external RViz `/scan` visualization. Vendor health, electrical measurements, wall-clock timing, corrupt/dropped-node accounting, absolute accuracy, and final mounting remain UNVERIFIED.

Phase 2.5 does not implement STM32 integration, ESP32 communication, WiFi, ROS, SLAM, navigation, obstacle avoidance, or simultaneous dual-C1 operation. ROS2/RViz appears only as user-provided external diagnostic evidence and is not a baseline dependency.

## Phase 3.1 Acceptance Philosophy

Phase 3.1 is a software-foundation phase. It defines `mars_scout_stm32_sensor_telemetry` version `1`, validates deterministic software telemetry for HC-SR04, TCRT5000, Hall, BH1750, and BMP280, and bridges validated messages into the existing Phase 2.4 recording format. It does not prove any real STM32 pin, connector, voltage, polarity, timing, I2C address, or physical sensor behavior.

Phase 3.1 does not implement real hardware access, serial-port access, GPIO, I2C, timers, STM32 flashing, ESP32 communication, WiFi, motor control, wheel encoders, MPU6050 integration, mapping, SLAM, navigation, obstacle avoidance, or autonomous motion.

## Phase 3.2A Acceptance Philosophy

Phase 3.2A is the first real-firmware preparation step for one low-rate sensor only: GY-302/BH1750 as `bh1750_1` on the OpenRF1 STM32F103RCT6 controller. It records the confirmed board, MCU, PB1/PC3 software-I2C pins, USART1 serial reference, GY-302 wiring, and BH1750 public 7-bit address `0x23`. It adds application-layer firmware source for the vendor Keil STM32F103RC project.

Phase 3.2A automated evidence is software-only: pure conversion/state-machine tests, file-backed mocked serial capture, strict Phase 3.1 parser reuse, Phase 2.4 recording conversion, and verifier smoke artifacts. It does not access real COM ports, USB devices, GPIO, I2C, flashing tools, or sensors. Recorded manual evidence verifies firmware flash, CH340/USART1 telemetry, BH1750 communication at configured address `0x23`, a 500 ms telemetry period, and physical light response. Absolute illuminance calibration remains UNVERIFIED.

Phase 3.2A does not implement BMP280, HC-SR04, TCRT5000, Hall, MPU6050, motors, encoders, mecanum kinematics, ESP32/WiFi, C1 hardware integration, mapping, SLAM, navigation, obstacle avoidance, or Phase 3.2B.

## Phase 3.2B Acceptance Philosophy

Phase 3.2B is a software-foundation phase for the proposed complete OpenRF1 hardware wiring. It preserves the Phase 3.2A BH1750-only application, adds an isolated full-hardware Keil project, and prepares bounded cooperative firmware foundations for shared I2C, BMP280, MPU6050, HC-SR04, TCRT5000, Hall, RPLIDAR C1 byte transport, and STM32-to-ESP32 transport.

Phase 3.2B automated evidence is software-only: pure logic tests, deterministic telemetry fixtures, strict parser and recording bridge coverage, binary frame golden vectors, static firmware/source audits, and local Keil build evidence. It does not access real COM ports, USB devices, GPIO, I2C, WiFi, flashing tools, or sensors. The revised electrical contract uses module-specific evidence for separate 5 V and 3.3 V domains but does not prove physical integration. Physical multisensor wiring, voltage levels, power integrity, BMP280/MPU6050 ACKs, USART2/USART3 operation, sensor polarity, ultrasonic Echo VOH/timing, RPLIDAR operation, ESP32 operation, concurrent operation, and real full-system sensor data remain UNVERIFIED.

Phase 3.2C isolates BMP280 physical bring-up from the Phase 3.2A BH1750 target and the Phase 3.2B full-hardware target. It adds `OpenRF1_BMP280_Bringup.uvprojx`, source under `firmware/openrf1/bmp280_bringup/`, host-side tests for chip ID `0x58`, calibration parsing, configuration register values, compensation, telemetry formatting, target isolation, and committed evidence validation. The formal capture uses BMP280 VCC -> OpenRF1 3.3 V, GND -> GND, SCL -> PB1/B1, SDA -> PC3/C3, CSB -> 3.3 V, and SDO -> GND for address `0x76`. Repository automation does not flash hardware or access real GPIO/I2C/COM ports; it validates the committed evidence offline. ACK at `0x76`, chip ID `0x58`, configuration readback, calibration-register path sufficient for compensated output, live compensated temperature/pressure telemetry, exact 500 ms periodicity, no I2C errors, and a stable 30-second isolated capture are PHYSICAL_EVIDENCE_VERIFIED. Absolute temperature/pressure accuracy, environmental-reference comparison, long-duration operation, shared-I2C concurrency, and complete full-hardware operation remain UNVERIFIED.

Phase 3.2D isolates MPU6050 software bring-up from the Phase 3.2A BH1750 target, Phase 3.2B full-hardware target, and Phase 3.2C BMP280 target. It adds `OpenRF1_MPU6050_Bringup.uvprojx`, source under `firmware/openrf1/mpu6050_bringup/`, host-side tests for WHO_AM_I `0x68`, register configuration values, 14-byte burst decoding, raw-to-g/dps/temperature conversion, telemetry formatting, startup gyro-bias semantics, offline JSONL parsing, and target isolation. A's sanitized manual report covers the isolated wiring, MPU6050 ACK/address `0x68`, WHO_AM_I `0x68`, configuration readback, live IMU telemetry, startup gyro-bias semantics, approximately 10 Hz output during a 15-second isolated test with no reported sequence loss, and isolated sensor-axis response. Repository automation does not flash hardware or access real GPIO/I2C/COM ports. Exact electrical measurements, continuity, delay-loop tuning, build/HEX metadata, exact timing statistics, and exact bias/noise statistics are UNVERIFIED, along with absolute accuracy, calibration motion rejection, long-duration thermal drift, final rover-frame axis alignment, shared-I2C concurrency, and complete full-hardware operation.

Phase 3.2E isolates HC-SR04 software bring-up from the earlier OpenRF1 targets. It adds `OpenRF1_HCSR04_Bringup.uvprojx`, source under `firmware/openrf1/hcsr04_bringup/`, host-side tests for CN6 pin order, PA5 TRIG, PA4 ECHO, TIM6, bounded echo state machine behavior, 100 ms scheduling, 30000 us timeouts, timer-wrap subtraction, nominal integer distance conversion, JSONL identity/success/error records, and target isolation. OpenRF1 vendor material locks CN6 pin 1: VCC_5V, pin 2: GND, pin 3: PA5_TRIG, pin 4: PA4_ECHO; direct ECHO to CN6 pin 4 is prohibited and the external 10 kOhm / 15 kOhm divider is required. Repository automation does not flash hardware or access real GPIO/timer/COM ports. Physical wiring, resistor installation, trigger pulse, echo pulse, real distance data, timeout behavior, timer accuracy, temperature compensation, and absolute distance accuracy remain UNVERIFIED.

Phase 3.2F isolates ground-sensor bring-up from the earlier OpenRF1 targets. It adds `OpenRF1_GroundSensors_Bringup.uvprojx`, source under `firmware/openrf1/ground_sensors_bringup/`, host-side logic tests, evidence validators, and strict numeric JSONL telemetry. OpenRF1 vendor material locks the six-pin connector order and floating-input mode as AUTHORITATIVE_VENDOR_DOCUMENTED. The design powers both TCRT5000 modules from 3.3 V, powers the Hall module from 5 V, and requires Hall S -> 10 kOhm / 15 kOhm divider -> protected PB0; direct Hall S -> PB0 is prohibited. A's isolated evidence is MANUAL_EVIDENCE_VERIFIED for the build/flash, installed PC4/PC5 signal connections, labelled 3.3 V/common-GND connections, live raw/debounced response from both TCRT modules, four 100-frame captures without sequence gaps, and exact 50 ms steady-state timestamps. Repository automation validates the sanitized captures offline and does not access hardware. Actual rail/output voltages, topology, polarity semantics, black/white/drop classification, Hall behavior, long-duration operation, full multisensor operation, and full-rover operation remain UNVERIFIED.

Phase 3.2B does not implement ESP32 WiFi firmware, motor/encoder control, mecanum kinematics, sensor fusion, mapping, SLAM, navigation, obstacle avoidance, or autonomous motion.

## Course Validation Evidence

Evidence should include software test logs, deterministic JSONL recordings, replay output, rendered figures, future bench hardware logs, future stationary physical tests, future moving-rover tests, safety test outcomes, and final presentation artifacts. Physical validations must not be marked complete until they are actually performed.
