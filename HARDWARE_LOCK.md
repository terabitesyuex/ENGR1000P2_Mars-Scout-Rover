# Hardware Lock

This file records hardware facts that must not drift silently. Unknown values remain explicit until physically verified.

## 2026-07-15 Inventory Update

The project inventory was rebaselined for Phase 2.4. This update adds newly confirmed available sensors and controller/chassis hardware while preserving earlier verified RPLIDAR C1 electrical facts.

## CONFIRMED INVENTORY

Ranging:

- RPLIDAR C1M1-R2 x1.
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
- The user reports that the complete vehicle has been assembled according to
  `docs/openrf1_rover_wiring_plan.md`. The 2026-07-23 evidence batch now records
  exterior assembly, vehicle front, three front HC-SR04 modules, installed
  C1/GY-521 modules, and supplied geometry/mounting dimensions. Connector
  orientation, continuity, voltage rails, protection, controller-bay wiring,
  motor/encoder signs, and integrated operation remain UNVERIFIED.
- ESP32 board x1: user-confirmed ESP32-C3 SuperMini. GPIO21 TX and GPIO20 RX are
  user-confirmed as stable UART pins for the STM32 link. The exact installed LDO
  part and thermally sustainable output current remain UNVERIFIED.
- Battery/power system: SELLER_DOCUMENTED Li-ion battery advertised as 11.1 V
  nominal, 7800 mAh, 5C, 12.6 V fully charged, 70 x 55 x 23 mm, with a
  DC 5.5 x 2.5 mm male barrel connector. This implies approximately 86.6 Wh
  nominal energy and 39 A at the advertised 5C rate; neither calculated value
  is a measured result, and 39 A is not a confirmed BMS continuous/peak rating.
  Barrel polarity, BMS thresholds, actual voltage, capacity, and condition
  remain UNVERIFIED. Evidence is hash-recorded in
  `evidence/hardware/battery/battery_evidence.md`.
- Matching charger: SELLER_DOCUMENTED as 110-240 VAC 50/60 Hz input, 12.6 V/1 A
  output, DC 5.5 x 2.5 mm female connector, and 100 cm cable. It is charge-only,
  is not the rover power source, and may be used only with the battery
  disconnected from the rover. Charger polarity and regulation remain
  UNVERIFIED.
- The user approves this pack as the direct OpenRF1 VIN source and reports that
  the installed components are wide-voltage parts. This is a USER_APPROVED_DESIGN
  topology, not measured electrical evidence. Main fuse selection, wire gauge,
  BMS current, motor stall current, polarity, and transient behavior remain
  MANUAL_ACTION_REQUIRED.
- Four JGB37-520 motors with Hall AB encoders. User-reported values: 6-12 V,
  0.36 A no-load current, 3.2 A stall current, 30:1 reduction, and 330 rpm
  no-load output speed. Four motors imply 1.44 A combined no-load current and
  12.8 A theoretical simultaneous stall current before board limiting.
- Four mecanum wheels.
- Existing rover chassis.

2026-07-23 vehicle geometry and mounting evidence:

- `MANUAL_EVIDENCE_VERIFIED` as supplied records: loaded wheel diameter
  `79 mm`, axle-centre wheelbase `190 mm`, and wheel-centre track width
  `217 mm`. Corresponding radius/half-values are `39.5 mm`, `95 mm`, and
  `108.5 mm`; tolerance and repeatability remain UNVERIFIED.
- The user reports C1 scan-plane height above the chassis upper surface as
  `56 mm + 29.8 mm = 85.8 mm`. C1 rover-frame x/y/yaw and an as-built datum
  check remain UNVERIFIED.
- The supplied response records left/centre/right HC-SR04 angles as
  `-45 deg`, `0 deg`, and `+45 deg`, with source-CAD tuples
  `(-42.45, 2.67, 132.23) mm`, `(0, 2.67, 148.33) mm`, and
  `(41.18, 2.67, 132.23) mm`. The source CAD axis convention is not defined,
  so these tuples are not yet rover-frame offsets.
- MPU6050 top/underside photographs preserve the installed module orientation
  relative to the marked vehicle front. The exact rover-frame axis transform,
  polarity, and calibration remain UNVERIFIED.
- Source files and hashes are archived in
  `evidence/hardware/vehicle_assembly_2026-07-23/vehicle_assembly_evidence.md`.

Neutral planned sensor IDs:

- `c1_1`
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

OpenRF1 motor, encoder, and UART evidence added from the board schematic dated
2024-07-01 and the supplied vendor motor examples:

- CN1 through CN4 are XH2.54-6P motor/encoder connectors. Their electrical pin
  order is pin 1 OUT2, pin 2 encoder 5 V, pin 3 encoder A, pin 4 encoder B, pin
  5 GND, and pin 6 OUT1.
