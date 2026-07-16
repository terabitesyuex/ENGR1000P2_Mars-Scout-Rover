# OpenRF1 BH1750 Bring-Up Procedure

Phase 3.2A prepares software for one GY-302/BH1750 sensor on the OpenRF1 STM32F103RCT6 controller. This procedure is manual. Do not mark any result verified until evidence is recorded.

## Confirmed Configuration

| Item | Value | Status |
| --- | --- | --- |
| Board | OpenRF1 robot controller | CONFIRMED |
| MCU | STM32F103RCT6, 64 pins, Cortex-M3, 256 KB flash, 48 KB SRAM | CONFIRMED |
| Vendor toolchain | Keil MDK/uVision 5 | CONFIRMED intended toolchain |
| Vendor target | STM32F103RC | CONFIRMED |
| Vendor defines | `STM32F10X_HD`, `USE_STDPERIPH_DRIVER` | CONFIRMED |
| Software I2C SCL | PB1 | CONFIRMED |
| Software I2C SDA | PC3 | CONFIRMED |
| Pull-ups | 10 kOhm to 3.3 V on PB1/SCL and PC3/SDA | CONFIRMED by schematic |
| I2C header supply | 5 V and GND | CONFIRMED by schematic |
| BH1750 module | GY-302 with VCC, GND, SCL, SDA, ADDR | CONFIRMED |
| BH1750 address | 7-bit `0x23` when ADDR is grounded | MANUAL_EVIDENCE_VERIFIED for recorded Phase 3.2A run |
| UART telemetry | USART1, PA9 TX, PA10 RX, 115200 baud, 8N1 | CONFIRMED reference |
| PC COM port | User-selected CH340 COM port; exact identifier kept private | MANUAL_EVIDENCE_VERIFIED for CH340/USART1 telemetry path |

## Wiring Table

| GY-302 pin | OpenRF1 connection |
| --- | --- |
| VCC | OpenRF1 I2C 5V |
| GND | OpenRF1 I2C GND |
| SCL | OpenRF1 PB1/SCL |
| SDA | OpenRF1 PC3/SDA |
| ADDR | OpenRF1 GND |

Exact wiring summary:

- GY-302 VCC -> OpenRF1 I2C 5V
- GY-302 GND -> OpenRF1 I2C GND
- GY-302 SCL -> OpenRF1 PB1/SCL
- GY-302 SDA -> OpenRF1 PC3/SDA
- GY-302 ADDR -> OpenRF1 GND

The OpenRF1 2x4 I2C header duplicates each signal row: PC3/SDA, PB1/SCL, GND, and 5V. Do not confuse this header with the adjacent SWD connector. Change wiring only while powered off.

Module electrical note:

- The bare BH1750 IC operates at approximately 2.4 V to 3.6 V.
- The specific GY-302 breakout has CONFIRMED_MODULE_EVIDENCE for onboard low-dropout 3.3 V regulation, onboard logic-level conversion, module-level 3 V to 5 V supply compatibility, and onboard I2C pull-ups on the regulated logic rail.
- GY-302 VCC -> OpenRF1 5 V is accepted for this exact module.
- No external regulator or I2C level shifter is required for this exact module.
- ADDR -> GND remains required for configured address `0x23`.

## Recorded Physical Evidence

The committed Phase 3.2A evidence file records a BH1750-only manual run using frozen firmware commit `ba2024b`.

MANUAL_EVIDENCE_VERIFIED:

- Firmware flash completed through FlyMcu on a user-verified CH340 port at 115200 baud.
- STM32 ROM bootloader version, device class, flash size, erase/program/execute result, and telemetry were recorded in sanitized form.
- Exactly 60 UTF-8 JSONL telemetry records were captured.
- All records use protocol `mars_scout_stm32_sensor_telemetry`, version `1`, message type `illuminance`, sensor ID `bh1750_1`, and status `ok`.
- Sequences are continuous from 769 through 828.
- Timestamps increase by exactly 500 ms.
- Recorded readings range from 0.00 lux when covered to 20.83 lux when illuminated.
- The readings respond strongly to physical cover and illumination.

