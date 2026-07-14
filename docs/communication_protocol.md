# Communication Protocol

This document describes the planned ESP32-to-PC transport. It is not the SLAMTEC C1 LiDAR protocol.

## Planned Frame Layout

```text
sync byte 1
sync byte 2
protocol version
message type
flags
sequence number
timestamp_us
payload length
payload
CRC16-CCITT
```

## Planned Message Types

- `HELLO`
- `DEVICE_INFO`
- `HEALTH`
- `LIDAR_POINT_BATCH`
- `LIDAR_SCAN_END`
- `LIDAR_STATISTICS`
- `OBSTACLE_SECTORS`
- `SYSTEM_STATUS`
- `ERROR_EVENT`
- `COMMAND_ACK`

## Rules

- Batch multiple LiDAR samples into one packet.
- Use byte order, field widths, signedness, units, and valid ranges documented before implementation.
- Do not use one CSV line per point for normal high-rate operation.
- Do not mix debug text with binary frames.
- Use diagnostic packets or a separate debug output for logs.

Final field values are deferred until Phase 5.
