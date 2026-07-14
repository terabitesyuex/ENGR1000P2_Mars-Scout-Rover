# Test Plan

## Phase 0 Tests

Phase 0 has no hardware dependency.

Run:

```powershell
cd rplidar_c1_subsystem
pip install -e .\\pc
pytest .\\pc\\tests
```

Expected result:

- coordinate conversion tests pass;
- synthetic scan source tests pass;
- no serial port is opened;
- no live LiDAR communication occurs.

## Phase 0 Acceptance

- Repository skeleton exists.
- `HARDWARE_LOCK.md` contains C1M1-R2.
- Verified electrical values are documented.
- GPIO values remain explicit user-configurable settings.

## Later Test Categories

- PC-direct USB adapter verification.
- Embedded command encoder tests.
- Embedded response descriptor parser tests.
- Embedded scan parser tests.
- Scan assembler tests.
- ESP32-to-PC packet encoder and CRC tests.
- PC packet decoder tests.
- Recording and interrupted recording tests.
- Deterministic replay tests.
- Synthetic room tests.
- Static occupancy-grid ray tracing tests.
- Power interruption and recovery tests.

## Unresolved Hardware Values

- ESP32 RX pin.
- ESP32 TX pin.
- Power-supply model.
- Device firmware version.
- Device hardware revision.
- Redacted serial identifier.
- PC-direct verification date.
