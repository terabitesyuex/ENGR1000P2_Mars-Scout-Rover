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
