# Phase 3.2B OpenRF1 Multisensor And Communications Foundation

Phase 3.2B is a software-only foundation for the proposed full OpenRF1 sensor and communications wiring. It does not flash hardware, open COM ports, read USB devices, or prove any physical wiring.

Manual warning:

> Software foundation and Keil builds are SOFTWARE_VERIFIED only when the automated tests and both Keil builds pass. Recorded manual evidence verifies the Phase 3.2A BH1750-only flash, CH340/USART1 telemetry, configured `0x23` BH1750 communication, 500 ms telemetry period, and physical light response. All other real multisensor wiring, power integrity, voltage levels, USART2/USART3 operation, BMP280/MPU6050 ACKs, sensor polarity, ultrasonic timing, RPLIDAR transport, ESP32 link, concurrent operation, and real full-system sensor data remain UNVERIFIED.

## Status Labels

- CONFIRMED: supported by repository/manual/schematic evidence.
- CONFIRMED_MODULE_EVIDENCE: supported by supplied module-specific documentation or schematic evidence, but not necessarily validated in the rover wiring.
- SOFTWARE_VERIFIED: validated by automated tests or a successful local build.
- MANUAL_EVIDENCE_VERIFIED: supported by recorded manual evidence; automation may validate the committed evidence file but did not perform the physical action.
- MANUAL_ACTION_REQUIRED: requires a person to perform a physical step.
- UNVERIFIED: not yet demonstrated.
- BLOCKED: cannot proceed safely without missing evidence.

## Scope

Implemented software foundations:

- Isolated full-hardware firmware source under `firmware/openrf1/full_hardware/`.
- Separate Keil project `firmware/openrf1/keil/OpenRF1_FullHardware.uvprojx`.
- Separate output directory `firmware/openrf1/keil/Objects_FullHardware/`.
- Feature flags for BH1750, BMP280, MPU6050, ultrasonic, ground sensors, Hall, RPLIDAR C1 transport, and ESP32 link.
- Bounded software-I2C wrapper with 7-bit addresses and error status propagation.
- BMP280 chip ID/calibration/raw-read/compensation foundation.
- MPU6050 WHO_AM_I/raw-read/conversion foundation.
- Raw digital filtering for TCRT5000 and Hall without assumed active polarity.
- Nonblocking HC-SR04 state machine with timeout and quiet time.
- Bounded RPLIDAR C1 byte transport and counters.
- Versioned STM32-to-ESP32 binary frame codec contract.
- PC parser, simulator, recording bridge, and deterministic tests for new message types.

Out of scope:

- Firmware flashing.
- Hardware ACK/read validation.
- ESP32 WiFi firmware.
- Motor, encoder, mecanum, navigation, SLAM, mapping, or obstacle-avoidance decisions.
- RPLIDAR packet parsing beyond byte transport.

## Layering

```text
firmware/openrf1/full_hardware/
  board_config.h                 board constants, feature flags, unresolved mappings
  platform_full_hardware.c/.h     SysTick and bounded USART1 debug output
  scheduler.c/.h                  cooperative deadline scheduler
  i2c_bus.c/.h                    shared software-I2C transaction wrapper
  bmp280.c/.h                     BMP280 foundation
  mpu6050.c/.h                    MPU6050 foundation
  digital_filter.c/.h             raw/filtered digital-state logic
  ground_sensors.c/.h             TCRT5000 raw state holders
  hall_sensor.c/.h                Hall raw state holder
  hcsr04.c/.h                     HC-SR04 state machine
  uart_ring_buffer.c/.h           bounded power-of-two byte buffers
  rplidar_c1_transport.c/.h       USART2 byte-transport foundation
  esp32_link.c/.h                 frame encoding and link counters
  telemetry_full.c/.h             bounded status JSONL formatting for debug
  main_full_hardware.c            cooperative application entry point
```

## Candidate Wiring And Evidence Table

