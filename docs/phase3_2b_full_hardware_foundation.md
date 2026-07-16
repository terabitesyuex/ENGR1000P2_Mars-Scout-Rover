# Phase 3.2B OpenRF1 Multisensor And Communications Foundation

Phase 3.2B is a software-only foundation for the proposed full OpenRF1 sensor and communications wiring. It does not flash hardware, open COM ports, read USB devices, or prove any physical wiring.

Manual warning:

> Software foundation and Keil builds are VERIFIED only when the automated tests and both Keil builds pass; physical wiring, power integrity, voltage levels, USART2/USART3 operation, I2C ACKs, sensor polarity, ultrasonic timing, RPLIDAR transport, ESP32 link, and real sensor data remain UNVERIFIED.

## Status Labels

- CONFIRMED: supported by repository/manual/schematic evidence.
- SOFTWARE_VERIFIED: validated by automated tests or a successful local build.
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
| ESP32-C3 TX/RX | ESP32 GPIO21 TX -> OpenRF1 RX3, GPIO20 RX <- TX3 | USART3 link contract exists | UNVERIFIED |
| RPLIDAR C1 | C1 TX -> OpenRF1 RX2, C1 RX <- TX2 | USART2 byte transport exists | UNVERIFIED |
| Shared I2C | PB1/SCL, PC3/SDA | CONFIRMED pins reused | ACKs UNVERIFIED |
| HC-SR04 | PWM channels 0/1, 2/3, 4/5 as trig/echo pairs | nonblocking state machine exists | MCU pins and level shifting UNVERIFIED |
| TCRT5000/Hall | line input signals 1, 2, 3 | raw/debounced state model exists | MCU pins and polarity UNVERIFIED |

Do not infer MCU pins from connector order or channel numbers. Authoritative schematic/manual evidence is required before moving unresolved mappings into `board_config.h`.

## I2C Addresses And Straps

| Device | Strap requirement | 7-bit address in software | Status |
| --- | --- | --- | --- |
| GY-302/BH1750 | ADDR -> GND | `0x23` | PLANNED, ACK UNVERIFIED |
| GY-521/MPU6050 | AD0 -> GND; INT disconnected for polling foundation | `0x68` provisional | UNVERIFIED |
| HW-611/BMP280 | CSB -> VDDIO for I2C mode; SDO -> GND | `0x76` provisional | UNVERIFIED |

Module supply compatibility is MANUAL_ACTION_REQUIRED until each breakout board circuit is inspected. Do not state unresolved module supplies as final 5 V or 3.3 V facts.

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
- PWM channel 0 through 5 MCU GPIO/timer mappings.
- line input signal 1 through 3 MCU GPIO mappings.
- HC-SR04 echo electrical protection path.
- TCRT5000 and Hall active polarity.

## Electrical Safety Notes

- HC-SR04 Echo may be 5 V and requires an external divider or suitable level shifter before STM32 input unless board-level protection is proven.
- PWM servo supply jumper must be set to 5 V, not 6.5 V, before powering HC-SR04 modules from that rail.
- BMP280 chip voltage limits differ from breakout-board input claims; exact HW-611 supply compatibility is MANUAL_ACTION_REQUIRED.
- I2C pull-up rail must be checked before attaching modules.
- ESP32-C3 logic is 3.3 V.
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

## Incremental Bring-Up Order

1. Preserve and complete BH1750-only physical validation.
2. Validate BMP280 alone on the shared I2C bus.
3. Validate MPU6050 alone.
4. Validate all three I2C devices together.
5. Validate TCRT5000 raw inputs.
6. Validate Hall raw input.
7. Validate one HC-SR04 with level shifting.
8. Validate all three HC-SR04 modules with staggered triggering.
9. Validate USART2 electrical idle and loopback where safe.
10. Validate one C1 unit on USART2.
11. Validate USART3 loopback.
12. Validate ESP32-C3 link.
13. Validate C1-to-ESP32 data transport.
14. Perform full-system power and concurrency testing.

## Troubleshooting

- No I2C ACK: power off, confirm straps, check SDA/SCL orientation, verify pull-up rail and common ground.
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
