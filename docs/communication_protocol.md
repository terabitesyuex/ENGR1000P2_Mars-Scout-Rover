# Communication Protocol Planning

This document describes the planned future communication architecture. Phase 2.5 does not implement the future wire protocol.

The Phase 2.4 JSONL recording format is not the future on-wire protocol. The Phase 2.5 PC-direct C1 path is a bench-test and recording path, not the ESP32-to-PC WiFi protocol.

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
- No final ESP32 GPIO or UART assignment is locked in Phase 2.5.

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
- Exact STM32-ESP32 connector.
- Exact packet field widths.
- Exact checksum polynomial.
- Exact bandwidth budget.
- Exact reconnection timing.
- Simultaneous dual-C1 transport feasibility.