| Interface | Proposal | Software status | Physical status |
| --- | --- | --- | --- |
| GY-302/BH1750 | VCC -> OpenRF1 5 V I2C supply, GND common, SCL PB1, SDA PC3, ADDR -> GND | address `0x23`; 500 ms telemetry path exists | MANUAL_EVIDENCE_VERIFIED for BH1750-only bring-up; absolute lux calibration UNVERIFIED |
| GY-521/MPU6050 | VCC -> OpenRF1 5 V, GND common, SCL/SDA shared, AD0 -> GND, INT/XDA/XCL disconnected | raw-read/conversion foundation exists | MANUAL_EVIDENCE_VERIFIED for isolated ACK/address `0x68`, WHO_AM_I, configuration readback, live telemetry, startup bias, and axis response; shared-bus operation UNVERIFIED |
| BMP280-3.3 | VCC -> OpenRF1 3.3 V, GND common, SCL/SDA shared, CSB -> 3.3 V, SDO -> GND | chip-ID/raw/calibration/compensation foundation exists | MANUAL_EVIDENCE_VERIFIED for isolated ACK `0x76`, chip ID `0x58`, configuration, compensated telemetry, and 30-second capture; accuracy/shared bus UNVERIFIED |
| Shared I2C signals | PB1/SCL and PC3/SDA shared across BH1750, MPU6050, and BMP280; module VCC rails are not tied together | CONFIRMED pins reused | Each module has isolated evidence; concurrent shared-I2C operation remains UNVERIFIED |
| ESP32-C3 TX/RX | ESP32 GPIO21 TX -> OpenRF1 RX3, GPIO20 RX <- TX3, ESP32 5 V input during non-USB operation | USART3 link contract exists | ESP32 module pins CONFIRMED_MODULE_EVIDENCE; OpenRF1 RX3/TX3 pins and real link UNVERIFIED |
| RPLIDAR C1 | Exactly one physical `c1_1`; planned C1 TX -> OpenRF1 RX2, C1 RX <- TX2 | USART2 byte transport exists | Physical C1 acceptance and OpenRF1 transport UNVERIFIED; no second physical C1 |
| HC-SR04 | Phase 3.2E supersedes the initial 3.3 V proposal for the isolated CN6 baseline: CN6 pin 1: VCC_5V, pin 2: GND, pin 3: PA5_TRIG, pin 4: PA4_ECHO | nonblocking state machine exists; isolated Phase 3.2E target adds PA5/PA4/TIM6 software | AUTHORITATIVE_VENDOR_DOCUMENTED for CN6/PA5/PA4/TIM6; physical wiring and Echo voltage UNVERIFIED |
| TCRT5000 | VCC -> OpenRF1 3.3 V, GND common, OUT -> signal 1 / X1 / PC4 and signal 2 / X2 / PC5 | Phase 3.2F adds isolated 5 ms sampling, 20 ms debounce, and 50 ms JSONL telemetry | MANUAL_EVIDENCE_VERIFIED for isolated PC4/PC5 connections, live response, and four 100-frame captures; measured voltages, polarity, black/white/drop semantics, and full hardware UNVERIFIED |
| Hall | `+` -> OpenRF1 5 V, `-` -> GND, `S` -> external 10 kOhm / 15 kOhm divider -> signal 3 / X3 / PB0 | Phase 3.2F adds isolated raw/debounced Hall level telemetry without semantic polarity | AUTHORITATIVE_VENDOR_DOCUMENTED for X3/PB0 and connector pin order; installed divider, divided voltage, output topology, and polarity UNVERIFIED |

Earlier Phase 3.2B planning did not infer unresolved line-input MCU pins from channel numbers. Phase 3.2F adds vendor-documented mappings and isolated manual evidence for installed TCRT PC4/PC5 connections. Hall wiring, measured voltages, polarity semantics, and full-hardware operation remain UNVERIFIED.

## I2C Addresses And Straps

| Device | Strap requirement | 7-bit address in software | Status |
| --- | --- | --- | --- |
| GY-302/BH1750 | ADDR -> GND | `0x23` | MANUAL_EVIDENCE_VERIFIED for Phase 3.2A BH1750-only bring-up |
| GY-521/MPU6050 | AD0 -> GND for deterministic `0x68`; INT, XDA, and XCL disconnected for polling foundation | `0x68` provisional | CONFIRMED_MODULE_EVIDENCE for module default; real ACK UNVERIFIED |
| BMP280-3.3 | CSB -> 3.3 V for I2C mode; SDO -> GND | `0x76` provisional | CONFIRMED_MODULE_EVIDENCE for strap plan; real ACK UNVERIFIED |

