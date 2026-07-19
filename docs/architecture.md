# Architecture

The rover architecture separates hardware access, transport, data models, algorithms, visualization, recording, and replay. Phase 3.2F adds an isolated OpenRF1 ground-sensor-only software bring-up target while preserving the Phase 3.2A BH1750-only path, Phase 3.2C BMP280-only path, Phase 3.2D MPU6050-only path, Phase 3.2E HC-SR04-only path, Phase 3.2B full-hardware foundation, and the Phase 2.4 recording/replay pipeline.

## Sensor Layer

Ranging:

- RPLIDAR C1 x2, neutral IDs `c1_1` and `c1_2`.
- HC-SR04 x3, neutral IDs `ultrasonic_1`, `ultrasonic_2`, `ultrasonic_3`.

Motion and pose:

- Four wheel encoders.
- MPU6050 x1.

Ground and landmark:

- TCRT5000 x2 for edge/drop detection.
- Hall sensor module x1 for magnetic landmark/checkpoint detection.

Environment:

- BH1750 x1 for illuminance in lux.
- BMP280 x1 for temperature and atmospheric pressure.

## Planned Data Paths

```text
RPLIDAR C1
    -> ESP32 -> WiFi -> PC visualization/recording

STM32 sensors and rover state
    -> ESP32 -> WiFi -> PC

HC-SR04 / TCRT5000 / relevant local state
    -> STM32 safety decision -> motor control -> rover motion

rover motion
    -> encoders / MPU6050 / sensors -> STM32 -> ESP32 -> PC
```

The ESP32 -> WiFi -> PC path is the current communication plan. Bluetooth is only a superseded early concept if it appears in historical material.

## Responsibility Split

STM32 planned responsibilities:

- Existing four-mecanum-wheel motor control.
- Wheel encoder acquisition.
- Low-level motor safety.
- Command-timeout stop.
- MPU6050 acquisition.
- HC-SR04 acquisition.
- TCRT5000 edge/drop detection.
- Hall landmark detection.
- BH1750 and BMP280 acquisition unless interface tests require a different assignment.
- Low-rate sensor preprocessing.
- Basic odometry support.
- Local stop/turn obstacle-avoidance state machine.

ESP32 planned responsibilities:

- WiFi communication with the PC.
- Receive STM32 rover and sensor information.
- Package and transmit data.
- Receive limited configuration/control messages.
- Interface with at least one RPLIDAR C1 in a later phase.

PC responsibilities:

- Real-time polar visualization.
- Real-time Cartesian visualization.
- Recording.
- Replay.
- Experiment inspection.
- Data and figure export.
- Later short-range encoder/IMU-assisted accumulated 2D mapping.

## Current Software Layers

```text
Synthetic LiDAR source
PC-direct C1 byte stream with explicit user-provided port or fixture bytes
STM32 low-rate sensor telemetry simulator / future forwarded telemetry
OpenRF1 BH1750 mocked serial capture / future user-selected CH340 COM port
OpenRF1 Phase 3.2B full-hardware fixtures and STM32-to-ESP32 frame codec
OpenRF1 Phase 3.2C BMP280 evidence validator
OpenRF1 Phase 3.2D MPU6050 bring-up software tests
OpenRF1 Phase 3.2E HC-SR04 bring-up software tests
OpenRF1 Phase 3.2F ground-sensor bring-up software tests
Phase 4A pure mecanum kinematics / encoder conversion / SE(2) odometry simulator
    -> ScanFrame data model
    -> STM32 telemetry parser / recording bridge
    -> scan builder / coordinate transforms
    -> visualization
    -> Phase 2.4 JSONL recorder
    -> lazy replay
    -> replay visualization
```

The Phase 2.4 JSONL recording format is a PC-side reproducibility format. Phase 2.5 writes PC-direct C1 captures into that same format. Phase 3.1 writes validated STM32 low-rate sensor telemetry into that same format. Phase 3.2A writes mocked or manually captured BH1750 serial telemetry into that same format. Phase 3.2B writes deterministic raw-IMU and transport-status fixture records into that same format. JSONL recordings are not the future on-wire ESP32 protocol.

Phase 4A adds pure host-side kinematics and odometry records to the same version-1 telemetry and recording containers. It has no hardware adapter and does not read encoders, motors, serial ports, GPIO, timers, or MPU6050 data. Explicit configuration separates later hardware acquisition from the mathematical layer.

## Two-C1 Policy

- Two C1 units are available.
- Phase 2.5 must test both independently.
- One stable C1 is the baseline integration target.
- Simultaneous dual-C1 operation is optional and remains UNVERIFIED until UART, GPIO, bandwidth, buffering, timing, and power feasibility are measured.
- Final exact LiDAR-derived avoidance ownership is not yet locked.

## Current Phase Scope

Phase 3.1 implements `mars_scout_stm32_sensor_telemetry` v1, deterministic STM32 sensor telemetry simulation, strict PC parsing, and a bridge into the existing recording format. Automated tests use fixture files and in-memory streams only.

