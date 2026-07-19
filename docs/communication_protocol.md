# Communication Protocol Planning

This document describes the planned future communication architecture. Phase 3.1 does not implement the future ESP32 WiFi wire protocol.

The Phase 2.4 JSONL recording format is not the future on-wire protocol. The Phase 2.5 PC-direct C1 path is a bench-test and recording path, not the ESP32-to-PC WiFi protocol. The Phase 3.1 `mars_scout_stm32_sensor_telemetry` protocol is a versioned diagnostic/foundation format for low-rate STM32 sensor data and future forwarding; it is not a claim that ESP32 transport is implemented.

## Planned Links

STM32 to ESP32 future link:

- Rover state.
- Wheel encoder summaries.
- MPU6050 summaries.
- HC-SR04 range summaries.
- TCRT5000 edge/drop states.
- Hall landmark states.
- BH1750 illuminance readings.
- BMP280 temperature and pressure readings.
- Safety and fault state.

ESP32 to PC future WiFi link:

- RPLIDAR C1 scan data.
- STM32 rover and sensor data.
- Health and diagnostics.
- Sequence and timestamp fields.
- Configuration/status acknowledgements.
- Error and timeout events.

## C1 Integration Policy

- Phase 2.5 targets the one physical `c1_1` by PC-direct methods.
- Phase 5 targets one physical C1 + STM32 + ESP32 WiFi.
- Dual-C1 integration and feasibility evaluation are NOT CURRENT SCOPE; a future second C1 requires a new inventory and electrical, power, UART, bandwidth, buffering, timing, mounting, synchronization, and safety review.
- No final ESP32 GPIO or UART assignment is locked in Phase 3.1.
- No final STM32 GPIO, timer, UART, or I2C peripheral assignment is locked in Phase 3.1.

## Planned Message Categories

- `HELLO`
- `SYSTEM_STATUS`
- `ROVER_STATE`
- `SENSOR_SUMMARY`
- `LIDAR_POINT_BATCH`
- `LIDAR_SCAN_END`
- `LIDAR_STATISTICS`
- `OBSTACLE_SECTORS`
- `ERROR_EVENT`
- `COMMAND_ACK`
- `CONFIG_UPDATE`

## Phase 3.1 STM32 Sensor Telemetry

Phase 3.1 defines `mars_scout_stm32_sensor_telemetry` version `1` as newline-delimited UTF-8 JSON. Required fields are `protocol`, `version`, `sequence`, `timestamp_ms`, `message_type`, `sensor_id`, `payload`, and `status`.

Supported message types:

- `ultrasonic`
- `ground_edge`
- `hall_landmark`
- `illuminance`
- `barometer`

This protocol is strict, human-inspectable, and machine-parseable. It does not open serial ports. It is designed so later STM32 or ESP32 transports can forward messages without changing the PC recording schema.

## Phase 3.2A OpenRF1 BH1750 Serial Telemetry

Phase 3.2A uses the existing `mars_scout_stm32_sensor_telemetry` version `1` protocol for one real-firmware preparation path:

- `message_type`: `illuminance`
- `sensor_id`: `bh1750_1`
- payload field: `illuminance_lux`
- valid status: `ok` from firmware or `simulated` from deterministic test fixtures
- error statuses: `timeout`, `not_initialized`, `stale`, or `hardware_fault`

The firmware foundation is configured for OpenRF1 STM32F103RCT6 software I2C on PB1/SCL and PC3/SDA, GY-302/BH1750 address `0x23`, and USART1 PA9/PA10 at 115200 baud 8N1. Recorded manual evidence verifies firmware flash, CH340/USART1 telemetry, configured-address BH1750 communication, a 500 ms telemetry period, and physical light response. The PC `capture-stm32-serial` workflow accepts either a user-selected COM port for manual tests or `--mock-input` for automated verification. Automated tests and verifier smoke runs never open a real COM port.

Invalid BH1750 communication must not be represented as zero lux. A valid dark reading may be `0.0` lux only when the sensor transaction is valid.

## Phase 3.2B OpenRF1 Full-Hardware Foundation