Do not tie all I2C module VCC pins together. Correct proposed power is BH1750 VCC -> 5 V, MPU6050 VCC -> 5 V, BMP280 VCC -> 3.3 V, all grounds common, SCL common, and SDA common. No external I2C pull-ups are added by default because the OpenRF1 board and modules already include pull-ups; inspect parallel pull-up strength during physical bus testing if communication becomes unreliable.

## Revised Power Domains

| Domain | Modules | Status |
| --- | --- | --- |
| 5 V | GY-302/BH1750 module, GY-521/MPU6050 module, ESP32-C3 5 V input during non-USB operation, RPLIDAR C1, Hall module | BH1750 manually verified; other devices require per-module bring-up |
| 3.3 V | BMP280-3.3, two TCRT5000 modules, STM32/ESP32 UART logic, I2C signal pull-up rail | CONFIRMED_MODULE_EVIDENCE where listed; measurements still required |
| Common ground | all modules | MANUAL_ACTION_REQUIRED before each physical test |

The OpenRF1 board exposes a 3.3 V sensor/output rail, so no separate regulator is currently required for the BMP280/TCRT5000 proposal. Phase 3.2E uses the vendor-documented CN6 VCC_5V HC-SR04 path and requires the external 10 kOhm / 15 kOhm ECHO divider before PA4. Total current budget, regulator temperature, noise, brownout behavior, motor interference, and full-system concurrency remain MANUAL_ACTION_REQUIRED.

## UART Allocation

| UART | Use | Baud | Status |
| --- | --- | --- | --- |
| USART1 PA9/PA10 | CH340 debug/bring-up telemetry | 115200 8N1 | CONFIRMED for Phase 3.2A |
| USART2 | RPLIDAR C1 byte transport | 460800 8N1 | connector pins UNVERIFIED |
| USART3 | ESP32-C3 STM32-side link | 921600 provisional | connector pins and baud UNVERIFIED |

USART1 must not carry high-rate lidar payload. It is retained for bounded debug/status output.

## Feature Flags

The full-hardware build defines:

- `OPENRF1_ENABLE_BH1750`
- `OPENRF1_ENABLE_BMP280`
- `OPENRF1_ENABLE_MPU6050`
- `OPENRF1_ENABLE_ULTRASONIC`
- `OPENRF1_ENABLE_GROUND_SENSORS`
- `OPENRF1_ENABLE_HALL`
- `OPENRF1_ENABLE_RPLIDAR_C1`
- `OPENRF1_ENABLE_ESP32_LINK`

The foundation is cooperative and bounded so a missing sensor can report status without freezing startup.

## Scheduler Rates

| Task | Provisional period | Notes |
| --- | --- | --- |
| Ground and Hall | 10 ms | 100 Hz raw/debounced state sampling |
| MPU6050 raw | 10 ms | 100 Hz polling foundation |
| BMP280 | 100 ms | 10 Hz environmental foundation |
| BH1750 | 500 ms | approximately 2 Hz, preserving Phase 3.2A behavior |
| Ultrasonic scheduler | 2 ms service tick | one channel active at a time |
| Status/health | 1000 ms | bounded USART1 debug/status |

## Static Memory Budget

STM32F103RCT6 budget: 256 KB flash, 48 KB SRAM.

Software-defined static buffers:

| Buffer | Bytes |
| --- | ---: |
| RPLIDAR RX ring | 2048 |
| ESP32 RX ring | 512 |
| ESP32 TX ring | 512 |
| Debug/status telemetry buffer | 320 |
| Misc state allowance | 512 |
| Estimated total | 3904 |

Compile-time assertions keep ring buffers power-of-two and the estimated static SRAM footprint below 8192 bytes, leaving margin for later motor/control work. No `malloc`, `free`, recursion, or large stack buffers are used in the Phase 3.2B firmware source.

