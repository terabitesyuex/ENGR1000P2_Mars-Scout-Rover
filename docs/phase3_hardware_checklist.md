# Phase 3 Hardware Checklist

Do not mark checklist items complete automatically. Record measured evidence before changing any UNVERIFIED value.

## General Evidence Table

Evidence table fields:

| Test date | Operator | Firmware commit | Board identity | Sensor ID | Wiring revision | Test procedure | Expected result | Observed result | Pass/fail | Notes | Evidence path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED |

## General Bring-Up

- Identify exact STM32 board and MCU.
- Record board revision.
- Identify firmware toolchain.
- Verify programmer/debugger.
- Inspect connectors.
- Power off before changing wiring.
- Verify supply voltage with a multimeter.
- Verify logic levels.
- Confirm common ground.
- Use current-limited first power-up where practical.
- Connect one sensor at a time.
- Record photos and measured values.
- Redact unnecessary device identifiers in public evidence.

## HC-SR04

- Verify VCC requirement.
- Verify TRIG input compatibility.
- Measure or verify ECHO high voltage.
- Determine whether a divider or level shifter is required.
- Echo level protection is conditional on module supply and measured Echo VOH; direct connection is not approved until measured or the exact MCU pin tolerance is established.
- For first test, power one wide-voltage HC-SR04 from the OpenRF1 3.3 V output and do not use the PWM servo-interface rail.
- Test one unit before three.
- Test timeout behavior.
- Test minimum and maximum useful distance.
- Test cross-talk with multiple units.
- Record physical mounting direction.

## TCRT5000

- Verify connector orientation.
- Verify supply voltage.
- Verify raw idle and trigger states.
- Determine active polarity.
- Measure performance over actual floor and edge materials.
- Verify edge/drop threshold.
- Verify both modules independently.
- Preserve raw state in telemetry until polarity is verified.

## Hall

- Verify raw idle and trigger states.
- Determine active polarity.
- Identify useful magnet orientation and distance.
- Verify it is treated only as landmark/checkpoint input.
- Preserve raw state in telemetry until polarity is verified.

## BH1750 And BMP280

- Verify I2C voltage.
- Verify pull-ups.
- Run real I2C address discovery.
- Verify both sensors can share the bus.
- Record detected addresses.
- Verify units and plausible room readings.
- Document environmental-change limitations.
- Do not claim reliable dust-storm detection.

Phase 3.2C recorded evidence verifies one isolated BMP280-only capture at address `0x76` with chip ID `0x58`, configuration readback, compensated live temperature/pressure telemetry, exact 500 ms periodicity, and no I2C errors during the formal 30-second run. This does not verify absolute temperature/pressure accuracy, environmental-reference comparison, long-duration operation, shared-I2C concurrency, or full-hardware operation.

## Phase 3.2A OpenRF1 GY-302/BH1750

Do not mark these items complete automatically.

- Confirm OpenRF1 board identity and STM32F103RCT6 marking.
- Confirm the 2x4 I2C header, not the adjacent SWD connector.
- Confirm OpenRF1 I2C 5V and GND with power off before wiring.
- Wire GY-302 VCC -> OpenRF1 I2C 5V.
- Wire GY-302 GND -> OpenRF1 I2C GND.
- Wire GY-302 SCL -> OpenRF1 PB1/SCL.
- Wire GY-302 SDA -> OpenRF1 PC3/SDA.
- Wire GY-302 ADDR -> OpenRF1 GND.
- Keep motors and other new sensors disconnected for first power-on.
- Build the STM32F103RC Keil project before flashing.
- Flash only by the documented USB ISP or SWD method.
- Identify the CH340 COM port privately in Device Manager.
- Open serial at 115200 baud 8N1.
- Confirm valid versioned JSONL output.
- Confirm BH1750 ACK at public 7-bit address `0x23`.
- Record uncovered room-light readings.
- Cover the sensor and confirm lux decreases strongly.
- Shine a lamp indirectly and confirm lux increases.
- Capture at least 30 seconds of telemetry and convert it to Phase 2.4 recording.
- Record commit, date, operator, wiring revision, COM port privately, expected result, observed result, pass/fail, notes, and evidence paths.

Recorded evidence status:

- Firmware flash: MANUAL_EVIDENCE_VERIFIED.
- CH340/USART1 telemetry: MANUAL_EVIDENCE_VERIFIED.
- BH1750 communication at configured address `0x23`: MANUAL_EVIDENCE_VERIFIED.
- 500 ms telemetry period: MANUAL_EVIDENCE_VERIFIED.
- Physical cover/illumination response: MANUAL_EVIDENCE_VERIFIED.
- Absolute illuminance calibration: UNVERIFIED.

## Planned Ground/Landmark Connector

The following is USER-CONFIRMED PLANNED CONNECTION only:

- TCRT5000 left OUT -> PH2.0-6P line-tracking connector signal channel 1.
- TCRT5000 right OUT -> signal channel 2.
- Hall sensor S -> signal channel 3.
- The old shared-VCC plan is superseded by module-specific evidence: TCRT5000 modules should use 3.3 V and the Hall module should use 5 V. Common ground remains required.

Before use, verify connector orientation, exact pin order, supply rails, logic voltage, Hall output topology, common ground, and polarity.

## Phase 3.2B Manual Bring-Up Order

Do not mark these items complete automatically.

1. Preserve the committed BH1750-only physical evidence and repeat only if wiring or firmware changes.
2. Preserve the committed Phase 3.2C isolated BMP280 evidence and repeat only if wiring or firmware changes; shared-bus BMP280 operation with other I2C devices remains a separate validation.
3. Validate MPU6050 alone at 5 V with AD0 -> GND.
4. Validate all three I2C devices together without tying their VCC rails together.
5. Validate TCRT5000 raw inputs at 3.3 V.
6. Measure Hall `S` voltage in both magnetic states before STM32 input connection.
7. Validate one HC-SR04 from 3.3 V and measure Echo VOH before approving direct input or adding protection.
8. Validate all three HC-SR04 modules with staggered triggering.
9. Validate USART2 electrical idle and loopback where safe.
10. Validate one C1 unit on USART2.
11. Validate USART3 loopback.
12. Validate ESP32-C3 link with USB disconnected from the ESP32 while OpenRF1 5 V is feeding it.
13. Validate C1-to-ESP32 data transport.
14. Perform full-system power and concurrency testing.

Record voltage levels, common ground, exact connector pins, observed raw states, pass/fail, and evidence paths for each step. Physical Phase 3.2B remains UNVERIFIED until this evidence exists.
