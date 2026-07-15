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

- Phase 2.5 tests `c1_1` and `c1_2` independently by PC-direct methods.
- Phase 5 first targets one stable C1 + STM32 + ESP32 WiFi.
- Simultaneous dual-C1 operation is optional and remains UNVERIFIED until UART, GPIO, bandwidth, buffering, timing, and power feasibility are measured.
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

The firmware foundation is configured for OpenRF1 STM32F103RCT6 software I2C on PB1/SCL and PC3/SDA, GY-302/BH1750 address `0x23`, and USART1 PA9/PA10 at 115200 baud 8N1. The PC `capture-stm32-serial` workflow accepts either a user-selected COM port for manual tests or `--mock-input` for automated verification. Automated tests and verifier smoke runs never open a real COM port.

Invalid BH1750 communication must not be represented as zero lux. A valid dark reading may be `0.0` lux only when the sensor transaction is valid.

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
- Measure bandwidth before dual-C1 operation is considered.

## Safety Expectations

The STM32 local safety path must not depend on a healthy PC connection. Timeout stop and local sensor safety remain planned STM32 responsibilities. Final exact LiDAR-derived avoidance ownership is not yet locked.

## Deferred Values

The following remain UNVERIFIED:

- Exact ESP32 GPIOs.
- Exact UART assignment.
- Exact STM32 GPIO, timer, UART, and I2C peripheral assignments outside the Phase 3.2A BH1750 OpenRF1 path.
- BH1750 ACK at 7-bit address `0x23`.
- Successful OpenRF1 CH340 COM-port path.
- Exact STM32-ESP32 connector.
- Exact packet field widths.
- Exact checksum polynomial.
- Exact bandwidth budget.
- Exact reconnection timing.
- Simultaneous dual-C1 transport feasibility.