- CN1 uses PC6/TIM8_CH1 with PA8 direction and PA0/PA1/TIM5 encoder inputs.
- CN2 uses PC7/TIM8_CH2 with PA11 direction and PA6/PA7/TIM3 encoder inputs.
- CN3 uses PC8/TIM8_CH3 with PA12 direction and PA15/PB3/TIM2 encoder inputs.
- CN4 uses PC9/TIM8_CH4 with PC10 direction and PB6/PB7/TIM4 encoder inputs.
- Vendor software maps A/L1 to CN2, B/R1 to CN4, C/L2 to CN1, and D/R2 to
  CN3. Mapping L1/R1/L2/R2 to installed FL/FR/RL/RR remains a controlled
  wheels-off-ground validation.
- Vendor software configures TIM8 PWM1 active high at approximately 17.99 kHz
  from a 72 MHz clock, prescaler 1, and period 2000. A separate production
  brake/coast/emergency-stop policy is still required.
- Encoder user evidence defines 11 A-phase cycles and 11 B-phase cycles per
  motor-shaft revolution. Nominal output-shaft values are 330 A cycles at x1 or
  1320 quadrature counts at x4 for the 30:1 reduction. One-output-revolution
  physical validation and gearbox tolerance remain UNVERIFIED.
- Encoder VCC accepts 3.3-5 V and signal-high level follows VCC. Output topology
  is unknown. The assembly design therefore leaves each motor connector pin 2
  5 V cavity unpopulated, powers all four blue encoder wires from CN5 3.3 V,
  and adds 10 kOhm pull-ups to 3.3 V on all eight A/B inputs.
- H5 USART2 pin order is pin 1 5 V, pin 2 GND, pin 3 PA2/TX2, and pin 4
  PA3/RX2.
- H6 USART3 pin order is pin 1 5 V, pin 2 GND, pin 3 PB11/RX3, and pin 4
  PB10/TX3.
- The assembly wiring design assigns ultrasonic 2 to H3 PB9/TRIG and PB8/ECHO,
  and ultrasonic 3 to H3 PD2/TRIG and PC11/ECHO. These are DESIGN_LOCKED
  project allocations, not vendor ultrasonic ports; each ECHO requires its own
  10 kOhm / 15 kOhm divider and firmware support.
- USER_CONFIRMED_CURRENT_DEMO_MAPPING supersedes that proposal for the current
  vehicle-demo target: US1 left PB9/PB8, US2 centre PB5/PB4, and US3 right
  PD2/PC11. Historical isolated CN6 bring-up facts are unchanged.
- USER_REPORTED_OPERATIONAL_DIRECT_ECHO: all three current demo ECHO paths are
  directly connected without dividers and obstacle avoidance operates. This is
  functional evidence only. ECHO-high voltage at PB8, PB4, and PC11 and
  long-term electrical safety remain UNVERIFIED.
- VEHICLE_DEMO_ENCODER_SOFTWARE_VERIFIED: the isolated VehicleDemo target
  configures the vendor-documented connector timer paths as CN1/TIM5 PA0/PA1,
  CN2/TIM3 PA6/PA7, CN3/TIM2 full remap PA15/PB3 with JTAG disabled and SWD
  retained, and CN4/TIM4 PB6/PB7. It samples 16-bit raw counters every 50 ms,
  computes modular deltas/cumulative counts, and emits connector-labelled
  read-only JSONL. This is not physical encoder evidence and does not establish
  CN-to-wheel mapping, installed pull-ups, direction signs, counts per wheel
  revolution, or real counter activity.
- ENCODER_BRINGUP_SOFTWARE_VERIFIED: the dedicated
  `OpenRF1_Encoder_Bringup` target uses the same neutral CN1/TIM5,
  CN2/TIM3, CN3/full-remapped-TIM2, and CN4/TIM4 read-only counter mapping at
  100 ms. It initializes no TIM8, motor GPIO, receive command path, ultrasonic,
  or Hall peripheral and linked with ARM Compiler 6.24 at 0 errors and
  0 warnings. This is not physical evidence; signal levels, pull-ups, counter
  activity, physical wheel assignment, direction, and counts/revolution remain
  UNVERIFIED.
- MOTOR_BRINGUP_SOFTWARE_VERIFIED: the dedicated
  `OpenRF1_Motor_Bringup` target preserves the vendor connector PWM,
  direction, and encoder mapping, but starts unconfigured with all TIM8 CCR
  values zero and both CCER and BDTR/MOE disabled. Exactly one connector can be
  enabled after explicit configuration plus ARM/RUN, and watchdog or command
  failure removes output. ARM Compiler 6.24 reports 0 errors and 0 warnings.
  The 0..1000 duty representation bound is not a physical safety rating.
  Flashing, wiring safety, selected duty, physical wheel identity/sign,
  current, stopping, counter response, and operation remain UNVERIFIED.