## Pin Mapping Status

CONFIRMED by repository evidence:

- Software I2C SCL: PB1.
- Software I2C SDA: PC3.
- USART1 debug TX/RX: PA9/PA10.
- USART1 debug: 115200 baud, 8N1.

Still UNVERIFIED:

- OpenRF1 USART2 user-UART MCU pins and DMA/interrupt channel details.
- OpenRF1 USART3 Bluetooth-UART MCU pins and DMA/interrupt channel details.
- PWM channel 0 through 5 MCU GPIO/timer mappings beyond the Phase 3.2E CN6 PA5/PA4 isolated baseline.
- final line-input connector/cable orientation, TCRT output voltages, Hall installation/divider values, Hall divided voltage, and active polarity.
- Physical HC-SR04 ECHO voltage before/after the required external Phase 3.2E divider.
- TCRT5000 and Hall active polarity.

## Electrical Safety Notes

- The GY-302/BH1750 module has CONFIRMED_MODULE_EVIDENCE for onboard 3.3 V regulation, logic-level conversion, module-level 3-5 V supply compatibility, and I2C pull-ups on the regulated logic rail. For this exact module, GY-302 VCC -> OpenRF1 5 V is accepted and no external regulator or I2C level shifter is required. ADDR -> GND remains required for configured address `0x23`.
- The GY-521/MPU6050 module has CONFIRMED_MODULE_EVIDENCE for 3.3 V or 5 V VCC, onboard 3.3 V regulation, SCL/SDA pull-ups to onboard 3.3 V, and AD0 pull-down. Use explicit AD0 -> GND for deterministic `0x68`; INT, XDA, and XCL remain disconnected in the polling foundation.
- The BMP280-3.3 module is a 3.3 V-only style board. BMP280 VCC must connect to OpenRF1 3.3 V and must not connect to the I2C connector 5 V pin. CSB -> 3.3 V selects I2C mode and SDO -> GND selects `0x76`. No external level shifter is needed when this module and the I2C pull-ups operate at 3.3 V.
- Phase 3.2E locks the OpenRF1 CN6 HC-SR04 path from vendor material: CN6 pin 1: VCC_5V, pin 2: GND, pin 3: PA5_TRIG, pin 4: PA4_ECHO, with TIM6 for isolated timing. Do not connect HC-SR04 ECHO directly to CN6 pin 4. Install the external 10 kOhm / 15 kOhm divider before PA4 receives the signal. Physical connector orientation, resistor installation, ECHO voltage, trigger pulse, echo pulse, and real distance data remain UNVERIFIED.
- TCRT5000 modules should be powered from 3.3 V for first integration so OUT cannot become a 5 V high from module supply. If later powered from 5 V, output voltage or MCU-pin 5 V tolerance must first be verified.
- Phase 3.2F requires the Hall module to use 5 V with Hall `S` routed through an external 10 kOhm / 15 kOhm divider before PB0. Hall `S` must not be declared safe for direct STM32 connection. Do not connect Hall `S` directly to PB0. Future manual bring-up must measure Hall `S` voltage in both magnetic states and must measure the divided PB0 voltage before connection. Installed resistor values, Hall output voltage, divided PB0 voltage, output topology, and polarity remain UNVERIFIED until recorded evidence exists.
- ESP32-C3 UART logic is 3.3 V, so no STM32-to-ESP32 UART level shifter is required for the proposed link. External 5 V power and USB power must not be connected simultaneously; disconnect the STM32/OpenRF1 5 V feed before plugging the ESP32 into USB. A removable jumper or switch in the ESP32 5 V wire is recommended as an integration aid.
- C1 signal identity must be verified from adapter-board labels or continuity testing, not wire color alone.
- Complete system power must not rely on an undersized USB supply.
- All modules require a common ground.
- Initial tests should keep motors and servos disconnected.

## Keil Build Procedure

Baseline Phase 3.2A build:

```powershell
& "$env:USERPROFILE\AppData\Local\Keil_v5\UV4\UV4.exe" -b firmware\openrf1\keil\OpenRF1_BH1750.uvprojx
```

