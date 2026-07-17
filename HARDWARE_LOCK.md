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
- The old shared-VCC plan is superseded by module-specific evidence: TCRT5000 modules should use 3.3 V and the Hall module should use 5 V. Common ground remains required.

This is a USER-CONFIRMED PLANNED CONNECTION only. It is not electrically tested hardware evidence. Connector orientation, exact pin order, supply rails, Hall output topology, logic voltage, pull configuration, active polarity, and installed behavior remain UNVERIFIED.

OpenRF1 BH1750 connection plan, supplied by the user for Phase 3.2A:

- Controller board: OpenRF1 robot controller by Yeahbot / Hangzhou Songjia Technology.
- MCU: STM32F103RCT6, 64 pins, ARM Cortex-M3, 256 KB flash, 48 KB SRAM.
- Intended vendor toolchain: Keil MDK / uVision 5.
- Vendor target: STM32F103RC.
- Vendor examples use STM32F10x Standard Peripheral Library with `STM32F10X_HD`, `USE_STDPERIPH_DRIVER`, and `startup_stm32f10x_hd.s`.
- OpenRF1 software I2C SCL: PB1.
- OpenRF1 software I2C SDA: PC3.
- The board schematic includes 10 kOhm pull-ups from PB1/SCL and PC3/SDA to 3.3 V.
- The OpenRF1 2x4 I2C header supplies duplicated PC3/SDA, PB1/SCL, GND, and 5V rows.
- Do not confuse the I2C header with the adjacent SWD connector.
- Board includes CH340 USB-to-serial hardware; USB supports program download and serial communication, and SWD is also available.
- Vendor serial reference initializes USART1 on PA9 TX and PA10 RX at 115200 baud, 8 data bits, no parity, 1 stop bit.

GY-302/BH1750 Phase 3.2A wiring:

| GY-302 pin | OpenRF1 connection | Status |
| --- | --- | --- |
| VCC | OpenRF1 I2C 5V | MANUAL_EVIDENCE_VERIFIED for this GY-302 bring-up |
| GND | OpenRF1 I2C GND | MANUAL_EVIDENCE_VERIFIED for this GY-302 bring-up |
| SCL | OpenRF1 PB1/SCL | MANUAL_EVIDENCE_VERIFIED for this GY-302 bring-up |
| SDA | OpenRF1 PC3/SDA | MANUAL_EVIDENCE_VERIFIED for this GY-302 bring-up |
| ADDR | OpenRF1 GND | MANUAL_EVIDENCE_VERIFIED for configured address `0x23` |

The GY-302 module marking and pin labels VCC, GND, SCL, SDA, and ADDR are CONFIRMED by user-provided physical observation. With ADDR grounded, the configured public BH1750 7-bit address is `0x23`. Recorded manual evidence verifies firmware flash, CH340/USART1 telemetry, BH1750 communication at configured address `0x23`, a 500 ms telemetry period, and physical cover/illumination response. Repository automation did not flash hardware or open a real COM port; it only validates committed evidence. Absolute lux calibration remains UNVERIFIED.

GY-302 module-specific electrical evidence:

- The bare BH1750 IC operates at approximately 2.4 V to 3.6 V.
- The specific GY-302 breakout has onboard low-dropout 3.3 V regulation, onboard logic-level conversion, module-level 3 V to 5 V supply compatibility, and onboard I2C pull-ups on the regulated logic rail.
- GY-302 VCC -> OpenRF1 5 V is accepted for this exact module.
- No external regulator or I2C level shifter is required for this exact module.
- ADDR -> GND remains required for configured address `0x23`.

Phase 3.2B proposed full-hardware connection plan, supplied for software preparation only:

- ESP32-C3 SuperMini proposed link: GPIO21 TX -> OpenRF1 RX3, GPIO20 RX <- OpenRF1 TX3, with common ground and 5 V supply from the OpenRF1 Bluetooth UART header during non-USB operation. ESP32 external 5 V power and USB power must not be connected simultaneously.
- RPLIDAR C1 proposed link: C1 TX -> OpenRF1 RX2, C1 RX <- OpenRF1 TX2, VCC -> OpenRF1 user UART 5 V, GND -> user UART GND.
- Shared I2C signal proposal: BH1750, MPU6050, and BMP280 share PB1/SCL and PC3/SDA, but their VCC rails are not tied together.
- Proposed I2C power and straps: BH1750 VCC -> 5 V and ADDR -> GND for `0x23`; MPU6050 VCC -> 5 V and AD0 -> GND for `0x68`; BMP280 VCC -> 3.3 V, CSB -> 3.3 V, and SDO -> GND for `0x76`.
- HC-SR04 logical proposal: front trig/echo -> PWM channels 0/1, left -> 2/3, right -> 4/5. Initial bring-up powers one module from OpenRF1 3.3 V and measures Echo VOH before approving direct STM32 input.
- TCRT5000/Hall logical proposal: `tcrt5000_1` -> line input signal 1 and `tcrt5000_2` -> signal 2 at 3.3 V module power; `hall_1` -> signal 3 only after Hall `S` voltage is measured, with Hall module power at 5 V.

