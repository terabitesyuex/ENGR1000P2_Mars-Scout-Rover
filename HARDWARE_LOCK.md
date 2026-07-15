# Hardware Lock

This file records hardware facts that must not drift silently. Unknown values remain explicit until physically verified.

## 2026-07-15 Inventory Update

The project inventory was rebaselined for Phase 2.4. This update adds newly confirmed available sensors and controller/chassis hardware while preserving earlier verified RPLIDAR C1 electrical facts.

## CONFIRMED INVENTORY

Ranging:

- RPLIDAR C1 x2.
- HC-SR04 ultrasonic sensor x3.

Motion and pose:

- Wheel encoders associated with the four drive motors.
- MPU6050 inertial measurement unit x1.

Ground and landmark:

- TCRT5000 reflective infrared sensor x2 for edge/drop detection.
- Hall sensor module x1 for magnetic landmark/checkpoint detection.

Environment:

- BH1750 illuminance sensor x1.
- BH1750 x1.
- BMP280 temperature/pressure sensor x1.
- BMP280 x1.

Controllers and chassis:

- STM32 controller board x1.
- ESP32 board x1. Existing authoritative files previously use ESP32-C3 SuperMini language; do not silently change the model.
- Battery/power system.
- Four encoded motors.
- Four mecanum wheels.
- Existing rover chassis.

Neutral planned sensor IDs:

- `c1_1`
- `c1_2`
- `ultrasonic_1`
- `ultrasonic_2`
- `ultrasonic_3`
- `tcrt5000_1`
- `tcrt5000_2`
- `bh1750_1`
- `bmp280_1`
- `mpu6050_1`
- `hall_1`

## USER-CONFIRMED PLANNED CONNECTIONS

Ground and landmark connector plan, supplied by the user for future STM32 bring-up:

- Two TCRT5000 modules and one Hall sensor are planned to use the STM32 PH2.0-6P four-channel line-tracking connector.
- TCRT5000 left OUT -> signal channel 1.
- TCRT5000 right OUT -> signal channel 2.
- Hall sensor S -> signal channel 3.
- Their power and ground are planned to share the connector VCC and GND.

This is a USER-CONFIRMED PLANNED CONNECTION only. It is not electrically tested hardware evidence. Connector orientation, exact pin order, supply voltage, logic voltage, pull configuration, active polarity, and installed behavior remain UNVERIFIED.

## CONFIRMED ELECTRICAL FACTS

Verified RPLIDAR C1 facts from earlier hardware lock work:

- Exact model: SLAMTEC RPLIDAR C1M1-R2.
- Connector type: XH2.54-5P.
- Active conductors: four.
- Unused connector position: one unused position in the five-pin housing.
- Ranging principle: fusion DTOF.
- Typical scan frequency: 10 Hz.
- Scan frequency range: 8 Hz to 12 Hz.
- Maximum sample rate: approximately 5000 samples per second.
- White-object range: approximately 50 mm to 12000 mm.
- Low-reflectivity black-object range: approximately 50 mm to 6000 mm.
- Supply voltage: 4.8 V to 5.2 V.
- Typical supply voltage: 5.0 V.
- Typical startup current: approximately 800 mA.
- Typical operating current: approximately 230 mA at 10 Hz.
- Maximum normal operating current: approximately 260 mA.
- Maximum specified power-supply ripple: 150 mV.
- UART voltage: 3.3 V TTL.
- UART baud rate: 460800.
- UART format: 8 data bits, no parity, 1 stop bit.
- External motor PWM conductor: VERIFIED not present and not allowed.

Verified RPLIDAR C1 wire functions:

| Wire color | Function | Connection rule |
| --- | --- | --- |
| Red | VCC, 5 V supply | Independent regulated 5 V supply |
| Yellow | LiDAR TX | Receiver UART RX |
| Green | LiDAR RX | Transmitter UART TX |
| Black | GND | Common ground with controller and power supply |
| Unused position | None | Leave unused |

These wire facts are preserved from the verified C1 harness profile. They do not prove that either physical C1 is currently wired, powered, mounted, or operational.

## PLANNED RESPONSIBILITIES

STM32 planned responsibilities:

- Four-mecanum-wheel motor control.
- Wheel encoder acquisition.
- Low-level motor safety.
- Command-timeout stop.
- MPU6050 acquisition.
- HC-SR04 acquisition.
- TCRT5000 edge/drop detection.
- Hall landmark detection.
- BH1750 and BMP280 acquisition unless later interface testing requires a different assignment.
- Low-rate sensor preprocessing.
- Basic odometry support.
- Local stop/turn obstacle-avoidance state machine.

ESP32 planned responsibilities:

- WiFi communication with the computer.
- Receive STM32 rover and sensor information.
- Package and transmit data.
- Receive limited configuration/control messages.
- Interface with at least one RPLIDAR C1 in a later phase.

PC planned responsibilities:

- Polar visualization.
- Cartesian visualization.
- Recording.
- Replay.
- Experiment inspection.
- Later short-range accumulated mapping.
- Data and figure export.

## UNVERIFIED VALUES

- Individual C1 serial IDs: UNVERIFIED.
- Individual C1 revisions: UNVERIFIED.
- Both C1 units' operational status: UNVERIFIED.
- Final C1 placement and orientation: UNVERIFIED.
- Simultaneous dual-C1 architecture: UNVERIFIED and optional.
- exact ESP32 GPIOs: UNVERIFIED.
- exact UART assignment: UNVERIFIED.
- exact STM32-ESP32 connector: UNVERIFIED.
- exact HC-SR04 level-shifting requirements on the physical board: UNVERIFIED.
- HC-SR04 ECHO voltage compatibility with STM32 inputs: UNVERIFIED.
- actual BH1750 I2C address: UNVERIFIED.
- actual BMP280 I2C address: UNVERIFIED.
- actual MPU6050 I2C address: UNVERIFIED.
- TCRT5000 and Hall output polarity remains UNVERIFIED.
- physical TCRT5000 active polarity: UNVERIFIED.
- physical Hall active polarity: UNVERIFIED.
- battery voltage and capacity: UNVERIFIED unless measured.
- final power-distribution topology: UNVERIFIED.
- final sensor mounting offsets: UNVERIFIED.
- Physical wiring verification date: UNVERIFIED.
- Successful PC-direct test date for either C1: NOT RUN.

## FUTURE TESTS

- Test `c1_1` PC-direct through the supplied adapter.
- Test `c1_2` PC-direct through the supplied adapter.
- Record device information with only redacted serial identifiers.
- Measure distance and orientation against known references.
- Verify supply voltage, polarity, current margin, ripple, and common ground before controller wiring.
- Verify ESP32 GPIO and UART assignment before live integration.
- Verify STM32-ESP32 physical link before relying on rover sensor data.
- Verify HC-SR04 level interface, TCRT5000 polarity, Hall polarity, I2C addresses, and sensor mounting offsets.

## Phase 2.5 Software Boundary Status

- PC-direct capture software can consume a user-provided serial port or a test fixture byte stream.
- Automated Phase 2.5 tests use fixture bytes only and do not open serial ports.
- No physical PC-direct capture has been run by repository automation.
- `c1_1` and `c1_2` operational status remain UNVERIFIED until independent manual tests are documented.
- No COM port, mounting orientation, serial identifier, or hardware revision is inferred by software.

## Phase 3.1 Software Boundary Status

- Phase 3.1 defines `mars_scout_stm32_sensor_telemetry` version `1` for host-side software tests and future STM32 telemetry forwarding.
- Automated Phase 3.1 tests use deterministic files and in-memory streams only.
- No serial port, USB device, GPIO, I2C bus, timer, STM32 flash action, or real sensor is accessed by Phase 3.1 automation.
- STM32 MCU part number, board revision, firmware framework, pin assignments, timer channels, UART assignments, I2C peripheral assignments, and real I2C addresses remain UNVERIFIED.
- Physical STM32 sensor bring-up has not started.

## Safety Rules

- Do not connect the LiDAR red wire to ESP32 3.3 V.
- Do not connect LiDAR TX to transmitter TX or LiDAR RX to receiver RX.
- Do not drive LiDAR RX from a USB adapter and ESP32 at the same time.
- Do not mark physical wiring safe until voltage, polarity, connector orientation, and common ground are directly checked.
- Do not publish full device serial numbers.