The complete assembly harness and pre-power procedure are recorded in
`docs/openrf1_rover_wiring_plan.md`.

Ground and landmark connector plan, supplied by the user and checked against OpenRF1 vendor material for Phase 3.2F:

- Two TCRT5000 modules and one Hall sensor are planned to use the STM32 PH2.0-6P four-channel line-tracking connector.
- Signal channel 1 / X1 -> PC4, signal channel 2 / X2 -> PC5, and signal channel 3 / X3 -> PB0 are AUTHORITATIVE_VENDOR_DOCUMENTED for the isolated Phase 3.2F software target.
- Tracking connector pin order is AUTHORITATIVE_VENDOR_DOCUMENTED: pin 1 GND, pin 2 X4 / schematic PC14, pin 3 X3 / PB0, pin 4 X2 / PC5, pin 5 X1 / PC4, pin 6 VCC_5V.
- TCRT5000 left OUT -> signal channel 1 / X1 / PC4.
- TCRT5000 right OUT -> signal channel 2 / X2 / PC5.
- Hall sensor S -> external 10 kOhm / 15 kOhm divider -> signal channel 3 / X3 / PB0.
- X4 remains unused in Phase 3.2F because the schematic names PC14 while the old tracking example names PB1, and PB1 is already the repository's verified software-I2C SCL line.
- The old shared-VCC plan is superseded by module-specific evidence: TCRT5000 modules should use 3.3 V and the Hall module should use 5 V. Common ground remains required.

This is not electrically tested hardware evidence. Physical connector orientation, cable orientation, installed wiring, supply rails, Hall module-level output voltage, logic voltage at PB0 after the divider, active polarity, and installed behavior remain UNVERIFIED until manual evidence is recorded.

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

- ESP32-C3 SuperMini link: GPIO21 TX -> OpenRF1 RX3 and GPIO20 RX <- OpenRF1 TX3,
  with common ground. The assembly plan supersedes H6 power: H6 pin 1 remains
  disconnected and an independent 5 V buck feeds ESP32 through a removable
  jumper. ESP32 external 5 V and USB power must not be connected simultaneously.
- RPLIDAR C1 link: C1 TX -> OpenRF1 RX2 and C1 RX <- OpenRF1 TX2, with common
  ground. The assembly plan supersedes H5 power: H5 pin 1 remains disconnected
  and an independent regulated 5 V buck feeds C1.
- Shared I2C signal proposal: BH1750, MPU6050, and BMP280 share PB1/SCL and PC3/SDA, but their VCC rails are not tied together.
- Proposed I2C power and straps: BH1750 VCC -> 5 V and ADDR -> GND for `0x23`; MPU6050 VCC -> 5 V and AD0 -> GND for `0x68`; BMP280 VCC -> 3.3 V, CSB -> 3.3 V, and SDO -> GND for `0x76`.
- HC-SR04 Phase 3.2E isolated baseline: OpenRF1 vendor control-board package, ultrasonic sensor example, and OpenRF1 schematic revision dated 2024-07-01 lock CN6 B4B-PH-K-S(LF)(SN) pin 1: VCC_5V, pin 2: GND, pin 3: PA5_TRIG, pin 4: PA4_ECHO as AUTHORITATIVE_VENDOR_DOCUMENTED. TRIG: PA5. ECHO: PA4. TIM6 provides the isolated timer resource. Do not connect HC-SR04 ECHO directly to CN6 pin 4.
- TCRT5000/Hall logical proposal: `tcrt5000_1` -> line input signal 1 and `tcrt5000_2` -> signal 2 at 3.3 V module power; `hall_1` -> signal 3 only after Hall `S` voltage is measured, with Hall module power at 5 V.

This Phase 3.2B connection plan remains UNVERIFIED physical evidence. Later
schematic review confirms the H5/H6 UART pins and motor/encoder mappings listed
above, but it does not confirm installed connector orientation, cable
orientation, DMA operation, voltage measurements, I2C concurrency, UART
operation, sensor polarity, RPLIDAR operation, ESP32 operation, or real
full-system sensor data.

Phase 3.2D isolated MPU6050 bring-up plan, supplied for software preparation only:

