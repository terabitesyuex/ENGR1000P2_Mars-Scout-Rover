# Test Plan

This plan distinguishes automated software checks from future physical validation. A software test passing does not prove wiring, mounting, calibration, WiFi operation, or rover safety.

## Automated Phase Verification

Supported phases:

- `phase1`
- `phase2.1`
- `phase2.2`
- `phase2.3`
- `phase2.4`
- `phase2.5`
- `phase3.1`

Development verification:

```powershell
.\tools\verify_phase.cmd phase2.5 -AllowDirty
.\tools\verify_phase.cmd phase3.1 -AllowDirty
```

Normal verification after commit and push:

```powershell
.\tools\verify_phase.cmd phase2.5
.\tools\verify_phase.cmd phase3.1
```

The verifier uses repository-local pytest basetemp under `.verification/pytest_tmp/`, checks Git state, selects Python, confirms pytest import, runs targeted tests, regressions, the complete PC suite, and configured smoke workflows.

## Phase 2.4 Automated Software Tests

Targeted:

- `pc/tests/test_recording.py`
- `pc/tests/test_replay.py`
- `pc/tests/test_current_plan.py`

Regression:

- `pc/tests/test_visualization.py`
- `pc/tests/test_coordinate_transform.py`
- `pc/tests/test_synthetic_scan.py`
- `pc/tests/test_scan_builder.py`
- `pc/tests/test_hardware_lock_validation.py`

Smoke workflow:

- Generate deterministic two-LiDAR room session with auxiliary streams.
- Inspect the JSONL recording.
- Replay immediately.
- Render final frames for `c1_1` and `c1_2`.
- Verify artifacts under `.verification/phase2.4/`.

Phase 2.4 does not perform bench hardware tests, stationary physical tests, moving-rover tests, or real safety tests.

## Phase 2.5 Automated Software Tests

Targeted:

- `pc/tests/test_c1_pc_direct.py`
- `pc/tests/test_recording.py`
- `pc/tests/test_replay.py`

Regression:

- `pc/tests/test_visualization.py`
- `pc/tests/test_coordinate_transform.py`
- `pc/tests/test_synthetic_scan.py`
- `pc/tests/test_scan_builder.py`
- `pc/tests/test_hardware_lock_validation.py`
- `pc/tests/test_current_plan.py`

Smoke workflow:

- Capture `c1_1` from fixture standard scan bytes.
- Capture `c1_2` from fixture standard scan bytes independently.
- Inspect and replay captured JSONL.
- Render final replayed frame images.
- Verify artifacts under `.verification/phase2.5/`.

Phase 2.5 automated tests do not open serial ports. Manual PC-direct hardware tests remain required before physical C1 operation can be marked verified.

## Phase 3.1 Automated Software Tests

Targeted:

- `pc/tests/test_stm32_sensor_models.py`
- `pc/tests/test_stm32_sensor_protocol.py`
- `pc/tests/test_stm32_sensor_simulator.py`
- `pc/tests/test_stm32_recording_bridge.py`
- `pc/tests/test_stm32_sensor_cli.py`
- `pc/tests/test_phase3_current_plan.py`

Regression:

- Phase 2.4 recording and replay tests.
- Phase 2.5 C1 PC-direct tests.
- Visualization tests.
- Coordinate-transform tests.
- Hardware-lock validation.
- Current-plan validation.

Smoke workflow:

- Generate deterministic STM32 telemetry under `.verification/phase3.1/`.
- Inspect generated telemetry.
- Convert telemetry into the Phase 2.4 JSONL recording format.
- Inspect the converted recording.

Phase 3.1 automated tests do not open serial ports, GPIO, I2C, timers, USB devices, network sockets, or real sensors.

## Revised Phase Sequence

Phase 2.4:

- Automated software tests: JSONL schema, recorder, lazy reader, deterministic replay, CLI, visualization from replay, current-plan validator.
- Bench hardware tests: not performed.
- Stationary physical tests: not performed.
- Moving-rover tests: not performed.
- Safety tests: software scope only.
- Presentation evidence: deterministic recordings, inspection output, replay output, rendered PNGs, verifier logs.

Phase 2.5:

- Automated software tests: PC-direct driver boundary, standard scan-node parser fixtures, mocked timeout/error handling, captured JSONL replay, visualization regression.
- Bench hardware tests: test both `c1_1` and `c1_2` independently with the supplied adapter.
- Stationary physical tests: distance/orientation checks against known walls and targets.
- Moving-rover tests: not required.
- Safety tests: power, polarity, common ground, cable strain, serial-port release.
- Presentation evidence: device info, health, scan samples, distance error tables, orientation images.

