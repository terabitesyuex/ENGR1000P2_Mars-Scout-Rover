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
- Exact ESP32 GPIOs are UNVERIFIED.
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
- HC-SR04 ECHO voltage compatibility with the STM32 input remains UNVERIFIED; do not connect ECHO directly until the exact board I/O voltage tolerance is verified.
- TCRT5000 active polarity is UNVERIFIED.
- Hall active polarity is UNVERIFIED.
- Phase 3.2A BH1750 target board is OpenRF1 with STM32F103RCT6.
- OpenRF1 software I2C SCL is PB1/SCL and SDA is PC3/SDA.
- The OpenRF1 schematic includes 10 kOhm pull-ups from PB1/SCL and PC3/SDA to 3.3 V.
- The OpenRF1 2x4 I2C header duplicates PC3/SDA, PB1/SCL, GND, and 5V rows.
- The adjacent SWD connector must not be confused with the I2C header.
- BH1750 public 7-bit address `0x23` is configured by the GY-302 ADDR-to-GND plan, but ACK at `0x23` is UNVERIFIED.
- BMP280 I2C address is UNVERIFIED.
- MPU6050 I2C address is UNVERIFIED.
- Final sensor mounting offsets are UNVERIFIED.

## Phase 3.2A GY-302/BH1750 Planned Wiring

This plan is USER-CONFIRMED, NOT ELECTRICALLY TESTED:

| GY-302 pin | OpenRF1 connection |
| --- | --- |
| VCC | OpenRF1 I2C 5V |
| GND | OpenRF1 I2C GND |
| SCL | OpenRF1 PB1/SCL |
| SDA | OpenRF1 PC3/SDA |
| ADDR | OpenRF1 GND |

Power off before changing wiring. First power-on should be performed without motors and without additional new sensors. Confirm address ACK at `0x23` and controlled lux response before marking readings verified.

## User-Confirmed Planned Ground/Landmark Connector

This plan is USER-CONFIRMED PLANNED CONNECTION, not electrically tested hardware evidence:

- Two TCRT5000 modules and one Hall sensor are planned to use the STM32 PH2.0-6P four-channel line-tracking connector.
- TCRT5000 left OUT -> signal channel 1.
- TCRT5000 right OUT -> signal channel 2.
- Hall sensor S -> signal channel 3.
- Shared VCC and GND on that connector are planned.

Connector orientation, exact pin order, supply voltage, logic voltage, active polarity, and pull configuration remain UNVERIFIED.

## Future Verification Checklist

- Verify supply voltage and polarity before attaching each module.
- Verify common ground.
- Verify connector orientation.
- Verify current margin under motor load.
- Verify each C1 independently before any dual-C1 wiring.
- Verify STM32-ESP32 physical link before relying on transferred sensor data.
- Label each neutral sensor ID after installation evidence exists.
