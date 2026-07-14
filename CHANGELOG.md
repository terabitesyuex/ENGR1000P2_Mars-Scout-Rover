# Changelog

All notable subsystem changes are recorded here. Track protocol, GPIO, power, data-format, firmware, and calibration changes explicitly.

## 2026-07-14 - Phase 0 Skeleton

- Created repository skeleton for RPLIDAR C1 subsystem.
- Documented confirmed C1M1-R2 electrical and wiring constraints.
- Recorded unresolved GPIO and physical verification values.
- Added PC-side synthetic scan interface and coordinate conversion scaffolding.
- Did not implement live LiDAR communication.
- Did not implement the final C1 binary protocol parser.

## 2026-07-14 - Phase 1 Audit And Validation

- Aligned Phase 1 documentation with the current audit-only scope.
- Added `docs/phase1_hardware_audit.md` to record source-of-truth decisions, unverified values, and documentation conflicts.
- Added `docs/phase1_interface_inventory.md` to inventory current firmware and PC interfaces.
- Added standard-library hardware-lock validation tooling.
- Added focused pytest coverage for the hardware-lock validator.
- Kept ESP32 GPIO values unset pending physical verification.
- Kept live LiDAR communication out of scope.

## Change Categories

- Protocol changes: none in Phase 0 or current Phase 1.
- GPIO changes: GPIO values remain unset.
- Power changes: hardware values documented; supply model unverified.
- Data-format changes: recording and transport formats documented as planned interfaces.
- Firmware changes: PlatformIO structure created only; current Phase 1 adds no live hardware behavior.
- Calibration changes: calibration process documented only.