Phase 3.1:

- Automated software tests: STM32 telemetry protocol, parser, simulator, recording bridge, CLI, and current-plan anchors.
- Bench hardware tests: not performed.
- Stationary physical tests: not performed.
- Moving-rover tests: not performed.
- Safety tests: documentation/checklist only.
- Presentation evidence: deterministic telemetry files, converted recordings, inspection output, verifier logs.

Phase 3.2:

- Automated software tests: STM32 sensor parsing/validation where available.
- Bench hardware tests: HC-SR04, TCRT5000, Hall, BH1750, BMP280 individually.
- Stationary physical tests: sensor threshold and environmental response checks.
- Moving-rover tests: limited low-speed sensor-state checks only after safety approval.
- Safety tests: edge/drop response, ultrasonic timeout behavior, local stop path.
- Presentation evidence: sensor logs, threshold tables, environmental-change demonstrations.

Phase 4:

- Automated software tests: kinematics, encoder math, IMU parsing, odometry update logic.
- Bench hardware tests: encoder counts, MPU6050 readings, mecanum geometry.
- Stationary physical tests: wheel direction and low-speed movement on blocks.
- Moving-rover tests: straight, lateral, yaw, repeatability runs.
- Safety tests: timeout stop and bounded command behavior.
- Presentation evidence: trajectory and error plots.

Phase 5:

- Automated software tests: STM32-ESP32-PC framing, sequence, checksum, timeout handling.
- Bench hardware tests: WiFi packet flow and one-C1 baseline integration.
- Stationary physical tests: one stable C1 through ESP32 and PC display.
- Moving-rover tests: limited after local stop behavior is ready.
- Safety tests: packet-loss timeout stop and reconnection.
- Presentation evidence: latency, loss, reconnection, and runtime logs.

Phase 6:

- Automated software tests: real-time visualization, trajectory display, accumulated-map data structures.
- Bench hardware tests: PC display rate and export.
- Stationary physical tests: known-dimension environment checks.
- Moving-rover tests: short-range accumulated mapping runs.
- Safety tests: operator stop and communication-loss behavior.
- Presentation evidence: maps, trajectory plots, distortion/drift metrics.

Phase 7:

- Automated software tests: local obstacle stop/turn state machine.
- Bench hardware tests: obstacle sensor thresholds.
- Stationary physical tests: controlled obstacle response.
- Moving-rover tests: low-speed avoidance course.
- Safety tests: stopping distance and fail-safe behavior.
- Presentation evidence: obstacle-avoidance success rate and video/log evidence.

Phase 8:

- Automated software tests: final regression suite.
- Bench hardware tests: integrated sensor/system health.
- Stationary physical tests: full venue checks.
- Moving-rover tests: Mars-like venue demonstrations.
- Safety tests: continuous runtime and failure modes.
- Presentation evidence: final logs, recordings, figures, and demonstration results.

## Planned Validation Metrics

RPLIDAR:

- Distance error for `c1_1`.
- Distance error for `c1_2`.
- Orientation correctness.
- Scan rate.
- Dropped/corrupt scan rate.
- Continuous runtime.

Ultrasonic:

- Distance error.
- Timeout behavior.
- Cross-talk rate.
- Stop-distance contribution.

TCRT5000:

- Edge/drop detection success rate.
- False positives.
- Installation-height sensitivity.

Hall:

- Checkpoint detection success rate.
- False positives.
- Repeatability.

BH1750:

- Illuminance repeatability.
- Response to controlled light changes.

BMP280:

- Temperature stability.
- Pressure stability.
- Response to controlled environmental changes where practical.

MPU6050 and encoders:

- Straight-distance error.
- Lateral-distance error.
- Yaw error.
- Repeatability.

Communication:

- WiFi packet loss.
- Latency.
- Reconnection.
- Timeout stop.

Mapping:

- Known-dimension error.
- Point-cloud distortion.
- Trajectory drift.

System:

- Obstacle-avoidance success rate.
- Stopping distance.
- Continuous runtime.
- Failure-mode behavior.

## Current Plan Consistency Validator

`tools/validate_current_plan.py` checks explicit text anchors in authoritative current-plan files. It verifies selected facts such as two C1 units, BH1750/BMP280 presence, STM32/ESP32/PC roles, WiFi baseline, ROS/Linux non-goal status, dual-C1 optional status, and the revised phase order.

Limit: the validator checks literal text snippets only; it is not semantic AI analysis and does not validate historical documents unless they are treated as current-plan authorities.