This entire Phase 3.2B connection plan is UNVERIFIED physical evidence. It does not confirm connector orientation, exact MCU pins, timer channels, DMA channels, voltage safety, level shifting, I2C ACKs, UART operation, sensor polarity, RPLIDAR operation, ESP32 operation, or real sensor data.

Phase 3.2B module-specific electrical evidence:

- GY-521/MPU6050 module: CONFIRMED_MODULE_EVIDENCE for 3.3 V or 5 V VCC, onboard 3.3 V regulator, SCL/SDA pull-ups to onboard 3.3 V, AD0 onboard pull-down, floating AD0 default `0x68`, optional INT, and unused XDA/XCL. Use explicit AD0 -> GND for deterministic address `0x68`; no external I2C level shifter is required for this exact module.
- BMP280-3.3 module: CONFIRMED_MODULE_EVIDENCE for approximately 1.71 V to 3.6 V operation and no evidence of onboard 5 V regulation or bidirectional level conversion. BMP280 VCC must connect to OpenRF1 3.3 V and must not connect to the I2C connector 5 V pin.
- ESP32-C3 SuperMini: CONFIRMED_MODULE_EVIDENCE for external power through the 5 V pin, approximately 3.3 V to 6 V external input, 3.3 V UART logic, GPIO21 TX, and GPIO20 RX. No STM32-to-ESP32 UART level shifter is required, but external 5 V and USB power must not be connected simultaneously.
- Wide-voltage HC-SR04 modules: CONFIRMED_MODULE_EVIDENCE for approximately 2.8 V to 5.5 V operation, approximately 3 mA current, and nominal 2 cm to 450 cm range. Echo VOH is not authoritatively specified, so direct STM32 connection is not approved until measured or exact MCU pin tolerance is established.
- TCRT5000 modules: CONFIRMED_MODULE_EVIDENCE for 3.3 V to 5 V operation, digital switching output, and module logic conditioning. Use 3.3 V for first integration.
- Hall module: CONFIRMED_MODULE_EVIDENCE for approximately 4.5 V to 24 V supply, so use 5 V. Output topology remains insufficiently proven; measure `S` voltage in both magnetic states before STM32 connection.

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
- exact ESP32 module UART GPIOs: CONFIRMED_MODULE_EVIDENCE for GPIO21 TX and GPIO20 RX; physical link UNVERIFIED.
- exact OpenRF1 UART assignment: UNVERIFIED.
- exact STM32-ESP32 connector: UNVERIFIED.
- exact USART2 user-UART MCU pins: UNVERIFIED.
- exact USART3 Bluetooth-UART MCU pins: UNVERIFIED.
- exact PWM channel 0 through 5 MCU pins/timers: UNVERIFIED.
- exact line input signal 1 through 3 MCU pins: UNVERIFIED.
- exact HC-SR04 Echo protection requirement on the physical board: UNVERIFIED until module supply and Echo VOH are measured.
- HC-SR04 ECHO voltage compatibility with STM32 inputs: UNVERIFIED.
- BH1750 absolute illuminance calibration: UNVERIFIED.
- BMP280 address in isolated Phase 3.2C capture: PHYSICAL_EVIDENCE_VERIFIED at `0x76`; full shared-I2C BMP280 operation remains UNVERIFIED.
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
- Phase 3.2A supersedes the older unknown STM32 board identity for the BH1750 bring-up path: OpenRF1 and STM32F103RCT6 are now CONFIRMED for this path.
- Board revision remains UNVERIFIED. Recorded manual evidence verifies the BH1750-only build/flash/telemetry path and physical light response, while absolute lux calibration remains UNVERIFIED.

## Phase 3.2A Software Boundary Status

- Phase 3.2A adds OpenRF1/STM32F103RCT6 application-layer firmware source for GY-302/BH1750 on software I2C PB1/PC3.
- Phase 3.2A adds PC-side mocked STM32 serial capture that reuses the strict Phase 3.1 parser and Phase 2.4 recording bridge.
- Automated Phase 3.2A tests use pure logic, file-backed mock readers, and generated JSONL only.
- No real COM port, USB device, GPIO, I2C bus, flash action, Keil build, or real sensor is accessed by repository automation.
- Keil build: SOFTWARE_VERIFIED.
- Firmware flashing: MANUAL_EVIDENCE_VERIFIED for the recorded BH1750-only run.
- CH340/USART1 telemetry: MANUAL_EVIDENCE_VERIFIED with the COM identifier kept private.
- BH1750 communication at configured address `0x23`: MANUAL_EVIDENCE_VERIFIED.
- 500 ms telemetry period and physical light response: MANUAL_EVIDENCE_VERIFIED.
- Absolute lux calibration: UNVERIFIED.

## Phase 3.2B Software Boundary Status

