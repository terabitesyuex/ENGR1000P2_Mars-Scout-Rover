# Wiring

Electrical safety is the first project priority. Do not connect live hardware until voltage, polarity, connector orientation, and common ground are verified.

## Confirmed RPLIDAR C1 Wire Functions

| LiDAR wire | Function | Destination rule |
| --- | --- | --- |
| Red | VCC, 5 V | Independent regulated 5 V supply |
| Yellow | LiDAR TX | Receiver UART RX |
| Green | LiDAR RX | Transmitter UART TX |
| Black | GND | Controller and supply ground |
| Fifth position | Unused | Leave unused |

These wire functions preserve the verified C1 harness profile. They do not prove that either physical C1 is currently connected.

## Block-Level Inventory

- RPLIDAR C1 x2.
- HC-SR04 x3.
- TCRT5000 x2.
- BH1750 x1.
- BMP280 x1.
- MPU6050 x1.
- Hall sensor module x1.
- STM32 controller board x1.
- ESP32 board x1.
- Battery/power system.
- Four encoded motors.
- Four mecanum wheels.

## RPLIDAR C1 Rules

- Red VCC must use a regulated 5 V supply, not ESP32 3.3 V.
- Yellow LiDAR TX goes to a verified receiver UART RX.
- Green LiDAR RX goes to a verified transmitter UART TX.
- Black GND must share common ground with the controller and supply.
- Do not connect LiDAR TX to TX or LiDAR RX to RX.
- Do not drive LiDAR RX from a USB adapter and ESP32 at the same time.
- Dual-C1 ESP32 wiring is UNVERIFIED.
- ESP32-C3 GPIO21/GPIO20 are CONFIRMED_MODULE_EVIDENCE for the proposed module-side UART pins; OpenRF1 USART3 connector-to-MCU mapping remains UNVERIFIED.
- Exact UART assignment is UNVERIFIED.

## Power Rules

- Use a regulated 5 V supply capable of startup current margin for each connected C1.
- Preserve the verified C1 supply range of 4.8 V to 5.2 V.
- Keep specified supply ripple below 150 mV.
- Keep motor power wiring away from UART and low-level sensor wiring.
- Final power-distribution topology is UNVERIFIED.
- Battery voltage and capacity are UNVERIFIED unless measured.

## STM32 Sensor Wiring Status

- HC-SR04 logic-level interface on the physical STM32 board is UNVERIFIED.
- HC-SR04 Echo level protection is conditional on module supply and measured Echo VOH; direct connection is not approved until measured or the exact MCU pin tolerance is established.
- TCRT5000 active polarity is UNVERIFIED.
- Hall active polarity is UNVERIFIED.
- Phase 3.2A BH1750 target board is OpenRF1 with STM32F103RCT6.
- OpenRF1 software I2C SCL is PB1/SCL and SDA is PC3/SDA.
- The OpenRF1 schematic includes 10 kOhm pull-ups from PB1/SCL and PC3/SDA to 3.3 V.
- The OpenRF1 2x4 I2C header duplicates PC3/SDA, PB1/SCL, GND, and 5V rows.
- The adjacent SWD connector must not be confused with the I2C header.
- Recorded Phase 3.2A manual evidence verifies BH1750 communication at configured public 7-bit address `0x23`, 500 ms telemetry, and physical light response; absolute lux calibration remains UNVERIFIED.
- BMP280 I2C address is PHYSICAL_EVIDENCE_VERIFIED at `0x76` for the isolated Phase 3.2C BMP280-only capture; shared-bus operation remains UNVERIFIED.
- MPU6050 I2C address is planned as `0x68` with AD0 -> GND for Phase 3.2D software bring-up; physical ACK, WHO_AM_I, configuration readback, and live telemetry remain UNVERIFIED.
- Final sensor mounting offsets are UNVERIFIED.

## Phase 3.2A GY-302/BH1750 Wiring

This wiring is MANUAL_EVIDENCE_VERIFIED for the recorded BH1750-only bring-up with baseline firmware. The GY-302 module has CONFIRMED_MODULE_EVIDENCE for onboard 3.3 V regulation, logic-level conversion, module-level 3-5 V supply compatibility, and I2C pull-ups on the regulated logic rail. Distinguish those module facts from the bare BH1750 IC limit.