Full-hardware Phase 3.2B build:

```powershell
& "$env:USERPROFILE\AppData\Local\Keil_v5\UV4\UV4.exe" -b firmware\openrf1\keil\OpenRF1_FullHardware.uvprojx
```

The full-hardware project must emit `Objects_FullHardware/OpenRF1_FullHardware.hex` and must not overwrite `Objects/OpenRF1_BH1750.hex`.

Isolated Phase 3.2D MPU6050 build:

```powershell
& "$env:USERPROFILE\AppData\Local\Keil_v5\UV4\UV4.exe" -b firmware\openrf1\keil\OpenRF1_MPU6050_Bringup.uvprojx
```

The MPU6050 bring-up project must emit `Objects_MPU6050_Bringup/OpenRF1_MPU6050_Bringup.hex` and must not overwrite the BH1750, BMP280, or full-hardware outputs. Building is software evidence only; flashing and sensor validation remain manual.

## Incremental Bring-Up Order

1. Preserve the recorded BH1750-only physical evidence and repeat only if wiring changes.
2. Validate BMP280 alone at 3.3 V on the shared I2C signal bus.
3. Validate MPU6050 alone at 5 V with AD0 -> GND using the Phase 3.2D target.
4. Validate all three I2C devices together without tying their VCC rails together.
5. Validate TCRT5000 raw inputs at 3.3 V.
6. Measure Hall `S` voltage in both magnetic states before connecting it to an STM32 input.
7. Validate one HC-SR04 on the Phase 3.2E CN6 PA5/PA4 path only after installing and measuring the required external ECHO divider.
8. Validate all three HC-SR04 modules with staggered triggering.
9. Validate USART2 electrical idle and loopback where safe.
10. Validate one C1 unit on USART2.
11. Validate USART3 loopback.
12. Validate ESP32-C3 link with USB disconnected from the ESP32 while OpenRF1 5 V is feeding it.
13. Validate C1-to-ESP32 data transport.
14. Perform full-system power and concurrency testing.

## Troubleshooting

- No I2C ACK: power off, confirm straps, check SDA/SCL orientation, verify module-specific VCC rail, inspect pull-up strength if needed, and confirm common ground.
- BMP280 bad chip ID: stop and record the observed ID; do not treat it as a valid BMP280 reading.
- MPU6050 bad WHO_AM_I: stop and record the observed value; do not fabricate calibration.
- Ultrasonic timeout: preserve `valid: false`; do not convert timeout into zero distance.
- TCRT5000/Hall unexpected states: record raw and filtered states; do not infer polarity.
- RPLIDAR overflow: reduce forwarded chunk rate or increase downstream baud after measuring bandwidth.
- ESP32 CRC errors: preserve counters and inspect the binary frame stream before changing baud.
- Malformed JSON on USART1: keep raw logs and check that high-rate payload is not being printed through debug.

## Verification

Software verification:

```powershell
.\tools\verify_phase.cmd phase3.2b -AllowDirty
```

The verifier checks required files, targeted tests, regression tests, the complete PC suite, deterministic Phase 3.2B fixture generation/conversion/inspection, Keil build evidence, no absolute paths, no tracked generated Keil artifacts, and no real COM/USB/hardware access in automated tests.

## Manual Evidence Template

| Field | Value |
| --- | --- |
| Date | MANUAL_ACTION_REQUIRED |
| Operator | MANUAL_ACTION_REQUIRED |
| Commit | MANUAL_ACTION_REQUIRED |
| Board revision | MANUAL_ACTION_REQUIRED |
| Sensor/link under test | MANUAL_ACTION_REQUIRED |
| Wiring revision | MANUAL_ACTION_REQUIRED |
| Power source and measured voltage | MANUAL_ACTION_REQUIRED |
| Expected result | MANUAL_ACTION_REQUIRED |
| Observed result | MANUAL_ACTION_REQUIRED |
| Pass/fail | MANUAL_ACTION_REQUIRED |
| Evidence path | MANUAL_ACTION_REQUIRED |
