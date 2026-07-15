# Phase 1 Interface Inventory

Date: 2026-07-14.

This inventory records the interfaces present after Phase 0 and audited in current Phase 1. It does not define new live LiDAR communication behavior.

## Firmware Configuration Interfaces

- `firmware/include/hardware_profile.h`
  - Defines `kLidarBaudRate = 460800`.
  - Defines `kLidarSerialConfig = SERIAL_8N1`.
  - Requires `RPLIDAR_C1_LIDAR_RX_PIN` and `RPLIDAR_C1_LIDAR_TX_PIN` at compile time.
  - Keeps `kHasExternalMotorPwm = false`.

- `firmware/include/app_config.h`
  - Defines range and scan-size configuration constants.

- `firmware/include/error_codes.h`
  - Defines explicit LiDAR error categories.

- `firmware/include/data_types.h`
  - Defines device, health, raw sample, processed sample, scan, and statistics data structures.

## Firmware Runtime Interfaces

- `firmware/src/lidar/lidar_interface.h`
  - Class: `LidarInterface`.
  - Defines the future generic LiDAR driver contract.
  - Includes begin/end/reset, device info, health, scan start/stop, polling, sample reads, completed-scan reads, connection state, recovery, and statistics.

- `firmware/src/app/system_state.h`
  - Defines the planned ESP32 subsystem state machine states.

- `firmware/src/processing/coordinate_transform.h`
  - Defines pure native-clockwise to rover-angle conversion helpers.

- `firmware/src/transport/crc16.h`
  - Defines a CRC16-CCITT helper for later PC transport work.

## PC Interfaces

- `pc/src/rplidar_c1_tools/data_models.py`
  - Defines `LidarDeviceInfo`, `LidarHealth`, `RawLidarSample`, `LidarSample`, `LidarScan`, `LidarStatistics`, and `ScanSource`.

- `pc/src/rplidar_c1_tools/coordinate_transform.py`
  - Defines pure coordinate conversion helpers.

- `pc/src/rplidar_c1_tools/synthetic_scan.py`
  - Defines `SyntheticRoomConfig` and `SyntheticScanSource`.
  - Does not open serial ports.

- `pc/src/rplidar_c1_tools/cli.py`
  - Provides the `rplidar-c1 synthetic-room` command.

## PC-Direct Interfaces

- `pc_direct/scripts/list_serial_ports.py`
  - Lists host serial ports for future hardware verification.

- `pc_direct/scripts/save_device_info.py`
  - Placeholder entry point for future device-information capture.

- `pc_direct/official_sdk_probe/`
  - Placeholder CMake application area for future official SDK probing.

## Validation Interfaces

- `tools/validate_hardware_lock.py`
  - Standard-library validator for hardware facts, unresolved values, and documentation consistency.

- `pc/tests/test_hardware_lock_validation.py`
  - Focused pytest coverage for the validator.

## Out Of Scope For Current Phase 1

- Live LiDAR serial communication.
- Final C1 binary protocol parser.
- ESP32 UART receive loop.
- ESP32-to-PC binary transport implementation.
- Visualization beyond existing synthetic data scaffolding.

## Phase 2.1 Interface Update

- `pc/src/rplidar_c1_tools/data_models.py`
  - Adds `ScanPoint` and `ScanFrame`.
  - Uses rover-frame degrees for `ScanPoint.angle_deg`: 0 degrees forward, positive counterclockwise.
  - Uses millimeters for `ScanPoint.distance_mm`.

- `pc/src/rplidar_c1_tools/scan_builder.py`
  - Validates scan points and builds `ScanFrame` objects.
  - Does not parse hardware packets.

- `pc/src/rplidar_c1_tools/synthetic_scan.py`
  - Produces deterministic `ScanFrame` data for circle and room environments.

## Phase 2.4 Interface Update

- `pc/src/rplidar_c1_tools/recording_models.py`
  - Defines the versioned multi-sensor recording schema constants, sensor inventory models, rover pose, IMU, ultrasonic, ground/edge, Hall, illuminance, and barometer sample models.

- `pc/src/rplidar_c1_tools/recorder.py`
  - Implements streaming UTF-8 JSONL recording for existing `ScanFrame` objects and auxiliary synthetic sensor records.
  - Does not open serial ports, use WiFi sockets, or access hardware.

- `pc/src/rplidar_c1_tools/replay.py`
  - Implements lazy JSONL reading, line-number corruption errors, deterministic LiDAR scan replay, and recording inspection.

- `pc/src/rplidar_c1_tools/cli.py`
  - Adds `record-synthetic`, `inspect-recording`, `replay-recording`, and `render-recording`.

- `tools/validate_current_plan.py`
  - Validates selected explicit current-plan anchors in authoritative documentation.

## Phase 2.5 Interface Update

- `pc/src/rplidar_c1_tools/c1_pc_direct.py`
  - Adds the transport-injected `C1PcDirectDriver` boundary with `connect()`, `disconnect()`, `start_scan()`, `iter_scan_points()`, and bounded frame capture.
  - Adds `C1StandardScanParser` for standard 5-byte C1 scan-node fixtures and future PC-direct byte streams.
  - Adds `BytesBufferTransport` for tests and verifier smoke workflows without serial access.
  - Adds `PySerialByteTransport` for manual PC-direct capture using an explicit user-provided port.

- `pc/src/rplidar_c1_tools/cli.py`
  - Adds `capture-c1` for saving one PC-direct C1 stream into the existing Phase 2.4 JSONL recording format.

- `tools/verification/phase_manifest.json`
  - Adds `phase2.5` targeted tests, regression tests, full PC suite execution, and fixture-only capture/replay/render smoke workflows.

## Phase 3.1 Interface Update

- `pc/src/rplidar_c1_tools/stm32_sensor_models.py`
  - Defines `Stm32TelemetryMessage`, protocol constants, statuses, message types, and neutral sensor IDs.

- `pc/src/rplidar_c1_tools/stm32_sensor_protocol.py`
  - Encodes and strictly parses newline-delimited UTF-8 JSON telemetry lines.
  - Enforces stream sequence and timestamp ordering with line-numbered errors.

- `pc/src/rplidar_c1_tools/stm32_sensor_simulator.py`
  - Generates deterministic STM32 low-rate sensor telemetry sessions without hardware access.

- `pc/src/rplidar_c1_tools/stm32_recording_bridge.py`
  - Converts validated STM32 telemetry into existing Phase 2.4 recording records.

- `pc/src/rplidar_c1_tools/cli.py`
  - Adds `simulate-stm32-sensors`, `inspect-stm32-telemetry`, and `record-stm32-telemetry`.

- `tools/verification/phase_manifest.json`
  - Adds `phase3.1` targeted tests, regressions, complete PC suite execution, and telemetry generation/inspection/conversion smoke workflows.