- Dedicated target: `mpu6050_1` only, with no other new sensors connected for the first manual test.
- Planned module wiring: GY-521/MPU6050 VCC -> OpenRF1 5 V, GND -> OpenRF1 GND, SCL -> PB1 / connector B1, SDA -> PC3 / connector C3, AD0 -> GND for address `0x68`.
- Planned unused pins: INT, XDA, XCL, and FSYNC disconnected for polling bring-up.
- Planned register checks: WHO_AM_I register `0x75` expected `0x68`, `PWR_MGMT_1 = 0x01`, `SMPLRT_DIV = 0x09`, `CONFIG = 0x03`, `GYRO_CONFIG = 0x00`, and `ACCEL_CONFIG = 0x00`.

The original Phase 3.2D connection plan has now been manually exercised only for the isolated MPU6050 target. A's sanitized evidence is limited to the reported isolated VCC/GND/SCL/SDA/AD0 wiring, I2C ACK/address `0x68`, WHO_AM_I `0x68`, isolated configuration readback, live IMU JSON telemetry, startup gyro-bias semantics, approximately 10 Hz output during a 15-second isolated test with no reported sequence loss, and isolated sensor-axis response. Exact electrical measurements, continuity, delay-loop tuning, build/HEX metadata, exact timing statistics, and exact bias/noise statistics remain UNVERIFIED, together with absolute accuracy, calibration motion rejection, long-duration drift, shared-I2C operation, final rover-frame alignment, and full-hardware operation.

Phase 3.2B module-specific electrical evidence:

- GY-521/MPU6050 module: CONFIRMED_MODULE_EVIDENCE for 3.3 V or 5 V VCC, onboard 3.3 V regulator, SCL/SDA pull-ups to onboard 3.3 V, AD0 onboard pull-down, floating AD0 default `0x68`, optional INT, and unused XDA/XCL. Use explicit AD0 -> GND for deterministic address `0x68`; no external I2C level shifter is required for this exact module.
- BMP280-3.3 module: CONFIRMED_MODULE_EVIDENCE for approximately 1.71 V to 3.6 V operation and no evidence of onboard 5 V regulation or bidirectional level conversion. BMP280 VCC must connect to OpenRF1 3.3 V and must not connect to the I2C connector 5 V pin.
- ESP32-C3 SuperMini: CONFIRMED_MODULE_EVIDENCE for external power through the 5 V pin, approximately 3.3 V to 6 V external input, 3.3 V UART logic, GPIO21 TX, and GPIO20 RX. No STM32-to-ESP32 UART level shifter is required, but external 5 V and USB power must not be connected simultaneously.
- ESP32-C3 chip-level evidence confirms two hardware UARTs and GPIO-matrix
  routing. GPIO2, GPIO8, and GPIO9 are strapping pins. The user reports an
  AMS1117-class 500 mA nominal LDO expectation with a 250-300 mA continuous
  thermal target, but the exact SuperMini LDO part is UNVERIFIED until the
  physical board or its schematic identifies it.
- Wide-voltage HC-SR04 modules: CONFIRMED_MODULE_EVIDENCE for approximately 2.8 V to 5.5 V operation, approximately 3 mA current, and nominal 2 cm to 450 cm range. Echo VOH is not authoritatively specified. For the OpenRF1 CN6 path, the schematic supplies VCC_5V and connects PA4_ECHO directly to PA4 with no onboard level shifter; direct ECHO-to-CN6-pin-4 wiring is prohibited for controlled bring-up. The external protection scheme is AUTHORITATIVE_VENDOR_DOCUMENTED by project design lock: HC-SR04 ECHO -> 10 kOhm series resistor -> protected PA4 / CN6-pin-4 node; protected PA4 node -> 15 kOhm resistor -> GND; use 5 percent tolerance or better.
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
- The official SLAMTEC SDK repository lists C1 as supported in SDK v2.1.0.
- Startup sequence is DESIGN_LOCKED as transport setup -> GET_HEALTH -> SCAN
  (`0xA5 0x20`) -> descriptor validation -> sample stream. RESET is reserved for
  recovery and is not required before every normal scan.
- The user-provided 300 mA supply recommendation is not used for rover power
  sizing because the preserved C1 startup planning value is approximately
  800 mA.

Verified RPLIDAR C1 wire functions:

| Wire color | Function | Connection rule |
| --- | --- | --- |
| Red | VCC, 5 V supply | Independent regulated 5 V supply |
| Yellow | LiDAR TX | Receiver UART RX |
| Green | LiDAR RX | Transmitter UART TX |
| Black | GND | Common ground with controller and power supply |
| Unused position | None | Leave unused |

These wire facts are preserved from the verified C1 harness profile. They do not prove that the one physical C1 is correctly powered, permanently mounted, or integrated into the rover.

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

