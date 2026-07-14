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

## Phase 1 Tests

Phase 1 has no hardware dependency and must not open serial ports.

Run from the subsystem root:

```powershell
cd rplidar_c1_subsystem
python tools\\validate_hardware_lock.py
python -m pytest pc\\tests\\test_hardware_lock_validation.py -v
```

Expected result:

- hardware lock validation passes;
- unresolved ESP32 GPIO settings remain explicit;
- documentation conflicts are recorded;
- interface inventory exists;
- no live LiDAR communication occurs.

## Phase 1 Acceptance

- Repository audit is documented.
- `HARDWARE_LOCK.md` clearly separates VERIFIED facts from UNVERIFIED values.
- `docs/phase1_hardware_audit.md` records conflicts and unresolved values.
- `docs/phase1_interface_inventory.md` records current interfaces.
- Validation tooling succeeds.

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
