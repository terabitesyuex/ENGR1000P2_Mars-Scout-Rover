# Calibration Plan

No physical calibration is completed by Phase 2.5 automation. This file records future calibration responsibilities only.

## RPLIDAR C1

- Calibrate `c1_1` independently.
- Calibrate `c1_2` independently.
- Use Phase 2.5 PC-direct captures as input evidence only after the manual hardware procedure is actually run.
- Confirm forward direction relative to rover chassis.
- Confirm native zero-angle direction.
- Record mounting height, position, yaw, and orientation.
- Confirm range bias against known distances.
- Confirm angular orientation using known wall geometry.
- Measure scan rate and dropped/corrupt scan rate.

## HC-SR04

- Measure distance error for each of `ultrasonic_1`, `ultrasonic_2`, and `ultrasonic_3`.
- Measure timeout behavior.
- Measure cross-talk rate.
- Relate measured ranges to stop-distance contribution.
- Verify logic-level interface before wiring to the physical controller.

## TCRT5000

- Calibrate `tcrt5000_1` and `tcrt5000_2` for edge/drop detection.
- Measure false positives.
- Check installation-height sensitivity.
- Verify active polarity before relying on safety decisions.

## Hall Sensor

- Calibrate `hall_1` for magnetic landmark/checkpoint detection.
- Measure repeatability and false positives.
- Do not use the Hall module as wheel odometry.
- Verify active polarity before hardware integration.

## BH1750

- Calibrate `bh1750_1` illuminance response in lux.
- Measure repeatability.
- Test response to controlled light changes.
- Do not claim reliable real-world dust-storm detection.

## BMP280

- Calibrate `bmp280_1` temperature and atmospheric-pressure readings.
- Measure temperature stability.
- Measure pressure stability.
- Test response to controlled environmental changes where practical.

## Encoders And Mecanum Geometry

- Measure encoder counts per wheel revolution.
- Measure wheel diameter.
- Measure wheelbase and track geometry.
- Verify forward, lateral, and yaw kinematics.
- Measure straight-distance, lateral-distance, yaw, and repeatability errors.

## MPU6050

- Measure gyro bias.
- Measure accelerometer offsets.
- Confirm axis orientation relative to the rover.
- Measure yaw drift over short intervals.

## WiFi Timing

- Measure packet loss.
- Measure latency.
- Measure reconnection behavior.
- Confirm timeout stop behavior is independent of PC visualization.

## Accumulated Map Dimensions

- Use known-dimension test areas.
- Measure point-cloud distortion.
- Measure trajectory drift.
- Record map-scale and frame-assignment assumptions.

Calibration changes must be recorded in `CHANGELOG.md` only after measurements are performed.
