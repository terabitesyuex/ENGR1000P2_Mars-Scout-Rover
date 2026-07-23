# Phase 3 Hardware Checklist

Do not mark checklist items complete automatically. Record measured evidence before changing any UNVERIFIED value.

The user reports complete vehicle assembly, but no new checklist evidence has
been recorded. Use `near_term_vehicle_bringup_handoff.md` before beginning
Phase 4C software work or requesting any physical action.

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
- Review [`hardware_materials_bom.md`](hardware_materials_bom.md) before buying or adapting connector, power, divider, or vehicle-installation parts.

## Battery And Main Power

- Seller evidence documents a Li-ion pack advertised as 11.1 V, 7800 mAh, 5C,
  12.6 V fully charged, 70 x 55 x 23 mm, with a DC 5.5 x 2.5 mm male connector.
- Seller evidence documents a 12.6 V/1 A charger with DC 5.5 x 2.5 mm female
  connector; it is not a rover power supply.
- Disconnect the battery from the rover before charging.
- Meter battery and charger centre/sleeve polarity before making any adapter.
- Measure pack no-load and fully charged voltage.
- Obtain the BMS continuous/peak and overcurrent-trip ratings; do not substitute
  the calculated 39 A advertised-rate value for a BMS specification.
- Select the main fuse and motor wire only after BMS and controlled motor-current
  data are available.

## HC-SR04

- Confirm the physical inventory is three HC-SR04 modules.
- Verify VCC requirement.
- Verify TRIG input compatibility.
- Measure ECHO high voltage before and after the required divider.
- Confirm the external 10 kOhm / 15 kOhm divider is installed before PA4 receives ECHO.
- Do not connect HC-SR04 ECHO directly to CN6 pin 4.
- For Phase 3.2E, use the vendor-documented CN6 path only after installing the required external 10 kOhm / 15 kOhm ECHO divider. Do not connect HC-SR04 ECHO directly to CN6 pin 4.
- Use the keyed JST PH 2.0 mm `PHR-4` cable. Do not force 2.54 mm Dupont leads into CN6.
- Test the three physical modules sequentially, one at a time, on the single CN6 baseline and label every module/capture.
- Keep GPIO, connector, and timer resources for the other two simultaneous paths UNVERIFIED until separately designed.
- Provide one independent 10 kOhm / 15 kOhm divider per HC-SR04 ECHO in final simultaneous wiring. Do not share divider midpoints.
- Test timeout behavior.
- Test minimum and maximum useful distance.
- Test cross-talk only after three separate safe paths and staggered triggering have been implemented and reviewed.
- Record physical mounting direction.

## TCRT5000

- Isolated X1/PC4 and X2/PC5 signal connections are MANUAL_EVIDENCE_VERIFIED.
- Both modules produced recorded raw/debounced transitions, and four 100-frame steady-state captures had no gaps and exact 50 ms timestamps.
- Verify final connector orientation and strain relief after rover installation.
- Measure supply and OUT high/low voltages with a multimeter.
- Determine active polarity.
- Measure performance over actual floor and edge materials.
- Verify edge/drop threshold.
- Verify dependable distance window and ambient-light margin.
- Preserve raw state in telemetry until polarity is verified.

## Hall

- Verify raw idle and trigger states.
- Determine active polarity.
- Identify useful magnet orientation and distance.
- Verify it is treated only as landmark/checkpoint input.
- Preserve raw state in telemetry until polarity is verified.

## Phase 3.2F Ground-Sensor Bring-Up

Completed boxes below are backed by `evidence/phase3.2f/`. Do not complete remaining boxes without new manual evidence.

1. [x] Confirm official Keil build.
2. [x] Record HEX SHA-256.
3. [ ] Remove all board power.
4. [ ] Verify connector orientation.
5. [x] Verify installed signal 1 -> PC4 connection.
6. [x] Verify installed signal 2 -> PC5 connection.
7. [ ] Verify signal 3 -> PB0.
8. [ ] Confirm signal 4 remains unused.
9. [ ] Confirm both TCRT modules receive 3.3 V.
10. [ ] Confirm Hall module receives 5 V.
11. [ ] Confirm all modules share common ground.
12. [ ] Confirm Hall S passes through the external 10 kOhm / 15 kOhm divider.
13. [ ] Confirm Hall S is not directly connected to PB0.
14. [x] Flash isolated target.
15. [x] Reset and capture identity record.
16. [x] Confirm 50 ms steady-state periodic JSONL telemetry.
17. [ ] Record resting levels.
18. [x] Test left TCRT over a reflective white surface at the recorded geometry.
19. [ ] Test left TCRT over a dark surface.
20. [x] Test left TCRT in the recorded open-space geometry.
21. [x] Confirm the left channel transition in isolated captures.
22. [x] Repeat recorded reflective-surface/open-space tests for the right TCRT.
23. [x] Confirm the right channel transition in isolated captures.
24. [ ] Test Hall with no magnet.
25. [ ] Approach the marked A3144 face with a suitable magnetic pole.
26. [ ] Observe raw and debounced transition.
27. [ ] Remove the magnet.
28. [ ] Confirm release transition.
29. [ ] Repeat transitions several times.
30. [ ] Determine actual electrical and semantic polarity.
31. [ ] Record Hall orientation and triggering pole.
32. [ ] Record whether 20 ms debounce is suitable.
33. [x] Save sanitized raw JSONL without modifying telemetry content.
34. [x] Hash raw evidence before integration.

