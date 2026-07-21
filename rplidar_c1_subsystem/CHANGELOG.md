# SUPERSEDED HISTORICAL COPY

Use repository-root `CHANGELOG.md` for current changes. Historical entries below may be stale.

# Changelog

## Current Status Notice - 2026-07-21

This nested changelog is historical. The current repository has exactly one physical RPLIDAR C1M1-R2 (`c1_1`) and isolated TCRT5000 evidence is maintained at repository root. Do not use this mirror to claim dual-C1, Hall, full-rover, or WiFi validation.

All notable subsystem changes are recorded here. Track protocol, GPIO, power, data-format, firmware, and calibration changes explicitly.

## 2026-07-14 - Phase 0 Skeleton

- Created repository skeleton for RPLIDAR C1 subsystem.
- Documented confirmed C1M1-R2 electrical and wiring constraints.
- Recorded unresolved GPIO and physical verification values.
- Added PC-side synthetic scan interface and coordinate conversion scaffolding.
- Did not implement live LiDAR communication.
- Did not implement the final C1 binary protocol parser.

## Change Categories

- Protocol changes: none in Phase 0.
- GPIO changes: GPIO values remain unset.
- Power changes: hardware values documented; supply model unverified.
- Data-format changes: recording and transport formats documented as planned interfaces.
- Firmware changes: PlatformIO structure created only.
- Calibration changes: calibration process documented only.
