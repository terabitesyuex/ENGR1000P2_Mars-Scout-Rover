# Phase 3.2B Protocol Contracts

Phase 3.2B preserves `mars_scout_stm32_sensor_telemetry` version `1` and adds message types needed for the full-hardware software foundation. It also defines a separate STM32-to-ESP32 binary frame contract for USART3.

## STM32 JSON Telemetry Additions

Existing message types remain unchanged:

- `ultrasonic`
- `ground_edge`
- `hall_landmark`
- `illuminance`
- `barometer`

New message types:

### `imu_raw`

Sensor ID: `mpu6050_1`.

Payload fields:

- `accel_x_raw`, `accel_y_raw`, `accel_z_raw`: signed raw accelerometer counts.
- `gyro_x_raw`, `gyro_y_raw`, `gyro_z_raw`: signed raw gyroscope counts.
- `temperature_raw`: signed raw temperature count.
- `accel_range_g`: one of `2`, `4`, `8`, or `16`.
- `gyro_range_dps`: one of `250`, `500`, `1000`, or `2000`.
- `calibration_state`: string. Phase 3.2B uses `uncalibrated`; no calibration result is fabricated.

### `subsystem_status`

Sensor ID: `stm32_subsystem`.

Payload fields:

- `subsystem`: non-empty string.
- `health`: non-empty string such as `ok`, `degraded`, `fault`, `disabled`, `timeout`, or `nack`.
- `error_count`: non-negative integer.
- optional `detail`: string or null.

### `link_status`

Sensor ID: `esp32_link`.

Payload fields:

- `link_name`: non-empty string.
- `healthy`: boolean.
- `rx_bytes`, `tx_bytes`, `malformed_frames`, `crc_errors`, `sequence_gaps`: non-negative integers.
- `last_rx_ms`: non-negative integer or null.

### `lidar_transport_stats`

Sensor ID: `c1_1` or `c1_2`.

Payload fields:

- `rx_bytes`
- `bytes_read`
- `overflow_count`
- `framing_error_count`
- `chunks_forwarded`
- `last_rx_tick_ms`

All fields are non-negative integers. These are byte-transport diagnostics, not proof of a successful physical C1 connection.

## STM32-To-ESP32 Binary Frame

Purpose: a compact USART3 frame for heartbeat, acknowledgements, status, and binary lidar chunks. This is not an ESP32 WiFi protocol and does not implement a WiFi application.

Byte order: little-endian for multibyte integer fields.

Maximum payload: 256 bytes.

CRC: CRC-16/CCITT-FALSE over bytes from `version` through the payload, polynomial `0x1021`, initial value `0xFFFF`, no reflection, no final XOR. The CRC itself is little-endian.

Frame layout:

| Offset | Size | Field |
| ---: | ---: | --- |
| 0 | 1 | magic byte `0xA5` |
| 1 | 1 | magic byte `0x5A` |
| 2 | 1 | version, currently `1` |
| 3 | 1 | message type |
| 4 | 1 | flags |
| 5 | 1 | reserved, must be `0` |
| 6 | 2 | sequence |
| 8 | 4 | timestamp_ms |
| 12 | 2 | payload_length |
| 14 | N | payload |
| 14 + N | 2 | CRC-16/CCITT-FALSE |

Message types:

| Value | Name |
| ---: | --- |
| 1 | `HEARTBEAT` |
| 2 | `COMMAND_ACK` |
| 3 | `SUBSYSTEM_STATUS` |
| 4 | `LINK_STATUS` |
| 5 | `LIDAR_CHUNK` |

Golden vector:

```text
frame:
  message_type: HEARTBEAT (1)
  flags: 0
  sequence: 0x1234
  timestamp_ms: 0x01020304
  payload: "OK"
encoded_hex:
  a55a0101000034120403020102004f4b94fd
```

Decoder resynchronization:

- Scan for magic bytes.
- Drop noise before magic and count dropped bytes.
- Reject payload lengths above 256 and resume from the next byte.
- Reject CRC mismatches and resume from the next byte.
- Reject unsupported versions.
- Count sequence gaps, including wraparound from `0xFFFF` to `0x0000`.

Malformed frames must not block the stream permanently.