| GY-302 pin | OpenRF1 connection |
| --- | --- |
| VCC | OpenRF1 I2C 5V |
| GND | OpenRF1 I2C GND |
| SCL | OpenRF1 PB1/SCL |
| SDA | OpenRF1 PC3/SDA |
| ADDR | OpenRF1 GND |

Power off before changing wiring. First power-on or repeat validation should be performed without motors and without additional new sensors. The recorded evidence verifies configured-address communication and controlled light response for this exact setup, but it does not prove laboratory lux calibration.

## Phase 3.2B Proposed Full-Hardware Wiring

The following is a hardware-team proposal for future validation, not verified truth.

### ESP32-C3 SuperMini

- ESP32 5V -> OpenRF1 Bluetooth UART 5V during non-USB operation.
- ESP32 GND -> OpenRF1 Bluetooth UART GND.
- ESP32 GPIO21 TX -> OpenRF1 RX3.
- ESP32 GPIO20 RX <- OpenRF1 TX3.

Software intent: STM32 USART3 communicates with ESP32. USART3 is not the debug console. USART1 remains dedicated to CH340/debug telemetry. ESP32-C3 UART logic is 3.3 V, so no STM32-to-ESP32 UART level shifter is required for the proposed link.

Mandatory power rule: external 5 V power and USB power must not be connected simultaneously on the ESP32-C3 SuperMini. Disconnect the STM32/OpenRF1 5 V feed before plugging the ESP32 into USB. A removable jumper or switch in the ESP32 5 V wire is recommended as an integration aid, not a software requirement.

### RPLIDAR C1

- C1 VCC -> OpenRF1 user UART 5V.
- C1 GND -> OpenRF1 user UART GND.
- C1 TX -> OpenRF1 RX2.
- C1 RX <- OpenRF1 TX2.

C1 transport target: 3.3 V TTL UART, 460800 baud, 8 data bits, no parity, 1 stop bit. Do not trust wire colors alone; verify signal identity from adapter-board labels or continuity testing.

### Shared Software I2C

Known board bus:

- PB1 = SCL.
- PC3 = SDA.

Proposed power and straps:

- GY-302/BH1750 VCC -> OpenRF1 5 V, ADDR -> GND, address `0x23`.
- GY-521/MPU6050 VCC -> OpenRF1 5 V, AD0 -> GND, address `0x68`; INT, XDA, and XCL remain disconnected for polling.
- BMP280-3.3 VCC -> OpenRF1 3.3 V, CSB -> 3.3 V for I2C mode, SDO -> GND, address `0x76`.

Do not tie all I2C module VCC pins together. All grounds are common, SCL is common, and SDA is common. Do not add external I2C pull-ups by default because the OpenRF1 board and modules already contain pull-ups; inspect parallel pull-up strength during physical bus testing if communication becomes unreliable.

The BMP280-3.3 module must not connect to the I2C connector 5 V pin. No external level shifter is needed when the BMP280 module and I2C pull-ups operate at 3.3 V.

## Phase 3.2C BMP280-Only Bring-Up Wiring

This is the isolated Phase 3.2C bench target, not the full Phase 3.2B shared-bus integration. Connect only the BMP280 module:

| BMP280 pin | OpenRF1 connection | Status |
| --- | --- | --- |
| VCC | 3.3 V | CONFIRMED_MODULE_EVIDENCE for BMP280-3.3 supply rule |
| GND | GND | PHYSICAL_EVIDENCE_VERIFIED for isolated capture |
| SCL | PB1 / connector B1 | CONFIRMED OpenRF1 software-I2C signal |
| SDA | PC3 / connector C3 | CONFIRMED OpenRF1 software-I2C signal |
| CSB | 3.3 V | PHYSICAL_EVIDENCE_VERIFIED I2C-mode strap for isolated capture |
| SDO | GND | PHYSICAL_EVIDENCE_VERIFIED address strap for `0x76` in isolated capture |

Committed Phase 3.2C evidence verifies ACK at `0x76`, chip ID `0x58`, calibration-register path sufficient for compensated output, `ctrl_meas = 0x27` and `config = 0x80` readback, live compensated temperature/pressure telemetry, exact 500 ms periodicity, and a stable 30-second BMP280-only capture. Absolute temperature/pressure accuracy, environmental-reference comparison, long-duration operation, and shared-I2C concurrency remain UNVERIFIED.

## Phase 3.2D MPU6050-Only Bring-Up Wiring

This is the isolated Phase 3.2D software-prepared bench target, not the full Phase 3.2B shared-bus integration. Connect only the GY-521/MPU6050 module during the future manual test:

