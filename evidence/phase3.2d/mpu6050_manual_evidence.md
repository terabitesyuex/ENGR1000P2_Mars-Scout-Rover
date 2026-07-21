# Phase 3.2D MPU6050 Manual Evidence

This report contains only A's authorized, sanitized claims from the isolated
OpenRF1 MPU6050-only bring-up. It does not include raw terminal output, a
concrete COM port, local paths, unique device identifiers, build-artifact
metadata, or measurements outside A's authoritative evidence list.

## Evidence Scope

| Field | Value |
| --- | --- |
| Sensor ID | `mpu6050_1` |
| Isolated target | `firmware/openrf1/keil/OpenRF1_MPU6050_Bringup.uvprojx` |
| Evidence source | Sanitized report supplied by A |
| Automation role | Repository consistency checks only |

Repository automation did not build or flash firmware, open a serial port,
access USB or I2C, or physically read the sensor. C did not perform or repeat
the hardware test.

## Authorized Isolated Bring-Up Claims

- A reported the isolated GY-521/MPU6050 wiring as VCC to OpenRF1 H4 5 V,
  GND to H4 GND, SCL to PB1/SCL, SDA to PC3/SDA, and AD0 to GND.
- I2C ACK at address `0x68`: MANUAL_EVIDENCE_VERIFIED.
- WHO_AM_I register result `0x68`: MANUAL_EVIDENCE_VERIFIED.
- Isolated configuration readback: MANUAL_EVIDENCE_VERIFIED.
- Live IMU JSON telemetry: MANUAL_EVIDENCE_VERIFIED.
- Startup dynamic gyro-bias calibration semantics: MANUAL_EVIDENCE_VERIFIED.
- `gyro_raw` preserves raw register data while `gyro_dps` subtracts the
  startup dynamic bias: MANUAL_EVIDENCE_VERIFIED.
- A reported approximately 10 Hz telemetry during a 15-second isolated test
  with no sequence loss: MANUAL_EVIDENCE_VERIFIED.
- Manual rotation and flip produced an isolated sensor-axis response:
  MANUAL_EVIDENCE_VERIFIED. This does not verify rover-frame orientation.

## Still UNVERIFIED

- Exact connector orientation, measured rail or signal voltages, electrical
  continuity, and wiring safety beyond A's authorized isolated wiring report.
- Reproducible Keil build output, build warnings, firmware artifact identity,
  artifact size or hash, and the firmware flashing procedure.
- Software-I2C delay-loop tuning as the cause of observed communication.
- Exact frame count, exact inter-frame timing, and timing beyond A's reported
  approximately 10 Hz result during the 15-second isolated test.
- Exact gyro bias or standard-deviation values and stationary-noise limits.
- Absolute acceleration accuracy and absolute angular-rate accuracy.
- Calibration-time motion detection and calibration motion rejection.
- Long-duration thermal drift, accelerometer offsets, yaw drift, and
  temperature accuracy.
- Shared-I2C concurrency with BH1750 and BMP280.
- Complete multisensor firmware operation and complete rover operation.
- Final installed coordinate orientation and rover-frame alignment.
- Performance under motor vibration.
- Encoder/IMU fusion and physical odometry accuracy.
- ESP32/WiFi integration.