The multimeter is now available. Leave these incomplete until the readings are captured and recorded: 3.3 V rail measurement, 5 V rail measurement, left TCRT OUT high and low voltage, right TCRT OUT high and low voltage, Hall S voltage before divider without magnet, Hall S voltage before divider with magnet, PB0 voltage after divider without magnet, PB0 voltage after divider with magnet, and actual installed divider resistor values.

Phase 3.2F uses vendor-documented signal 1 / X1 / PC4, signal 2 / X2 / PC5, and signal 3 / X3 / PB0 mappings. Signal 4 / X4 remains unused because the schematic says PC14 while the old example maps X4 to PB1. Do not power the TCRT modules from the connector's 5 V pin. Do not connect Hall S directly to PB0. Do not share one VCC rail across all three modules. The recorded 0/1 responses are electrical states, not black/white/drop semantics; polarity remains unverified.

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

## MPU6050

- Verify GY-521/MPU6050 module supply voltage and polarity before connection.
- Wire VCC -> OpenRF1 5 V, GND -> GND, SCL -> PB1/B1, SDA -> PC3/C3, and AD0 -> GND only for the isolated Phase 3.2D test.
- Leave INT, XDA, XCL, and FSYNC disconnected for polling bring-up.
- Verify ACK at planned address `0x68`.
- Verify WHO_AM_I register `0x75` reads `0x68`.
- Verify `PWR_MGMT_1`, `SMPLRT_DIV`, `CONFIG`, `GYRO_CONFIG`, and `ACCEL_CONFIG` read back the expected Phase 3.2D values.
- Capture live acceleration, angular-rate, and temperature JSONL telemetry.
- Move the module gently and confirm raw values respond.
- Do not claim calibrated acceleration, gyro bias, yaw drift, axis orientation, odometry, or navigation.
- Record commit, date, operator, wiring revision, private serial-port identifier, expected result, observed result, pass/fail, notes, and evidence paths.

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

- TCRT5000 left OUT -> PH2.0-6P line-tracking connector signal channel 1 / X1 / PC4.
- TCRT5000 right OUT -> signal channel 2 / X2 / PC5.
- Hall sensor S after external divider -> signal channel 3 / X3 / PB0.
- The old shared-VCC plan is superseded by module-specific evidence: TCRT5000 modules should use 3.3 V and the Hall module should use 5 V. Common ground remains required.
- The old example maps signal 4 / X4 to PB1 while the schematic says PC14; signal 4 remains unused in Phase 3.2F.

Before use, verify connector orientation, exact pin order, supply rails, logic voltage, Hall output topology, common ground, and polarity.

## Phase 3.2B Manual Bring-Up Order

Do not mark these items complete automatically.

1. Preserve the committed BH1750-only physical evidence and repeat only if wiring or firmware changes.
2. Preserve the committed Phase 3.2C isolated BMP280 evidence and repeat only if wiring or firmware changes; shared-bus BMP280 operation with other I2C devices remains a separate validation.
3. Validate MPU6050 alone at 5 V with AD0 -> GND using the Phase 3.2D target; physical ACK, WHO_AM_I, configuration readback, live IMU telemetry, calibration, and axis orientation are not yet verified.
4. Validate all three I2C devices together without tying their VCC rails together.
5. Validate TCRT5000 raw inputs at 3.3 V.
6. Measure Hall `S` voltage in both magnetic states before STM32 input connection.
7. Validate each of the three HC-SR04 specimens sequentially on the single Phase 3.2E CN6 PA5/PA4 path, one at a time, only after installing and measuring the required external ECHO divider.
8. Keep simultaneous three-HC-SR04 integration blocked until the GPIO, connector, timer, independent-divider, trigger-staggering, power, and cross-talk plan for the other two paths is implemented and reviewed.
9. Validate USART2 electrical idle and loopback where safe.
10. Validate one C1 unit on USART2.
11. Validate USART3 loopback.
12. Validate ESP32-C3 link with USB disconnected from the ESP32 while OpenRF1 5 V is feeding it.
13. Validate C1-to-ESP32 data transport.
14. Perform full-system power and concurrency testing.

Record voltage levels, common ground, exact connector pins, observed raw states, pass/fail, and evidence paths for each step. Physical Phase 3.2B remains UNVERIFIED until this evidence exists.