| GY-521/MPU6050 pin | OpenRF1 connection | Status |
| --- | --- | --- |
| VCC | 5 V | CONFIRMED_MODULE_EVIDENCE for GY-521/MPU6050 module capability; PHYSICAL_VERIFICATION_REQUIRED for this setup |
| GND | GND | PLANNED; PHYSICAL_VERIFICATION_REQUIRED |
| SCL | PB1 / connector B1 | CONFIRMED OpenRF1 software-I2C signal |
| SDA | PC3 / connector C3 | CONFIRMED OpenRF1 software-I2C signal |
| AD0 | GND | PLANNED for address `0x68`; PHYSICAL_VERIFICATION_REQUIRED |
| INT | disconnected | PLANNED polling bring-up |
| XDA/XCL | disconnected | PLANNED polling bring-up |
| FSYNC | disconnected | PLANNED polling bring-up |

Phase 3.2D repository automation verifies only source structure and pure software behavior. MPU6050 ACK, WHO_AM_I `0x68`, configuration readback, live acceleration/angular-rate/temperature telemetry, calibration, axis orientation, shared-I2C concurrency, and full-hardware operation remain UNVERIFIED.

### HC-SR04

Proposed logical allocation:

- `ultrasonic_1` front: Trig -> PWM channel 0, Echo -> PWM channel 1.
- `ultrasonic_2` left: Trig -> PWM channel 2, Echo -> PWM channel 3.
- `ultrasonic_3` right: Trig -> PWM channel 4, Echo -> PWM channel 5.

Preferred first test: power one wide-voltage HC-SR04 from the OpenRF1 3.3 V output, do not use the PWM servo-interface + rail, and connect only Trig/Echo to the selected PWM-channel signal pins. Measure Echo high voltage before direct STM32 connection. If Echo high is at or below the 3.3 V rail, no divider is required for that measured setup. If Echo exceeds safe STM32 input voltage, or if the module is powered from 5 V, add a divider or level shifter. Never infer safety only from the STM32 family name. Do not claim the full 450 cm range at 3.3 V until physically tested.

### TCRT5000 And Hall

Proposed logical allocation:

- `tcrt5000_1` VCC -> OpenRF1 3.3 V.
- `tcrt5000_2` VCC -> OpenRF1 3.3 V.
- `tcrt5000_1` OUT -> line input signal 1.
- `tcrt5000_2` OUT -> line input signal 2.
- Hall `+` -> OpenRF1 5 V.
- Hall `-` -> OpenRF1 GND.
- `hall_1` S -> line input signal 3.

TCRT5000 modules use 3.3 V for first integration to avoid a possible 5 V output-high level. If powered from 5 V later, output voltage or MCU-pin 5 V tolerance must first be verified.

Hall `S` must not be declared safe for direct STM32 connection yet. First measure Hall `S` voltage in both magnetic states. Use a divider if the module produces an approximately 5 V high state, use a 3.3 V pull-up if the output is open collector without onboard 5 V pull-up, or approve direct input only after recorded evidence shows the signal is already within 3.3 V logic range.

Actual STM32 GPIO pins and active polarity remain UNVERIFIED. Preserve raw digital states until physical tests establish polarity.

## User-Confirmed Planned Ground/Landmark Connector

This plan is USER-CONFIRMED PLANNED CONNECTION, not electrically tested hardware evidence:

- Two TCRT5000 modules and one Hall sensor are planned to use the STM32 PH2.0-6P four-channel line-tracking connector.
- TCRT5000 left OUT -> signal channel 1.
- TCRT5000 right OUT -> signal channel 2.
- Hall sensor S -> signal channel 3.
- The old shared-VCC plan is superseded by module-specific evidence: TCRT5000 modules should use 3.3 V and the Hall module should use 5 V. If the PH2.0-6P connector exposes only one VCC rail, it cannot safely power both module types under the revised proposal without additional measured evidence or separate power routing.

Connector orientation, exact pin order, supply voltage, logic voltage, Hall output topology, active polarity, and pull configuration remain UNVERIFIED.

## Future Verification Checklist

- Verify supply voltage and polarity before attaching each module.
- Verify common ground.
- Verify connector orientation.
- Verify current margin under motor load.
- Verify each C1 independently before any dual-C1 wiring.
- Verify STM32-ESP32 physical link before relying on transferred sensor data.
- Label each neutral sensor ID after installation evidence exists.
