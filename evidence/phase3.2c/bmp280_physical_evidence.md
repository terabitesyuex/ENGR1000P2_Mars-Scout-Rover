# Phase 3.2C BMP280 Physical Evidence

This report summarizes recorded manual hardware evidence for the isolated
OpenRF1 BMP280-only bring-up target. The raw JSONL capture is stored beside
this report and is validated byte-for-byte by repository tests.

## Evidence Files

| Field | Value |
| --- | --- |
| Source firmware commit | `adef636` |
| Formal Keil HEX SHA-256 | `85101B9F76C27FDFA019E382FC7285F239F78FA78FB0722B0400F8DDFF67E27E` |
| Raw telemetry file | `bmp280_physical_adef636_20260718_002346.jsonl` |
| Raw telemetry SHA-256 | `1BB0C5BE149DC7C49A3C63432D1CAE4AACAE3D5A80265FE879CA06D1E1A74805` |
| Record count | 61 |
| Sensor identity records | 1 |
| Environmental records | 60 |
| Sequence range | 0 through 60 |
| First timestamp | 6 ms |
| First environmental timestamp | 506 ms |
| Last timestamp | 30006 ms |
| Capture duration | 30000 ms from identity to final sample |
| Environmental sample span | 29500 ms |
| Timestamp interval | exactly 500 ms between all consecutive records |

## Identity And Configuration Results

- Protocol: `mars_scout_stm32_sensor_telemetry`, version `1`.
- Sensor ID: `bmp280_1`.
- Configured address: `0x76`.
- Expected chip ID: `0x58`.
- Observed chip ID: `0x58`.
- `ctrl_meas` readback: `0x27`.
- `config` readback: `0x80`.
- All 61 records have `status:"ok"`.
- No `nack` or other error records appear in the formal capture.

## Environmental Results

- Temperature range: 26.18 C to 26.23 C.
- Pressure range: 99867 Pa to 99882 Pa.
- All 60 environmental records contain numeric temperature and pressure values.
- Every environmental interval is exactly 500 ms.
- The full capture is a stable 30-second run.

## Physical Conclusions

- Isolated BMP280 firmware flashing with FlyMcu: PHYSICAL_EVIDENCE_VERIFIED.
- USART1 / CH340 JSONL telemetry: PHYSICAL_EVIDENCE_VERIFIED.
- I2C communication at `0x76`: PHYSICAL_EVIDENCE_VERIFIED.
- BMP280 ACK at `0x76`: PHYSICAL_EVIDENCE_VERIFIED.
- BMP280 chip ID `0x58`: PHYSICAL_EVIDENCE_VERIFIED.
- Calibration-register path sufficient for compensated output: PHYSICAL_EVIDENCE_VERIFIED.
- `ctrl_meas = 0x27` and `config = 0x80` write/readback: PHYSICAL_EVIDENCE_VERIFIED.
- Continuous compensated temperature telemetry: PHYSICAL_EVIDENCE_VERIFIED.
- Continuous compensated pressure telemetry: PHYSICAL_EVIDENCE_VERIFIED.
- 500 ms periodicity: PHYSICAL_EVIDENCE_VERIFIED.
- Stable 30-second BMP280-only capture: PHYSICAL_EVIDENCE_VERIFIED.
- I2C errors in this formal capture: none observed.

## Still UNVERIFIED

- Absolute temperature accuracy.
- Absolute pressure accuracy.
- Comparison against an environmental reference instrument.
- Long-duration operation beyond this 30-second capture.
- Full multi-device shared-I2C concurrency with BH1750 or MPU6050.
- Complete Phase 3.2B full-hardware operation.
- Behavior with motors, encoders, ESP32, RPLIDAR C1, ultrasonic sensors, TCRT5000 sensors, Hall sensor, WiFi, mapping, navigation, or obstacle avoidance.

Automation validates only the committed evidence file integrity and internal
properties. It did not flash hardware, open a serial port, access USB, run
GPIO/I2C, or physically read the sensor.