- C1 serial ID: UNVERIFIED.
- C1 revision: UNVERIFIED.
- Physical `c1_1` PC-direct scan acquisition: MANUAL_EVIDENCE_VERIFIED; complete operational acceptance remains partial.
- Final C1 placement and orientation: UNVERIFIED.
- Dual-C1 integration: NOT CURRENT SCOPE.
- exact ESP32 module UART GPIOs: CONFIRMED_MODULE_EVIDENCE for GPIO21 TX and GPIO20 RX; physical link UNVERIFIED.
- OpenRF1 UART assignment: AUTHORITATIVE_VENDOR_DOCUMENTED as H5/USART2 and H6/USART3; physical operation remains UNVERIFIED.
- STM32-ESP32 connector: DESIGN_LOCKED as H6/USART3; installed harness and operation remain UNVERIFIED.
- USART2 user-UART MCU pins: AUTHORITATIVE_VENDOR_DOCUMENTED as PA2/TX2 and PA3/RX2.
- USART3 Bluetooth-UART MCU pins: AUTHORITATIVE_VENDOR_DOCUMENTED as PB10/TX3 and PB11/RX3.
- Additional HC-SR04 paths are DESIGN_LOCKED on H3 PB9/PB8 and PD2/PC11; firmware support, installed dividers, timing, and physical operation remain UNVERIFIED.
- tracking connector signal 1 / X1 -> PC4, signal 2 / X2 -> PC5, signal 3 / X3 -> PB0, and connector pin order: AUTHORITATIVE_VENDOR_DOCUMENTED.
- installed line-input wiring, cable orientation, TCRT output voltages, Hall divider values, Hall divided voltage, and active polarity: UNVERIFIED.
- HC-SR04 CN6 pin order, PA5 TRIG, PA4 ECHO, TIM6, and external 10 kOhm / 15 kOhm ECHO divider requirement: AUTHORITATIVE_VENDOR_DOCUMENTED.
- HC-SR04 ECHO voltage compatibility at PA4 after the external divider: UNVERIFIED until the installed divider and voltages are physically measured.
- actual board connector orientation: UNVERIFIED.
- actual cable orientation: UNVERIFIED.
- installed HC-SR04 ECHO divider resistor values: UNVERIFIED.
- real HC-SR04 ECHO voltage before division: UNVERIFIED.
- real HC-SR04 ECHO voltage after division: UNVERIFIED.
- physical trigger pulse: UNVERIFIED.
- physical echo pulse: UNVERIFIED.
- real distance data: UNVERIFIED.
- physical HC-SR04 timer accuracy and timeout behavior: UNVERIFIED.
- BH1750 absolute illuminance calibration: UNVERIFIED.
- BMP280 address in isolated Phase 3.2C capture: PHYSICAL_EVIDENCE_VERIFIED at `0x76`; full shared-I2C BMP280 operation remains UNVERIFIED.
- actual MPU6050 I2C address: MANUAL_EVIDENCE_VERIFIED at `0x68` for the isolated Phase 3.2D bring-up with AD0 measured at 0 V; shared-I2C operation remains UNVERIFIED.
- TCRT5000 and Hall output polarity remains UNVERIFIED.
- physical TCRT5000 active polarity: UNVERIFIED.
- physical Hall active polarity: UNVERIFIED.
- battery product-page values: SELLER_DOCUMENTED as Li-ion, 11.1 V nominal,
  7800 mAh, 5C, 12.6 V fully charged, 70 x 55 x 23 mm, and DC 5.5 x 2.5 mm male;
  actual voltage/capacity, connector polarity, condition, and BMS continuous/
  peak current remain UNVERIFIED.
- battery charger product-page values: SELLER_DOCUMENTED as 12.6 V/1 A with
  110-240 VAC 50/60 Hz input and DC 5.5 x 2.5 mm female connector; measured
  polarity, regulation, cutoff behavior, and charging operation remain
  UNVERIFIED.
- final power-distribution topology: DESIGN_LOCKED in
  `docs/openrf1_rover_wiring_plan.md`; installed wiring and load validation
  remain UNVERIFIED.
- final sensor mounting offsets: UNVERIFIED.
- Physical wiring verification date: UNVERIFIED.
- Successful PC-direct evidence date for `c1_1`: MANUAL_EVIDENCE_VERIFIED on 2026-07-22.

## FUTURE TESTS