- Phase 3.2B adds an isolated OpenRF1 full-hardware firmware foundation and PC-side contracts/tests for proposed multisensor and communications integration.
- `firmware/openrf1/app/` remains the BH1750-only Phase 3.2A source boundary.
- `firmware/openrf1/full_hardware/` is the Phase 3.2B software foundation boundary.
- The Phase 3.2B full-hardware Keil project outputs to `Objects_FullHardware/` and must not overwrite `Objects/OpenRF1_BH1750.hex`.
- Automated Phase 3.2B tests use pure logic, deterministic files, and build/artifact audits only.
- No real COM port, USB device, GPIO, I2C bus, WiFi socket, flash action, or real sensor is accessed by repository automation.
- Physical Phase 3.2B multisensor wiring, voltage levels, power integrity, USART2/USART3 operation, BMP280/MPU6050 ACKs, TCRT5000/Hall polarity, HC-SR04 Echo VOH/timing, RPLIDAR transport, ESP32 link, concurrent operation, and real full-system sensor data remain UNVERIFIED.

## Phase 3.2C BMP280 Bring-Up Boundary Status

- Phase 3.2C adds an isolated OpenRF1 BMP280-only firmware boundary under `firmware/openrf1/bmp280_bringup/`.
- The Phase 3.2C Keil project is `firmware/openrf1/keil/OpenRF1_BMP280_Bringup.uvprojx`.
- The Phase 3.2C output directory is `Objects_BMP280_Bringup/` and must not overwrite `Objects/OpenRF1_BH1750.hex` or `Objects_FullHardware/OpenRF1_FullHardware.hex`.
- BMP280-only wiring for the formal evidence capture: VCC -> OpenRF1 3.3 V, GND -> OpenRF1 GND, SCL -> PB1 / connector B1, SDA -> PC3 / connector C3, CSB -> 3.3 V, and SDO -> GND.
- Committed Phase 3.2C evidence file `evidence/phase3.2c/bmp280_physical_adef636_20260718_002346.jsonl` has SHA-256 `1BB0C5BE149DC7C49A3C63432D1CAE4AACAE3D5A80265FE879CA06D1E1A74805`.
- Formal Keil HEX SHA-256 for the evidence run is `85101B9F76C27FDFA019E382FC7285F239F78FA78FB0722B0400F8DDFF67E27E`.
- BMP280 address `0x76`, ACK at `0x76`, and chip ID register readback `0xD0 -> 0x58`: PHYSICAL_EVIDENCE_VERIFIED for the isolated BMP280-only capture.
- Firmware configures `config = 0x80` and `ctrl_meas = 0x27` for 500 ms standby, filter off, temperature x1, pressure x1, and normal mode.
- Configuration readback `config = 0x80` and `ctrl_meas = 0x27`: PHYSICAL_EVIDENCE_VERIFIED.
- Calibration-register path sufficient for compensated output, continuous compensated temperature telemetry, continuous compensated pressure telemetry, 500 ms periodicity, and stable 30-second capture: PHYSICAL_EVIDENCE_VERIFIED.
- Automated Phase 3.2C tests use pure logic, static source checks, build/artifact audits, and committed evidence validation only.
- No real COM port, USB device, GPIO, I2C bus, flash action, or real sensor is accessed by repository automation.
- Absolute temperature accuracy, absolute pressure accuracy, environmental-reference comparison, long-duration operation beyond the formal capture, full multi-device shared-I2C concurrency, and complete full-hardware operation remain UNVERIFIED.

## Safety Rules

- Do not connect the LiDAR red wire to ESP32 3.3 V.
- Do not connect LiDAR TX to transmitter TX or LiDAR RX to receiver RX.
- Do not drive LiDAR RX from a USB adapter and ESP32 at the same time.
- Do not mark physical wiring safe until voltage, polarity, connector orientation, and common ground are directly checked.
- Do not publish full device serial numbers.
- Power off before changing GY-302 wiring.
- Do not confuse the OpenRF1 I2C header with the adjacent SWD connector.
- Do not report zero lux as an error sentinel; distinguish valid darkness from invalid telemetry.
- Do not connect HC-SR04 Echo directly until module supply and measured Echo VOH prove it is within the safe STM32 input range, or until suitable protection is installed.
- Do not use the PWM servo-interface + rail for the first HC-SR04 test; start with one module powered from the OpenRF1 3.3 V output and measure Echo high voltage.
- Disconnect the STM32/OpenRF1 5 V feed before plugging the ESP32-C3 SuperMini into USB; external 5 V and USB power must not be connected simultaneously.
- Do not power the BMP280-3.3 module from the I2C connector 5 V pin.
- For the BMP280-only bring-up, connect CSB to 3.3 V for I2C mode and SDO to GND for the planned `0x76` address before power-up.
- Do not treat Hall `S` as STM32-safe until its high/low voltage is measured in both magnetic states.
- Do not infer C1 signal identity from wire color alone.
- Do not use USART1 for high-rate lidar payload.
