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

## 2026-07-14 - Phase 2.1 Synthetic Scan Pipeline

- Added unified PC-side `ScanPoint` and `ScanFrame` data models.
- Implemented deterministic `generate_circle_scan()` and `generate_room_scan()` synthetic sources.
- Implemented `scan_builder.py` validation and frame construction helpers.
- Updated synthetic scan and scan-builder tests.
- Kept real LiDAR UART communication, serial access, mapping, SLAM, and visualization out of scope.

## 2026-07-14 - Phase 2.2 Coordinate Transforms

- Added `CartesianPoint` and `Transform2D` data models.
- Updated coordinate transforms to use the rover-frame `ScanPoint.angle_deg` convention directly.
- Added explicit `native_c1_angle_to_rover_deg()` for future clockwise-positive C1 packet input.
- Added scan point, scan frame, and 2D rigid transform conversion helpers.
- Updated coordinate-frame documentation with units, frame names, and unverified mounting-offset status.
- Added coordinate transform and synthetic integration tests.
- Kept hardware communication, plotting, mapping, odometry, and SLAM out of scope.

## 2026-07-15 - Phase 2.2.5 Automated Phase Verification

- Added a CMD wrapper and PowerShell phase verifier for `phase1`, `phase2.1`, and `phase2.2`.
- Added a data-driven phase manifest for targeted, regression, and full PC test sets.
- Added Git, Python, pytest import, working-tree, upstream, and tracked-file-change checks.
- Added ignored `.verification/` log output.
- Documented one-command phase verification and development-only `-AllowDirty`.
- Did not add Phase 2.3, hardware access, plotting, mapping, or GUI functionality.

## 2026-07-15 - Phase 2.3 Synthetic LiDAR Visualization

- Implemented headless-safe synthetic polar scan visualization.
- Implemented rover-centric Cartesian point-cloud visualization with forward-up and left-left display orientation.
- Added deterministic PNG export helpers for polar and point-cloud views.
- Added `render-synthetic` CLI export for circle, room, or both scenes.
- Added visualization tests for plotting semantics, PNG export, CLI smoke coverage, and synthetic integration.
- Extended automated phase verification to support `phase2.3` and generate manual acceptance images.
- Kept real LiDAR communication, serial access, mapping, SLAM, odometry, and hardware validation out of scope.

## 2026-07-15 - Phase 2.4 Multi-Sensor Recording Replay And Plan Rebaseline

- Added versioned UTF-8 JSONL schema `mars_scout_multisensor_recording` version `1`.
- Added streaming multi-sensor recorder support for existing `ScanFrame` objects.
- Added neutral two-C1 sensor ID support for `c1_1` and `c1_2`.
- Added optional rover-pose records.
- Added IMU, HC-SR04 ultrasonic, TCRT5000 ground/edge, Hall-landmark, BH1750 illuminance, and BMP280 temperature/pressure record support.
- Added lazy recording reading, line-number corruption errors, deterministic replay, recording inspection, and replay-to-visualization export.
- Added CLI commands `record-synthetic`, `inspect-recording`, `replay-recording`, and `render-recording`.
- Added current-plan consistency validation.
- Updated hardware inventory to include RPLIDAR C1 x2, HC-SR04 x3, TCRT5000 x2, BH1750 x1, BMP280 x1, MPU6050 x1, Hall sensor module x1, STM32 x1, ESP32 x1, battery/power system, four encoded motors, and four mecanum wheels.
- Rebaselined project guidance around WiFi, one-C1 baseline integration, optional dual-C1 feasibility, environmental-change indication, and the revised Phase 2.4 through Phase 8 plan.
- Preserved verified C1 voltage, current, UART, connector, wire, and no-external-motor-PWM facts.
- Kept real hardware access, WiFi sockets, firmware changes, mapping, SLAM, odometry, ROS, and obstacle-avoidance implementation out of scope.

## Change Categories

- Protocol changes: none in Phase 0, Phase 1, Phase 2.1, Phase 2.2, Phase 2.2.5, or Phase 2.3.
- GPIO changes: GPIO values remain unset.
- Power changes: hardware values documented; supply model unverified.
- Data-format changes: Phase 2.1 adds the PC-side `ScanFrame` software interface; Phase 2.2 adds Cartesian transform models; Phase 2.3 adds PNG visualization export; Phase 2.4 adds the multi-sensor JSONL recording format.
- Firmware changes: PlatformIO structure created only; no live hardware behavior added.
- Calibration changes: calibration process documented only.