- Measure the `c1_1` supply, polarity, current margin, ripple, and common ground before rover integration.
- Run vendor device-information, health, scan-mode, and measured-frequency checks with identifiers redacted.
- Repeat bounded capture with wall-clock timing and explicit corrupt/dropped-node accounting.
- Measure distance and orientation against controlled known references for calibration.
- Verify ESP32 GPIO and UART assignment before live integration.
- Verify STM32-ESP32 physical link before relying on rover sensor data.
- Verify HC-SR04 level interface, TCRT5000 polarity, Hall polarity, shared-I2C operation, final MPU6050 mounting orientation, and sensor mounting offsets.
- USER_CONFIRMED_CURRENT_DEMO_MAPPING: left PB9/PB8, centre PB5/PB4, and right
  PD2/PC11. The confirmation screenshot SHA-256 is
  `E018B695861391BFB3ED7EF4EA6F5560A13D6BBD409FBBF0FABCE86E6E16B3F0`.
- USER_REPORTED_OPERATIONAL_DIRECT_ECHO: no divider is installed on the three
  current demo ECHO paths and the user reports successful operation. Do not
  infer voltage compatibility or electrical safety; measure ECHO high at PB8,
  PB4, and PC11 before electrical acceptance.

## Phase 2.5 Software Boundary Status

- PC-direct capture software can consume a user-provided serial port or a test fixture byte stream.
- Automated Phase 2.5 tests use fixture bytes only and do not open serial ports.
- No physical PC-direct capture has been run by repository automation.
- Committed physical evidence validates eight `c1_1` JSONL captures, 102 scan records, 36,720 decoded points, repository replay/rendering, and external RViz `/scan` visualization as MANUAL_EVIDENCE_VERIFIED.
- The evidence timestamps are generated by the capture tool; electrical safety, vendor health, wall-clock scan timing, absolute accuracy, final mounting, and full-rover operation remain UNVERIFIED.
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

## Phase 3.2D MPU6050 Bring-Up Boundary Status

- Phase 3.2D adds an isolated OpenRF1 MPU6050-only firmware boundary under `firmware/openrf1/mpu6050_bringup/`.
- The Phase 3.2D Keil project is `firmware/openrf1/keil/OpenRF1_MPU6050_Bringup.uvprojx`.
- The Phase 3.2D output directory is `Objects_MPU6050_Bringup/` and must not overwrite `Objects/OpenRF1_BH1750.hex`, `Objects_BMP280_Bringup/OpenRF1_BMP280_Bringup.hex`, or `Objects_FullHardware/OpenRF1_FullHardware.hex`.
- A reported the isolated MPU6050-only wiring as GY-521/MPU6050 VCC -> OpenRF1 H4 5 V, GND -> H4 GND, SCL -> PB1 / SCL, SDA -> PC3 / SDA, and AD0 -> GND. Exact connector orientation and electrical measurements remain UNVERIFIED.
- Address `0x68`, WHO_AM_I `0x68`, wake/configuration values `PWR_MGMT_1 = 0x01`, `SMPLRT_DIV = 0x09`, `CONFIG = 0x03`, `GYRO_CONFIG = 0x00`, and `ACCEL_CONFIG = 0x00` readback: MANUAL_EVIDENCE_VERIFIED for the isolated bring-up.
- `gyro_raw` remains raw register data and only `gyro_dps` subtracts the startup dynamic bias: MANUAL_EVIDENCE_VERIFIED. Exact bias and noise statistics remain UNVERIFIED.
- Software-I2C delay-loop tuning and reproducible Keil build/HEX metadata remain UNVERIFIED.
- Automated Phase 3.2D tests use pure logic, static source checks, build/artifact audits, and previous evidence hash checks only.
- No real COM port, USB device, GPIO, I2C bus, flash action, or real sensor is accessed by repository automation.
- Isolated MPU6050 ACK/address, WHO_AM_I, configuration readback, live IMU telemetry, startup gyro-bias semantics, A-reported approximately 10 Hz output during a 15-second test with no reported sequence loss, and isolated sensor-axis response are MANUAL_EVIDENCE_VERIFIED.
- Absolute acceleration accuracy, absolute angular-rate accuracy, calibration-time motion detection, calibration motion rejection, long-duration thermal drift, final rover-frame axis alignment, accelerometer offsets, yaw drift, full multi-device shared-I2C concurrency, motor-vibration behavior, encoder/IMU fusion, physical odometry accuracy, ESP32/WiFi integration, and complete full-hardware operation remain UNVERIFIED.

## Phase 3.2E HC-SR04 Bring-Up Boundary Status