Phase 3.1 does not implement real STM32 sensor acquisition, serial ports, GPIO, I2C, timers, ESP32 communication, WiFi sockets, firmware behavior, mapping, SLAM, odometry, navigation, obstacle avoidance, or simultaneous dual-C1 operation.

Phase 3.2A implements application-layer firmware source for one GY-302/BH1750 sensor on OpenRF1 software I2C PB1/PC3, plus a mockable PC serial-capture layer for versioned `illuminance` telemetry from `bh1750_1`. Automated tests use pure logic and file-backed mock readers only.

Phase 3.2A remains the BH1750-only firmware path. Recorded manual evidence verifies firmware flash, CH340/USART1 telemetry, BH1750 communication at configured address `0x23`, a 500 ms telemetry period, and physical light response. Absolute lux calibration remains UNVERIFIED.

Phase 3.2B implements an isolated full-hardware firmware foundation under `firmware/openrf1/full_hardware/`, a separate Keil project/output, raw sensor/status telemetry contracts, deterministic PC fixtures, and the STM32-side binary frame contract for the future ESP32 link. It does not implement ESP32 WiFi firmware, motor/encoder control, physical multisensor validation, mapping, SLAM, navigation, obstacle avoidance, or autonomous motion. USART2/USART3 pins, PWM pins, line-input pins, BMP280/MPU6050 ACKs, HC-SR04 Echo VOH, Hall output voltage, sensor polarity, RPLIDAR operation, ESP32 operation, power integrity, concurrent operation, and real full-system sensor data remain UNVERIFIED.

Phase 3.2E implements an isolated OpenRF1 HC-SR04 software foundation under `firmware/openrf1/hcsr04_bringup/`. CN6 pin order, PA5 TRIG, PA4 ECHO, TIM6, and the external 10 kOhm / 15 kOhm ECHO divider requirement are AUTHORITATIVE_VENDOR_DOCUMENTED. Physical wiring, installed resistor values, trigger pulse, echo pulse, real distance data, timeout behavior, timer accuracy, and distance accuracy remain UNVERIFIED.

Phase 3.2C implements an isolated BMP280-only OpenRF1 bring-up firmware target under `firmware/openrf1/bmp280_bringup/` and `OpenRF1_BMP280_Bringup.uvprojx`. It reuses the software-I2C and BMP280 driver boundary, emits USART1 JSONL, keeps BH1750 and FullHardware targets separate, and validates the committed BMP280 physical evidence offline. Absolute temperature/pressure accuracy, long-duration operation, shared-I2C concurrency, and full-hardware operation remain UNVERIFIED.

Phase 3.2D implements an isolated MPU6050-only OpenRF1 software bring-up target under `firmware/openrf1/mpu6050_bringup/` and `OpenRF1_MPU6050_Bringup.uvprojx`. It reuses the software-I2C and MPU6050 driver boundary, emits USART1 JSONL for future manual capture, and keeps BH1750, BMP280, and FullHardware targets separate. Physical MPU6050 ACK, WHO_AM_I, configuration readback, live IMU telemetry, calibration, axis orientation, shared-I2C concurrency, and full-hardware operation remain UNVERIFIED.

Phase 3.2F implements an isolated ground-sensor-only OpenRF1 software bring-up target under `firmware/openrf1/ground_sensors_bringup/` and `OpenRF1_GroundSensors_Bringup.uvprojx`. It samples PC4, PC5, and PB0 as floating inputs every 5 ms, applies independent 4-sample debounce, and emits 50 ms JSONL raw/debounced numeric levels only. Signal 1 / X1 / PC4, signal 2 / X2 / PC5, signal 3 / X3 / PB0, and the tracking connector pin order are AUTHORITATIVE_VENDOR_DOCUMENTED. The schematic says PC14 for X4 while the old example maps X4 to PB1, so signal 4 remains unused. Physical wiring, voltage levels, active polarity, surface behavior, magnetic behavior, serial periodicity, and full-hardware operation remain UNVERIFIED.

Phase 4A implements the standard X-layout mecanum equations, explicit raw-to-mathematical encoder signs, wheel-side count conversion, body-twist estimation, and exact constant-twist SE(2) integration on the host. It is a SOFTWARE_VERIFIED software-only foundation. Actual wheel geometry, resolution, gear ratio, counter width, signs, roller orientation, encoder acquisition, motor control, MPU6050 fusion, wheel slip, and physical accuracy remain UNVERIFIED.

Phase 4B layers pure control stages above Phase 4A: validated body commands, inverse kinematics, proportional wheel desaturation, per-wheel acceleration limits, explicit safety arbitration, four independent PID states, and dimensionless normalized efforts. A separate deterministic first-order synthetic plant feeds Phase 4A forward kinematics and optional pose integration. Hardware adapters remain outside these modules. Phase 4B does not import or access serial, USB, GPIO, I2C, timers, encoders, motors, or sensors.

Emergency stopping remains a local STM32 safety responsibility in the plan. PC mapping occurs later and is short-range accumulated mapping, not a required reusable global SLAM map. ROS is not required.