Still UNVERIFIED:

- Absolute illuminance calibration.
- Long-duration stability.
- Behavior with additional I2C devices on the bus.
- Any BMP280, MPU6050, HC-SR04, TCRT5000, Hall, RPLIDAR, ESP32, motor, or full-system result.

Do not record the COM number, Windows username, absolute source path, or MCU unique serial number in tracked files.

## Manual Procedure

Before building, provide the three platform functions declared in `firmware/openrf1/app/main.h`: `openrf1_platform_init()`, `openrf1_millis()`, and `openrf1_usart1_write()`. If the vendor project already has its own `main()`, merge the Phase 3.2A initialization and polling loop into it instead of compiling a second `main()`.

1. Inspect all five GY-302 pins: VCC, GND, SCL, SDA, ADDR.
2. Turn OpenRF1 power off.
3. Connect VCC, GND, SCL, SDA, and ADDR according to the wiring table.
4. Check continuity and connector orientation before power is applied.
5. Keep motors and other new sensors disconnected.
6. Connect the OpenRF1 USB cable.
7. Identify the CH340 COM port in Windows Device Manager.
8. Build the STM32F103RC Keil project with the Phase 3.2A application files.
9. Flash by the documented USB ISP or SWD method.
10. Open serial at 115200 baud, 8 data bits, no parity, 1 stop bit.
11. Confirm valid `mars_scout_stm32_sensor_telemetry` version `1` JSONL output.
12. Confirm the sensor ACKs at 7-bit address `0x23`.
13. Record uncovered room-light readings.
14. Cover the sensor and confirm lux decreases strongly.
15. Shine a lamp indirectly and confirm lux increases.
16. Capture at least 30 seconds of telemetry.
17. Save raw telemetry and converted Phase 2.4 recording files.
18. Record commit, date, operator, wiring revision, COM port privately, expected result, observed result, pass/fail, and evidence paths.
19. Power off before disconnecting wiring.

## PC Capture Command

Manual capture requires the operator-selected COM port:

```powershell
python -m rplidar_c1_tools capture-stm32-serial --port <USER_VERIFIED_COM_PORT> --baud 115200 --duration 30 --telemetry-output bh1750_telemetry.jsonl --recording-output bh1750_recording.jsonl --overwrite
```

Automated tests and verifier smoke runs use `--mock-input` and do not open a real port.

## Failure Branches

No COM port:

- Stop the capture attempt.
- Confirm the CH340 driver appears in Device Manager.
- Do not invent a COM port.

Keil build failure:

- Record the exact build command, errors, and warnings.
- Confirm the target is STM32F103RC/F1 and the defines are `STM32F10X_HD` and `USE_STDPERIPH_DRIVER`.
- Do not flash.

Flash failure:

- Record the method used, error message, and board power state.
- Do not retry with unknown boot settings.

No ACK at `0x23`:

- Power off.
- Recheck ADDR to GND, SDA/SCL orientation, 5 V/GND, and common ground.
- The committed evidence verifies one successful configured-address run. For any new wiring, do not mark the address verified again until fresh ACK or valid telemetry evidence is recorded.

All-zero data:

- Confirm ACK first.
- Cover and uncover the sensor to distinguish valid dark readings from stuck data.
- Do not convert communication errors to zero lux.

Saturated data:

- Reduce incident light and re-test.
- Record whether readings remain saturated.

Malformed JSON:

- Keep the raw serial log as evidence.
- Confirm no debug text is mixed into the telemetry UART stream.

Decreasing timestamps:

- Stop the test and inspect the firmware millisecond tick source.

Unstable readings:

- Check wiring strain, pull-ups, power, and ambient-light changes.

SDA stuck low:

- Power off and disconnect the module before rechecking continuity.

SCL stuck low:

- Power off and inspect PB1/SCL wiring and connector orientation.