- Phase 3.2E adds an isolated OpenRF1 HC-SR04-only firmware boundary under `firmware/openrf1/hcsr04_bringup/`.
- The Phase 3.2E Keil project is `firmware/openrf1/keil/OpenRF1_HCSR04_Bringup.uvprojx`.
- The Phase 3.2E output directory is `Objects_HCSR04_Bringup/` and must not overwrite previous Phase 3.2A/3.2B/3.2C/3.2D outputs.
- OpenRF1 vendor control-board package, ultrasonic sensor example, and OpenRF1 schematic revision dated 2024-07-01 lock CN6 B4B-PH-K-S(LF)(SN) pin 1: VCC_5V, pin 2: GND, pin 3: PA5_TRIG, pin 4: PA4_ECHO as AUTHORITATIVE_VENDOR_DOCUMENTED.
- TRIG: PA5, GPIOA push-pull output. ECHO: PA4, GPIOA floating input in the vendor example. Timer: TIM6, prescaler 71, period 30000, nominal 1 us count at the established 72 MHz timer clock.
- Do not connect HC-SR04 ECHO directly to CN6 pin 4. The external protection requirement is HC-SR04 ECHO -> 10 kOhm series resistor -> protected PA4 / CN6-pin-4 node; protected PA4 node -> 15 kOhm resistor -> GND; use 5 percent tolerance or better.
- Automated Phase 3.2E tests use pure logic, static source checks, build/artifact audits, and previous evidence hash checks only.
- No real COM port, USB device, GPIO, timer peripheral, flash action, or real sensor is accessed by repository automation.
- actual board connector orientation: UNVERIFIED.
- actual cable orientation: UNVERIFIED.
- installed resistor values: UNVERIFIED.
- real ECHO voltage before division: UNVERIFIED.
- real ECHO voltage after division: UNVERIFIED.
- physical trigger pulse: UNVERIFIED.
- physical echo pulse: UNVERIFIED.
- real distance data: UNVERIFIED.
- physical timer accuracy, physical timeout behavior, absolute distance accuracy, and complete full-hardware operation remain UNVERIFIED.

## Phase 3.2F Ground-Sensor Bring-Up Boundary Status

- Phase 3.2F adds an isolated OpenRF1 ground-sensor-only firmware boundary under `firmware/openrf1/ground_sensors_bringup/`.
- The Phase 3.2F Keil project is `firmware/openrf1/keil/OpenRF1_GroundSensors_Bringup.uvprojx`.
- The Phase 3.2F output directory is `Objects_GroundSensors_Bringup/` and must not overwrite previous Phase 3.2A/3.2B/3.2C/3.2D/3.2E outputs.
- OpenRF1 vendor control-board package, OpenRF1 four-channel tracking example, and OpenRF1 schematic revision dated 2024-07-01 lock signal 1 / X1 / PC4, signal 2 / X2 / PC5, and signal 3 / X3 / PB0 as AUTHORITATIVE_VENDOR_DOCUMENTED.
- Tracking connector pin order is AUTHORITATIVE_VENDOR_DOCUMENTED: pin 1: GND, pin 2: X4 / schematic PC14, pin 3: X3 / PB0, pin 4: X2 / PC5, pin 5: X1 / PC4, pin 6: VCC_5V.
- The vendor tracking example configures PC4, PC5, and PB0 as floating input.
- The schematic says PC14 for X4; the old example maps X4 to PB1. PB1 is already used as the software-I2C SCL line in this repository, so signal 4 / X4 is unused and excluded from Phase 3.2F.
- DESIGN_LOCKED: left TCRT5000 OUT -> signal 1 / X1 / PC4, VCC -> STM32 3.3 V, GND -> common GND.
- DESIGN_LOCKED: right TCRT5000 OUT -> signal 2 / X2 / PC5, VCC -> STM32 3.3 V, GND -> common GND.
- DESIGN_LOCKED: Hall + -> 5 V, Hall - -> common GND, Hall S -> external 10 kOhm / 15 kOhm divider -> signal 3 / X3 / PB0.
- Do not connect Hall S directly to PB0.
- Do not power the TCRT modules from the connector's 5 V pin during controlled bring-up.
- Do not share one VCC rail across all three modules.
- Automated Phase 3.2F tests use pure logic, static source checks, build/artifact audits, and offline validation of the four sanitized TCRT captures.
- No real COM port, USB device, GPIO, timer peripheral, flash action, or real sensor is accessed by repository automation.
- isolated firmware build and flash: MANUAL_EVIDENCE_VERIFIED.
- installed left OUT -> signal 1 / X1 / PC4 and right OUT -> signal 2 / X2 / PC5: MANUAL_EVIDENCE_VERIFIED.
- labelled 3.3 V/common-GND module connections: MANUAL_EVIDENCE_VERIFIED as connections only; voltage remains unmeasured.
- Hall physical placement: USER_CONFIRMED_FROM_SUPPLIED_PHOTOGRAPH as mounted
  on the rover underside; the top of the supplied photograph is the rover-front
  direction.
