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
- `phase3.2a`
- `phase3.2b`
- `phase3.2c`
- `phase3.2d`
- `phase3.2e`
- `phase3.2f`
- `phase4a`
- `phase4b`

Development verification:

```powershell
.\tools\verify_phase.cmd phase2.5 -AllowDirty
.\tools\verify_phase.cmd phase3.1 -AllowDirty
.\tools\verify_phase.cmd phase3.2a -AllowDirty
.\tools\verify_phase.cmd phase3.2b -AllowDirty
.\tools\verify_phase.cmd phase3.2c -AllowDirty
.\tools\verify_phase.cmd phase3.2d -AllowDirty
.\tools\verify_phase.cmd phase3.2e -AllowDirty
.\tools\verify_phase.cmd phase3.2f -AllowDirty
.\tools\verify_phase.cmd phase4a -AllowDirty
.\tools\verify_phase.cmd phase4b -AllowDirty
```

Normal verification after commit and push:

```powershell
.\tools\verify_phase.cmd phase2.5
.\tools\verify_phase.cmd phase3.1
.\tools\verify_phase.cmd phase3.2a
.\tools\verify_phase.cmd phase3.2b
.\tools\verify_phase.cmd phase3.2c
.\tools\verify_phase.cmd phase3.2d
.\tools\verify_phase.cmd phase3.2e
.\tools\verify_phase.cmd phase3.2f
.\tools\verify_phase.cmd phase4a
.\tools\verify_phase.cmd phase4b
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

- Generate the deterministic one-C1 room session with auxiliary streams.
- Inspect the JSONL recording.
- Replay immediately.
- Render the final `c1_1` frame.
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
- Keep explicit synthetic multi-LiDAR compatibility covered by recording/replay tests; it is not a physical acceptance workflow.
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

## Phase 3.2A Automated Software Tests

Targeted:

- `pc/tests/test_openrf1_bh1750.py`
- `pc/tests/test_phase32a_physical_evidence.py`
- `pc/tests/test_openrf1_firmware_foundation.py`
- `pc/tests/test_stm32_serial_capture.py`
- `pc/tests/test_stm32_sensor_protocol.py`
- `pc/tests/test_stm32_recording_bridge.py`
- `pc/tests/test_phase3_current_plan.py`

Regression:

- Phase 3.1 telemetry tests.
- Phase 2.5 C1 PC-direct tests.
- Phase 2.4 recording and replay tests.
- Visualization tests.
- Coordinate-transform tests.
- Hardware-lock validation.
- Current-plan validation.

Smoke workflow:

- Generate deterministic BH1750-only telemetry under `.verification/phase3.2a/`.
- Capture that telemetry through the mocked serial-capture path.
- Inspect the preserved telemetry.
- Inspect the converted Phase 2.4 recording.
- Generate `build_audit.txt` and `manual_hardware_status.txt`.
- Validate the committed sanitized BH1750 physical evidence JSONL.

Phase 3.2A automated tests do not open real COM ports, USB devices, GPIO, I2C, flash tools, network sockets, motors, or real sensors. They may validate committed recorded manual evidence integrity offline.

## Phase 3.2C Automated Software Tests

Targeted:

- `pc/tests/test_openrf1_bmp280_bringup.py`
- `pc/tests/test_phase32c_physical_evidence.py`

Regression:

- Phase 3.2B firmware foundation tests.
- Phase 3.2A BH1750 firmware/evidence tests.
- STM32 protocol and recording bridge tests.
- Phase 3 current-plan anchors.

Smoke workflow:

- Audit required BMP280 bring-up files.
- Confirm the isolated Keil target and output directory.
- Confirm BMP280 register configuration constants.
- Validate the committed BMP280 physical evidence JSONL exact SHA-256 and internal structure.
- Confirm generated Keil artifacts are not tracked.
- Report BMP280, BH1750, and FullHardware local Keil build evidence when local builds have been run.

Phase 3.2C automated tests do not open real COM ports, USB devices, GPIO, I2C, flash tools, network sockets, motors, or real sensors. They validate the committed evidence file offline. The formal evidence marks isolated BMP280 ACK/address `0x76`, chip ID `0x58`, configuration readback, live compensated temperature/pressure telemetry, exact 500 ms periodicity, and stable 30-second capture as PHYSICAL_EVIDENCE_VERIFIED. Absolute temperature/pressure accuracy, long-duration operation, shared-I2C concurrency, and complete full-hardware operation remain UNVERIFIED.

## Phase 3.2D Automated Software Tests

Targeted:

- `pc/tests/test_openrf1_mpu6050_bringup.py`

Regression:

- Phase 3.2C BMP280 bring-up/evidence tests.
- Phase 3.2B firmware foundation tests.
- Phase 3.2A BH1750 firmware/evidence tests.
- STM32 protocol and recording bridge tests.
- Phase 3 current-plan anchors.

Smoke workflow:

- Audit required MPU6050 bring-up files.
- Confirm the isolated Keil target and output directory.
- Confirm MPU6050 register configuration constants.
- Confirm previous Phase 3.2A and Phase 3.2C raw evidence file hashes are unchanged.
- Confirm generated Keil artifacts are not tracked.
- Report MPU6050 local Keil build evidence when a local build has been run.

Phase 3.2D automated tests do not open real COM ports, USB devices, GPIO, I2C, flash tools, network sockets, motors, or real sensors. MPU6050 ACK, WHO_AM_I, configuration readback, live IMU telemetry, calibration, axis orientation, shared-I2C concurrency, and complete full-hardware operation remain UNVERIFIED.

## Phase 3.2E Automated Software Tests

Targeted:

- `pc/tests/test_openrf1_hcsr04_bringup.py`
- `pc/tests/test_openrf1_hcsr04_protocol.py`
- `pc/tests/test_openrf1_hcsr04_capture.py`
- `pc/tests/test_phase32e_evidence.py`

Regression:

- Phase 3.2D MPU6050 bring-up tests.
- Phase 3.2C BMP280 bring-up/evidence tests.
- Phase 3.2B firmware foundation tests.
- Phase 3.2A BH1750 firmware/evidence tests.
- STM32 protocol and recording bridge tests.
- Phase 3 current-plan anchors.

Smoke workflow:

- Audit required HC-SR04 bring-up files.
- Confirm CN6 pin order, PA5 TRIG, PA4 ECHO, TIM6, and the external 10 kOhm / 15 kOhm divider requirement.
- Confirm bounded trigger/echo timeout contracts, timer-wrap subtraction, nominal integer distance conversion, and JSONL identity/success/error records.
- Confirm the 512-byte JSONL / 513-byte C-buffer framing boundary, explicit formatting failures, and complete startup identity emission.
- Replay deterministic identity, pulse-boundary, timeout/recovery, malformed, sensor-ID, and session-order cases through the strict parser and dedicated mocked capture.
- Confirm evidence templates are not evidence and future sanitized candidates receive structural validation without automatic physical certification.
- Confirm the isolated Keil target and output directory.
- Confirm previous Phase 3.2A and Phase 3.2C raw evidence file hashes are unchanged.
- Confirm generated Keil artifacts are not tracked.
- Report HC-SR04 local Keil build evidence when a local build has been run.

Phase 3.2E automated tests do not open real COM ports, USB devices, GPIO, timer peripherals, I2C, flash tools, network sockets, motors, or real sensors. The dedicated capture uses a file-backed mock in automation. Physical wiring, trigger/echo pulses, real distance data, timeout behavior, timer accuracy, and absolute distance accuracy remain UNVERIFIED / PHYSICAL_VERIFICATION_REQUIRED.

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
- Bench hardware tests: test the one physical `c1_1` with the supplied adapter.
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

Phase 3.2A:

- Automated software tests: OpenRF1 BH1750 address/conversion logic, nonblocking state machine, firmware source constraints, mocked serial capture, strict parser reuse, recording bridge, and verifier smoke artifacts.
- Bench hardware tests: recorded manual evidence verifies Keil-built firmware flash, CH340/USART1 telemetry, BH1750 communication at configured address `0x23`, a 500 ms telemetry period, and controlled cover/illumination response.
- Stationary physical tests: recorded manual cover/uncover/lamp response exists for the BH1750-only path; absolute lux calibration remains UNVERIFIED.
- Moving-rover tests: not performed.
- Safety tests: documentation/checklist only; motors remain disconnected for first power-on.
- Presentation evidence: mocked telemetry, converted recording, build audit, manual status file, sanitized raw BH1750 physical evidence, and physical-evidence report.

Phase 3.2B:

- Automated software tests: STM32 sensor parsing/validation where available.
- Bench hardware tests: HC-SR04, TCRT5000, Hall, BH1750, BMP280 individually.
- Stationary physical tests: sensor threshold and environmental response checks.
- Moving-rover tests: limited low-speed sensor-state checks only after safety approval.
- Safety tests: edge/drop response, ultrasonic timeout behavior, local stop path.
- Presentation evidence: sensor logs, threshold tables, environmental-change demonstrations.

Phase 4A:

- Automated software tests: canonical and combined mecanum kinematics, round trips, explicit wheel-side encoder math/signs/wrap, exact and near-zero SE(2) integration, deterministic simulation, telemetry/recording compatibility, CLI failures, overwrite protection, privacy, generated-artifact hygiene, and no hardware access.
- Bench, stationary, moving-rover, and safety hardware tests: not part of Phase 4A.
- Presentation evidence: deterministic JSONL and verifier output only; no physical trajectory or accuracy claim.

Later Phase 4 hardware/control work:

- Bench hardware tests: encoder counts, MPU6050 readings, measured mecanum geometry, and safe per-wheel sign checks.
- Stationary physical tests: wheel direction and low-speed movement on blocks.
- Moving-rover tests: straight, lateral, yaw, repeatability, and calibrated accuracy runs.
- Safety tests: timeout stop and bounded command behavior.
- Presentation evidence: physical trajectory and error plots only after recorded evidence exists.

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
- Distance error for the physical `c1_1`.
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

`tools/validate_current_plan.py` checks explicit text anchors in authoritative current-plan files. It verifies the one-C1 baseline, BH1750/BMP280 presence, STM32/ESP32/PC roles, WiFi baseline, ROS/Linux non-goal status, and the revised phase order.

Limit: the validator checks literal text snippets only; it is not semantic AI analysis and does not validate historical documents unless they are treated as current-plan authorities.

## Phase 3.2B Software Foundation Tests

Run:

```powershell
.\tools\verify_phase.cmd phase3.2b -AllowDirty
```

The Phase 3.2B verifier covers:

- pure ring-buffer, scheduler, BMP280, MPU6050, debounce, and HC-SR04 state-machine tests
- STM32-to-ESP32 binary frame golden vectors, CRC failures, malformed-frame recovery, and sequence gaps
- strict JSON telemetry parsing for `imu_raw`, `subsystem_status`, `link_status`, and `lidar_transport_stats`
- deterministic Phase 3.2B telemetry generation, recording conversion, and inspection
- static firmware source audit for bounded buffers, feature flags, no dynamic allocation, no unbounded high-rate debug output, and isolated Keil outputs
- baseline Phase 3.2A and full-hardware Phase 3.2B Keil build evidence

Phase 3.2B automated tests do not open real COM ports, USB devices, WiFi sockets, GPIO, I2C, flashing tools, or sensors.

## Phase 3.2C BMP280 Bring-Up Tests

Run:

```powershell
.\tools\verify_phase.cmd phase3.2c -AllowDirty
```

The Phase 3.2C verifier covers:

- BMP280 chip ID, calibration parsing, raw sample decoding, configuration register constants, compensation, and JSONL telemetry formatting
- static source checks for the BMP280-only firmware boundary
- Keil target isolation under `Objects_BMP280_Bringup/`
- exact SHA-256 and structure of the committed BMP280 physical evidence
- regression tests for Phase 3.2A and Phase 3.2B software contracts
- local build evidence reporting for BH1750, FullHardware, and BMP280 bring-up targets

Recorded BMP280 physical evidence is documented in `evidence/phase3.2c/bmp280_physical_evidence.md`. Future repeat testing should follow `docs/openrf1_bmp280_bringup.md` and must keep private local details out of tracked files.

## Phase 3.2D MPU6050 Bring-Up Tests

Run:

```powershell
.\tools\verify_phase.cmd phase3.2d -AllowDirty
```

The Phase 3.2D verifier covers:

- MPU6050 WHO_AM_I validation, register configuration constants, 14-byte burst decoding, raw conversion to g/dps/temperature units, and JSONL telemetry formatting
- static source checks for the MPU6050-only firmware boundary
- Keil target isolation under `Objects_MPU6050_Bringup/`
- previous raw Phase 3.2A and Phase 3.2C evidence hash preservation
- regression tests for Phase 3.2A, Phase 3.2B, and Phase 3.2C software/evidence contracts
- local build evidence reporting for the MPU6050 bring-up target when a local build has been run

Future manual testing should follow `docs/openrf1_mpu6050_bringup.md` and must keep private local details out of tracked files.

## Phase 3.2E HC-SR04 Bring-Up Tests

Run:

```powershell
.\tools\verify_phase.cmd phase3.2e -AllowDirty
```

The Phase 3.2E verifier covers:

- HC-SR04 CN6 pin order, PA5 TRIG, PA4 ECHO, TIM6, and external divider documentation
- static source checks for the HC-SR04-only firmware boundary
- bounded wait-for-low, rising-edge timeout, falling-edge timeout, no infinite wait, and no stale distance after error contracts
- timer-wrap-safe pulse-width subtraction and integer distance conversion vectors
- JSONL startup identity, success, and error schema contracts
- Keil target isolation under `Objects_HCSR04_Bringup/`
- previous raw Phase 3.2A and Phase 3.2C evidence hash preservation
- regression tests for Phase 3.2A, Phase 3.2B, Phase 3.2C, and Phase 3.2D software/evidence contracts

Future manual testing should follow `docs/openrf1_hcsr04_bringup.md` and must keep private local details out of tracked files.

## Phase 3.2F Ground-Sensor Bring-Up Tests

Run:

```powershell
.\tools\verify_phase.cmd phase3.2f -AllowDirty
```

The Phase 3.2F verifier covers:

- signal 1 / X1 / PC4, signal 2 / X2 / PC5, and signal 3 / X3 / PB0 mapping contracts
- signal 4 / X4 unused status and the PC14/PB1 source conflict
- PC4, PC5, and PB0 floating input firmware representation
- 5 ms sampling, 4-sample debounce, effective 20 ms stability, and 50 ms telemetry period
- startup initialization from observed raw levels
- stable input, low-to-high, high-to-low, bouncing input, and independent-channel debounce vectors
- strict JSONL identity and periodic records with numeric raw/debounced levels only
- no semantic detection claims and no fake disconnected-sensor detection
- TCRT 3.3 V supply documentation, Hall 5 V supply documentation, Hall external 10 kOhm / 15 kOhm divider documentation, and direct Hall S -> PB0 prohibition
- Keil target isolation under `Objects_GroundSensors_Bringup/`
- no UTF-8 BOM in `OpenRF1_GroundSensors_Bringup.uvprojx`
- previous raw Phase 3.2A and Phase 3.2C evidence hash preservation
- regression tests for Phase 3.2A, Phase 3.2B, Phase 3.2C, Phase 3.2D, and Phase 3.2E software/evidence contracts

Phase 3.2F automated tests do not open real COM ports, USB devices, GPIO, timer peripherals, flashing tools, or sensors. Future manual testing should follow `docs/openrf1_ground_sensors_bringup.md` and must keep private local details out of tracked files.

## Phase 4A Mecanum Kinematics and Odometry Tests

Run:

```powershell
.\tools\verify_phase.cmd phase4a -AllowDirty
```

The Phase 4A verifier covers:

- standard X-layout inverse and forward canonical motions and round trips;
- explicit finite positive geometry and wheel-side counts-per-revolution validation;
- four independent `+1`/`-1` direction multipliers and explicit-only counter wrap;
- stationary, forward, left-strafe, counterclockwise-rotation, and combined-motion odometry;
- exact constant-twist SE(2), stable near-zero yaw, nonzero initial heading, and yaw normalization;
- deterministic UTF-8 JSONL simulation, strict version-1 telemetry, recording bridge, inspection, CLI errors, and overwrite protection;
- Phase 2.x/3.x regression tests and the complete PC suite;
- privacy and generated-artifact tracking scans.

Phase 4A automated tests do not open COM ports, USB devices, GPIO, timers, encoders, motors, I2C, Keil, FlyMcu, flashing tools, network sockets, or sensors. Actual geometry, counts per wheel revolution, gear ratio, counter width, direction signs, roller orientation, acquisition timing, wheel slip, motor behavior, MPU6050 fusion, and physical odometry accuracy remain UNVERIFIED.

## Phase 4B Closed-Loop Motion-Control Foundation Tests

Run:

```powershell
.\tools\verify_phase.cmd phase4b -AllowDirty
```

The Phase 4B verifier covers body-command validation; canonical and mixed Phase 4A targets; proportional desaturation; per-wheel acceleration limiting and reversal; derivative-on-measurement PID; positive/negative saturation and conditional anti-windup; recovery, disable, and reset; four independent controller states; supplied-timestamp watchdog boundaries; emergency, controller, communication, edge, ultrasonic, sensor-validity, and external-stop policies; deterministic stop/restart; all 12 synthetic scenarios; slow-wheel mismatch; JSONL parsing; recording conversion and inspection; CLI success/failure/overwrite behavior; Phase 4A and Phase 3 regression tests; the full PC suite; privacy/artifact scans; and source-level no-hardware-import checks.

Phase 4B automated tests do not open COM ports, USB devices, GPIO, I2C, timers, encoders, motors, sensors, network sockets, Keil, FlyMcu, or flashing tools. Motor rotation, encoder acquisition, physical direction, PWM mapping, usable physical PID gains, roller orientation, trajectory following, stopping distance, and real closed-loop performance remain UNVERIFIED.
