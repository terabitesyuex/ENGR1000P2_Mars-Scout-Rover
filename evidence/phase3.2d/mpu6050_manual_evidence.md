# Phase 3.2D MPU6050 Manual Evidence

This report summarizes A's recorded manual hardware evidence for the isolated
OpenRF1 MPU6050-only bring-up target. No raw terminal log, concrete COM port,
MCU unique identifier, local path, or unsanitized device identifier is recorded
in this repository.

## Evidence Summary

| Field | Value |
| --- | --- |
| Sensor ID | `mpu6050_1` |
| Isolated firmware target | `firmware/openrf1/keil/OpenRF1_MPU6050_Bringup.uvprojx` |
| Reported final HEX name | `OpenRF1_MPU6050_FINAL_AUTO_CAL_20260720.hex` |
| Reported final HEX size | 51928 bytes |
| Reported final HEX SHA-256 | `403F46A865A32B496586CA4B36E476ECED53C2165868F4B0FA7BCBA8BCB0D55F` |
| Reported Keil build result | 0 errors, 0 warnings |
| Formal continuity-test frames | 151 |
| Formal continuity-test wall time | 15.05 s |
| Formal timestamp span | 15000 ms |
| Median / maximum interval | 100 ms / 100 ms |
| Sequence gaps greater than 1 | 0 |

The HEX metadata above is A's reported build artifact. Repository automation
did not reproduce the Keil build or recalculate this hash.

## Manual Wiring And Electrical Evidence

- OpenRF1 H4 connector order in A's photo orientation, left to right:
  5 V, GND, PB1 / SCL, PC3 / SDA.
- MPU6050 VCC -> H4 5 V: MANUAL_EVIDENCE_VERIFIED.
- MPU6050 GND -> H4 GND: MANUAL_EVIDENCE_VERIFIED.
- MPU6050 SCL -> PB1 / SCL: MANUAL_EVIDENCE_VERIFIED.
- MPU6050 SDA -> PC3 / SDA: MANUAL_EVIDENCE_VERIFIED.
- AD0 measured 0 V: MANUAL_EVIDENCE_VERIFIED.
- H4 5 V approximately 4.77 V: MANUAL_EVIDENCE_VERIFIED.
- MPU6050 VCC approximately 4.78 V: MANUAL_EVIDENCE_VERIFIED.
- SCL idle approximately 3.31 V: MANUAL_EVIDENCE_VERIFIED.
- SDA idle approximately 3.31 V: MANUAL_EVIDENCE_VERIFIED.
- Continuity checks found no signal-line short to power or ground:
  MANUAL_EVIDENCE_VERIFIED.

## Verified Isolated Bring-Up Claims

- Isolated MPU6050 firmware flashing and execution from Flash:
  MANUAL_EVIDENCE_VERIFIED.
- Software-I2C communication became stable after the delay loop was changed
  from `ticks = 24u` to `ticks = 240u`: MANUAL_EVIDENCE_VERIFIED.
- I2C ACK at address `0x68`: MANUAL_EVIDENCE_VERIFIED.
- WHO_AM_I register result `0x68`: MANUAL_EVIDENCE_VERIFIED.
- Isolated bring-up configuration readback: MANUAL_EVIDENCE_VERIFIED.
- Live IMU JSON telemetry on USART1 / CH340: MANUAL_EVIDENCE_VERIFIED.
- Startup dynamic gyro-bias calibration: MANUAL_EVIDENCE_VERIFIED.
- `gyro_raw` preserves raw register data while `gyro_dps` subtracts the
  dynamic bias: MANUAL_EVIDENCE_VERIFIED.
- Approximately 10 Hz telemetry output: MANUAL_EVIDENCE_VERIFIED.
- 15-second test without sequence loss greater than one: MANUAL_EVIDENCE_VERIFIED.
- Manual rotation/flip produced expected gravity-axis response for isolated
  bring-up: MANUAL_EVIDENCE_VERIFIED.

## Calibration Summary

- Startup warmup: 5000 ms.
- Calibration samples: 500.
- Calibration sample interval: approximately 10 ms.
- X mean approximately -0.0117 dps; X std approximately 0.1826 dps.
- Y mean approximately 0.0279 dps; Y std approximately 0.1326 dps.
- Z mean approximately 0.1331 dps; Z std approximately 0.1014 dps.
- In the recorded stationary summary, all three axes remained below 1 dps.
- The sensor must remain still for approximately 12 seconds after each power-on
  or reset.

## Still UNVERIFIED

- Absolute acceleration accuracy.
- Absolute angular-rate accuracy.
- Calibration-time motion detection.
- Calibration motion rejection.
- Long-duration thermal drift.
- Shared-I2C concurrency with BH1750 and BMP280.
- Complete multisensor firmware operation.
- Complete rover operation.
- Final installed coordinate orientation and rover-frame alignment.
- Performance under motor vibration.
- Encoder/IMU fusion.
- Physical odometry accuracy.
- ESP32/WiFi integration.

Automation validates repository consistency only. It did not flash hardware,
open a serial port, access USB, run GPIO/I2C, or physically read the sensor.