- Hall body-boundary clearances: MANUAL_EVIDENCE_VERIFIED as user-supplied
  corrected measurements: 185 mm to the front boundary, 135 mm to the rear
  boundary, and 75 mm to both the left and right boundaries. These imply a body
  envelope of 320 x 150 mm and a derived planar Hall offset of x=-25 mm, y=0 mm
  from that envelope's geometric centre (`+x` forward, `+y` left).
- Hall-to-axle measurements: MANUAL_EVIDENCE_VERIFIED as user-supplied values
  of 95 mm to both front and rear axle centres. Together with the supplied
  190 mm wheelbase and equal 75 mm side clearances, this establishes the Hall
  sensing point at x=0 mm, y=0 mm relative to the wheel-centre `base_link` in
  the horizontal plane.
- Hall sensing-point height above the floor: MANUAL_EVIDENCE_VERIFIED as a
  user-supplied 65 mm measurement. With the supplied 79 mm loaded wheel diameter
  (39.5 mm radius) and `base_link z=0` at the wheel-centre plane, the derived
  vertical offset is z=+25.5 mm. This is mounting geometry, not verified
  magnetic working distance. Sensing face, connector wiring, and cable routing
  remain UNVERIFIED.
- live raw/debounced response from both TCRT modules: MANUAL_EVIDENCE_VERIFIED for the tested geometry.
- four 100-frame captures without sequence gaps and exact 50 ms steady-state timestamps: MANUAL_EVIDENCE_VERIFIED.
- final connector/cable orientation and strain relief: UNVERIFIED.
- actual 3.3 V rail: UNVERIFIED.
- actual 5 V rail: UNVERIFIED.
- actual TCRT output voltage: UNVERIFIED.
- TCRT output topology: UNVERIFIED.
- left TCRT active polarity: UNVERIFIED.
- right TCRT active polarity: UNVERIFIED.
- Hall module-level output voltage: UNVERIFIED.
- Hall active polarity: UNVERIFIED.
- Hall triggering magnetic pole: UNVERIFIED.
- reflective white-surface response at the tested geometry: MANUAL_EVIDENCE_VERIFIED.
- black-surface response: UNVERIFIED.
- open-space response at the tested geometry: MANUAL_EVIDENCE_VERIFIED; dependable drop/edge safety classification is UNVERIFIED.
- magnetic activation: UNVERIFIED.
- magnetic release: UNVERIFIED.
- optical threshold, reliable detection distance, black/white classification, Hall trigger distance, real debounce suitability outside the captured steady states, startup timing, long-duration stability, moving-rover drop prevention, and complete full-hardware operation remain UNVERIFIED.
- raw GPIO values are not semantic detection states, and semantic polarity remains unverified.

## Safety Rules

- Do not connect the LiDAR red wire to ESP32 3.3 V.
- Do not connect LiDAR TX to transmitter TX or LiDAR RX to receiver RX.
- Do not drive LiDAR RX from a USB adapter and ESP32 at the same time.
- Do not mark physical wiring safe until voltage, polarity, connector orientation, and common ground are directly checked.
- Do not publish full device serial numbers.
- Power off before changing GY-302 wiring.
- Do not confuse the OpenRF1 I2C header with the adjacent SWD connector.
- Do not report zero lux as an error sentinel; distinguish valid darkness from invalid telemetry.
- Do not connect HC-SR04 ECHO directly to CN6 pin 4.
- For Phase 3.2E, install the external 10 kOhm / 15 kOhm ECHO divider before PA4 receives the signal; do not claim it has been installed or tested until physical evidence is recorded.
- For Phase 3.2F, do not connect Hall S directly to PB0; install and verify the external 10 kOhm / 15 kOhm divider before PB0 receives Hall S.
- For Phase 3.2F, do not power the TCRT modules from the tracking connector's 5 V pin during controlled bring-up, and do not share one VCC rail across the TCRT and Hall modules.
- Disconnect the STM32/OpenRF1 5 V feed before plugging the ESP32-C3 SuperMini into USB; external 5 V and USB power must not be connected simultaneously.
- Do not power the BMP280-3.3 module from the I2C connector 5 V pin.
- For the BMP280-only bring-up, connect CSB to 3.3 V for I2C mode and SDO to GND for the planned `0x76` address before power-up.
- For the MPU6050-only bring-up, use the GY-521/MPU6050 module 5 V VCC plan only for that module type and keep AD0 tied to GND for the isolated `0x68` address; do not generalize the isolated ACK or WHO_AM_I evidence to shared-I2C, final installed orientation, or complete full-hardware operation.
- Do not treat Hall `S` as STM32-safe until its high/low voltage is measured in both magnetic states.
- Do not infer C1 signal identity from wire color alone.
- Do not use USART1 for high-rate lidar payload.
