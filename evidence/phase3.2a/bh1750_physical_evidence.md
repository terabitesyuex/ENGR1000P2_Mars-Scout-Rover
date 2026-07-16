# Phase 3.2A BH1750 Physical Evidence

This report summarizes recorded manual hardware evidence for the OpenRF1
GY-302/BH1750 bring-up. The raw JSONL evidence file is stored in this
repository directory beside the report.

## Evidence Files

| Field | Value |
| --- | --- |
| Firmware commit | `ba2024b` |
| Frozen HEX SHA-256 | `F614110B67BFA6F019D81089D8D19B20E6F06A39DA78A9009C8F691B9C442089` |
| Raw telemetry file | `bh1750_physical_ba2024b_20260716_234217.jsonl` |
| Raw telemetry SHA-256 | `6B9A2AE724C6473D6D8F18533CDC7B7081BCC782709862E914CE6B20B1690317` |
| Record count | 60 |
| Sequence range | 769 through 828 |
| Timestamp interval | exactly 500 ms |
| Minimum lux | 0.00 |
| Maximum lux | 20.83 |

## Sanitized Flash Summary

- FlyMcu connected successfully to a user-verified CH340 port.
- Baud: 115200.
- STM32 ROM bootloader version: 2.2.
- Device PID: 0x0414, High-density.
- Detected flash: 256 KB.
- Full erase succeeded.
- Approximately 12 KB was programmed.
- Execution from 0x08000000 succeeded.

The COM identifier and MCU unique serial number are intentionally not recorded
in tracked files.

## Verified Claims

- Firmware build: SOFTWARE_VERIFIED.
- Firmware flash: MANUAL_EVIDENCE_VERIFIED.
- CH340/USART1 telemetry: MANUAL_EVIDENCE_VERIFIED.
- BH1750 communication at configured 7-bit address `0x23`: MANUAL_EVIDENCE_VERIFIED.
- Telemetry protocol `mars_scout_stm32_sensor_telemetry` version `1`: MANUAL_EVIDENCE_VERIFIED.
- Message type `illuminance` and sensor ID `bh1750_1`: MANUAL_EVIDENCE_VERIFIED.
- Status `ok` for all records: MANUAL_EVIDENCE_VERIFIED.
- Continuous sequence 769 through 828: MANUAL_EVIDENCE_VERIFIED.
- 500 ms telemetry period: MANUAL_EVIDENCE_VERIFIED.
- Physical cover and illumination response: MANUAL_EVIDENCE_VERIFIED.
- GY-302 module powered from the OpenRF1 5 V I2C supply for this run: MANUAL_EVIDENCE_VERIFIED.

## Still UNVERIFIED

- Absolute illuminance calibration.
- Long-duration BH1750 stability.
- Behavior with BMP280 or MPU6050 sharing the I2C signal bus.
- Any HC-SR04, TCRT5000, Hall, RPLIDAR C1, ESP32, motor, encoder, WiFi, mapping, or full-system result.
- Full-system current, regulator temperature, noise, brownout behavior, and motor-interference behavior.

Automation validates only the committed evidence file integrity and internal
properties. It did not flash hardware, open a real COM port, access USB, run
GPIO/I2C, or physically read the sensor.