Phase 3.2B adds software contracts only:

- USART2 is the proposed RPLIDAR C1 byte-transport link at 460800 baud 8N1, but OpenRF1 connector-to-MCU pins remain UNVERIFIED.
- USART3 is the proposed STM32-to-ESP32 link. The software configuration uses a provisional 921600 baud because 115200 is not automatically sufficient for lidar chunks. This baud is NOT PHYSICALLY VERIFIED.
- USART1 remains the CH340/debug telemetry path at 115200 baud 8N1 and must not carry high-rate lidar payload.

The STM32-to-ESP32 binary frame is documented in `docs/openrf1_phase32b_protocol.md`. It uses:

- Magic `0xA5 0x5A`.
- Version `1`.
- Little-endian sequence, timestamp, payload length, and CRC fields.
- Maximum payload length 256 bytes.
- CRC-16/CCITT-FALSE over version through payload.
- Resynchronization by scanning for the magic bytes and rejecting malformed length or CRC failures.

New JSON telemetry message types for PC inspection and recording fixtures:

- `imu_raw`
- `subsystem_status`
- `link_status`
- `lidar_transport_stats`

These contracts are SOFTWARE_VERIFIED by tests only. They do not prove ESP32 operation, RPLIDAR operation, UART electrical idle, framing integrity on real wires, or WiFi behavior.

## Phase 3.2D OpenRF1 MPU6050 Bring-Up Telemetry

Phase 3.2D adds a separate MPU6050-only USART1 bring-up JSONL stream for future manual capture:

- `message_type`: `sensor_identity` for startup identity/configuration.
- `message_type`: `imu` for raw and scaled MPU6050 samples.
- `sensor_id`: `mpu6050_1`.
- planned address: `0x68` with AD0 grounded.
- expected WHO_AM_I: `0x68`.
- sample period: 100 ms.

This bring-up stream is for isolated bench evidence and host-side tests. It does not implement sensor fusion, odometry, Phase 4 motion estimation, ESP32 forwarding, WiFi transport, or a calibrated rover-frame IMU contract. Physical ACK, WHO_AM_I, configuration readback, live telemetry, calibration, and axis orientation remain UNVERIFIED.

## Transport Expectations

- Include sequence numbers.
- Include timestamps in microseconds where practical.
- Include payload length.
- Include CRC/checksum protection.
- Detect sequence gaps.
- Detect stale data.
- Bound buffering and memory use.
- Support timeout stop behavior.
- Support reconnection reporting.
- Measure bandwidth before any future second-C1 extension is considered.

## Safety Expectations

The STM32 local safety path must not depend on a healthy PC connection. Timeout stop and local sensor safety remain planned STM32 responsibilities. Final exact LiDAR-derived avoidance ownership is not yet locked.

## Deferred Values

The following remain UNVERIFIED:

- ESP32-C3 module-side GPIO21 TX and GPIO20 RX have CONFIRMED_MODULE_EVIDENCE for the proposed link.
- Exact OpenRF1 UART connector-to-MCU assignment.
- Exact STM32 GPIO, timer, UART, and I2C peripheral assignments outside the Phase 3.2A BH1750 OpenRF1 path.
- Absolute BH1750 lux calibration.
- Exact STM32-ESP32 connector.
- Exact packet field widths.
- Exact checksum polynomial.
- Exact bandwidth budget.
- Exact reconnection timing.
- Future second-C1 transport feasibility (NOT CURRENT SCOPE).
- OpenRF1 USART2 connector-to-MCU pins.
- OpenRF1 USART3 connector-to-MCU pins.
- Physical STM32-to-ESP32 baud rate.

## Phase 4B Software-Derived Control Records

Phase 4B extends the existing version-1 telemetry vocabulary only for software-derived command, wheel-setpoint, synthetic wheel-measurement, normalized-effort, motion-safety, and complete control-snapshot records. This does not implement STM32 motor transport, ESP32 forwarding, WiFi, PWM, encoder acquisition, or any on-wire motor command. All Phase 4B outputs identify their synthetic/software origin.
