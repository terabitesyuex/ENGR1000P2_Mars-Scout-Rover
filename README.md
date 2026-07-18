# ENGR1000P2 Mars Scout Rover

This repository supports a low-cost Mars Scout Rover using an STM32 mecanum-wheel chassis, an ESP32 communication layer, multiple sensors, and PC visualization/recording tools.

Mandatory baseline functions are nearby-obstacle detection, local stop/turn collision avoidance, rover and sensor data acquisition, WiFi data transmission to a computer, real-time 2D LiDAR/radar-style display, reproducible evidence through recording/replay, and safe behavior when communication or sensors fail.

Major enhancements are encoder/IMU-assisted pose estimation, short-range accumulated 2D environment mapping, optional dual-RPLIDAR C1 use after feasibility is verified, and environmental-change indication using illuminance, temperature, and atmospheric-pressure measurements. ROS and a vehicle-mounted Linux computer are not required.

## Current Phase

- Phase 0: complete.
- Phase 1: complete.
- Phase 2.1: synthetic scan pipeline and unified `ScanFrame` model complete.
- Phase 2.2: rover-frame coordinate transforms complete.
- Automated phase verification foundation: complete.
- Phase 2.3: synthetic LiDAR visualization complete.
- Phase 2.4: multi-sensor JSONL recording, replay, reproducible synthetic datasets, hardware-inventory update, and plan rebaseline complete.
- Phase 2.5: PC-direct C1 driver boundary, standard scan-node parsing, bounded capture into JSONL, replay, and visualization integration complete.
- Phase 3.1: STM32 low-rate sensor telemetry protocol, deterministic simulator, strict parser, recording bridge, CLI workflows, and manual bring-up checklist complete.
- Phase 3.2A: OpenRF1 STM32F103RCT6 + GY-302/BH1750 firmware foundation, mocked PC serial-capture workflow, documentation, phase verification, and recorded BH1750-only physical evidence complete. Absolute lux calibration remains UNVERIFIED.
- Phase 3.2B: OpenRF1 multisensor and communications software foundation, isolated full-hardware Keil project, PC contracts, simulators, parser/recording support, and software verification support added. Physical wiring and live sensor/link behavior remain UNVERIFIED.
- Phase 3.2C: isolated OpenRF1 BMP280-only bring-up firmware, Keil target, host-side BMP280 register/telemetry tests, verifier support, and recorded BMP280 physical evidence complete. Absolute temperature and pressure accuracy remain UNVERIFIED.
- Phase 3.2D: isolated OpenRF1 MPU6050-only bring-up firmware foundation, Keil target, host-side MPU6050 register/telemetry tests, and verifier support complete. Physical ACK, WHO_AM_I, live IMU telemetry, calibration, and axis orientation remain UNVERIFIED.
- Phase 3.2E: isolated OpenRF1 HC-SR04-only bring-up firmware foundation, PA5/PA4/CN6/TIM6 vendor-documented design lock, required external ECHO divider, Keil target, host-side HC-SR04 tests, and verifier support complete. Physical wiring, trigger/echo pulses, real distance data, timeout behavior, and distance accuracy remain UNVERIFIED.
- Phase 3.2F: isolated OpenRF1 ground-sensor firmware foundation, X1/PC4 left TCRT5000 mapping, X2/PC5 right TCRT5000 mapping, X3/protected PB0 Hall mapping, X4 conflict documentation, independent debounce, Keil target, host-side tests, and verifier support complete. Physical wiring, voltage levels, active polarity, surface response, magnetic behavior, and serial periodicity remain UNVERIFIED.

Phase 3.2F does not implement motors, encoders, ESP32 WiFi firmware, mapping, SLAM, navigation, obstacle avoidance, physical C1 validation, sensor fusion, odometry, or full multisensor hardware integration. Automated tests do not access real COM ports, USB devices, GPIO, timer peripherals, I2C, flashing tools, WiFi, or sensors.

## Confirmed Hardware Inventory

Ranging:

- RPLIDAR C1 x2.
- HC-SR04 ultrasonic sensor x3.

Motion and pose:

- Wheel encoders associated with four drive motors.
- MPU6050 inertial measurement unit x1.

Ground and landmark:

- TCRT5000 reflective infrared sensor x2 for edge/drop detection.
- Hall sensor module x1 for magnetic landmark/checkpoint detection.

Environment:

- BH1750 illuminance sensor x1.
- BMP280 temperature/pressure sensor x1.

Controllers and chassis:

- STM32 controller board x1.
- ESP32 board x1.
- Battery/power system.
- Four encoded motors.
- Four mecanum wheels.
- Existing rover chassis.

Use neutral sensor IDs until installation is physically verified: `c1_1`, `c1_2`, `ultrasonic_1`, `ultrasonic_2`, `ultrasonic_3`, `tcrt5000_1`, `tcrt5000_2`, `bh1750_1`, `bmp280_1`, `mpu6050_1`, and `hall_1`.

Two C1 units physically exist. Both must be tested independently in Phase 2.5. One stable C1 is the baseline integration target. Simultaneous dual-C1 use is optional and remains UNVERIFIED until UART, GPIO, bandwidth, buffering, timing, and power feasibility are proven.

The software pipeline can now accept a bounded PC-direct C1 byte stream and save it as JSONL. Real physical C1 operation still requires manual Phase 2.5 hardware evidence before it can be marked VERIFIED.

## Phase 3.1 STM32 Sensor Telemetry

Phase 3.1 defines the transport-facing protocol `mars_scout_stm32_sensor_telemetry` version `1` for future STM32 low-rate sensor messages. It is newline-delimited UTF-8 JSON for software bring-up and later ESP32 forwarding. The persistent PC recording format remains `mars_scout_multisensor_recording` version `1`.

Generate deterministic STM32 telemetry:

```powershell
python -m rplidar_c1_tools.cli simulate-stm32-sensors --cycles 5 --scenario nominal --output .verification\phase3.1\synthetic_stm32_telemetry.jsonl --overwrite
```

Inspect telemetry:

```powershell
python -m rplidar_c1_tools.cli inspect-stm32-telemetry --input .verification\phase3.1\synthetic_stm32_telemetry.jsonl --output .verification\phase3.1\telemetry_inspection.txt
```

Convert telemetry into the existing Phase 2.4 recording format:

```powershell
python -m rplidar_c1_tools.cli record-stm32-telemetry --input .verification\phase3.1\synthetic_stm32_telemetry.jsonl --output .verification\phase3.1\converted_multisensor_recording.jsonl --overwrite
```

Supported Phase 3.1 sensor message types are `ultrasonic`, `ground_edge`, `hall_landmark`, `illuminance`, and `barometer`. HC-SR04 timeout is explicit and is not converted to distance zero. TCRT5000 and Hall raw states remain visible while polarity is UNVERIFIED. BH1750 and BMP280 support environmental-change indication only; reliable dust-storm detection is not claimed.

## Phase 3.2A OpenRF1 BH1750 Foundation

Phase 3.2A locks the software target for the first real STM32 sensor path: OpenRF1 robot controller, STM32F103RCT6, software I2C on PB1/SCL and PC3/SDA, GY-302/BH1750 sensor ID `bh1750_1`, public 7-bit address `0x23`, and USART1 PA9 TX / PA10 RX at 115200 baud 8N1. Recorded manual evidence marks firmware flash, CH340/USART1 telemetry, BH1750 communication at configured address `0x23`, a 500 ms telemetry period, and physical light response as MANUAL_EVIDENCE_VERIFIED; absolute lux calibration remains UNVERIFIED.

Generate deterministic BH1750-only telemetry:

```powershell
python -m rplidar_c1_tools simulate-bh1750-telemetry --samples 5 --output .verification\phase3.2a\mocked_bh1750_source.jsonl --overwrite
```

Capture from a mocked serial source and convert to the Phase 2.4 recording format:

```powershell
python -m rplidar_c1_tools capture-stm32-serial --mock-input .verification\phase3.2a\mocked_bh1750_source.jsonl --max-messages 5 --telemetry-output .verification\phase3.2a\mocked_bh1750_telemetry.jsonl --recording-output .verification\phase3.2a\mocked_bh1750_recording.jsonl --overwrite
```

Manual capture requires an operator-selected CH340 COM port; software never guesses a port:

```powershell
python -m rplidar_c1_tools capture-stm32-serial --port <USER_VERIFIED_COM_PORT> --baud 115200 --duration 30 --telemetry-output bh1750_telemetry.jsonl --recording-output bh1750_recording.jsonl --overwrite
```

Firmware source lives under `firmware/openrf1/app/`. It is application-layer source for the vendor OpenRF1 Keil MDK/uVision 5 STM32F103RC project. The committed Phase 3.2A evidence validates a manually recorded BH1750-only run; automated tests still use mocked/file-backed inputs and do not physically access the device.

## Phase 3.2B OpenRF1 Full-Hardware Foundation

Phase 3.2B keeps the Phase 3.2A BH1750-only project intact and adds a separate full-hardware firmware foundation under `firmware/openrf1/full_hardware/` with project file `firmware/openrf1/keil/OpenRF1_FullHardware.uvprojx`. The new Keil output is isolated under `Objects_FullHardware/` as `OpenRF1_FullHardware.hex`.

Software foundations include shared software-I2C transactions for BH1750/BMP280/MPU6050, BMP280 and MPU6050 pure conversion logic, raw digital filtering for TCRT5000/Hall, nonblocking HC-SR04 state machines, RPLIDAR C1 USART2 byte transport counters, and a versioned STM32-to-ESP32 USART3 binary frame contract. Phase 3.2B uses module-specific electrical evidence: BH1750 and MPU6050 module VCC -> 5 V, BMP280 and TCRT5000 VCC -> 3.3 V, Hall module -> 5 V with output measurement required, ESP32 external 5 V isolated from USB, and HC-SR04 Echo protection conditional on measured VOH. USART2/USART3 connector-to-MCU pins, PWM channel GPIOs, line-input GPIOs, BMP280/MPU6050 ACKs, polarity, power integrity, and real full-system sensor data remain UNVERIFIED.

Generate a deterministic Phase 3.2B telemetry fixture:

```powershell
python -m rplidar_c1_tools.cli simulate-stm32-sensors --cycles 2 --scenario phase32b_full_foundation --output .verification\phase3.2b\phase32b_full_telemetry.jsonl --overwrite
```

Convert it to the existing recording format:

```powershell
python -m rplidar_c1_tools.cli record-stm32-telemetry --input .verification\phase3.2b\phase32b_full_telemetry.jsonl --output .verification\phase3.2b\phase32b_full_recording.jsonl --overwrite
```

## Phase 3.2C OpenRF1 BMP280 Bring-Up

Phase 3.2C adds a BMP280-only physical bring-up target under `firmware/openrf1/bmp280_bringup/` with Keil project `firmware/openrf1/keil/OpenRF1_BMP280_Bringup.uvprojx`. Its output is isolated under `Objects_BMP280_Bringup/` as `OpenRF1_BMP280_Bringup.hex`.

The dedicated firmware expects only `bmp280_1` on software I2C PB1/SCL and PC3/SDA: VCC -> 3.3 V, GND -> GND, CSB -> 3.3 V for I2C mode, and SDO -> GND for address `0x76`. It probes `0x76`, reads chip ID register `0xD0`, expects `0x58`, reads calibration, writes `config = 0x80`, writes `ctrl_meas = 0x27`, and emits `environmental` JSONL every 500 ms on USART1 PA9/PA10 at 115200 8N1.

Committed evidence in `evidence/phase3.2c/` marks isolated BMP280 firmware flashing, USART1/CH340 JSONL telemetry, I2C ACK at `0x76`, chip ID `0x58`, calibration-register path for compensated output, `ctrl_meas = 0x27` and `config = 0x80` readback, continuous compensated temperature/pressure telemetry, exact 500 ms periodicity, and a stable 30-second capture as PHYSICAL_EVIDENCE_VERIFIED. Repository automation validates the evidence offline; it does not flash, open a COM port, or access hardware.

Absolute temperature accuracy, absolute pressure accuracy, environmental-reference comparison, long-duration operation beyond this capture, full shared-I2C concurrency, and complete full-hardware operation remain UNVERIFIED.

## Phase 3.2D OpenRF1 MPU6050 Bring-Up

Phase 3.2D adds an MPU6050-only firmware target under `firmware/openrf1/mpu6050_bringup/` with Keil project `firmware/openrf1/keil/OpenRF1_MPU6050_Bringup.uvprojx`. Its output is isolated under `Objects_MPU6050_Bringup/` as `OpenRF1_MPU6050_Bringup.hex`.

The dedicated firmware expects only `mpu6050_1` on software I2C PB1/SCL and PC3/SDA: GY-521/MPU6050 VCC -> OpenRF1 5 V, GND -> GND, SCL -> PB1/B1, SDA -> PC3/C3, and AD0 -> GND for the planned address `0x68`. INT, XDA, XCL, and FSYNC remain disconnected for polling bring-up. It probes `0x68`, reads WHO_AM_I register `0x75`, expects `0x68`, writes and reads back `PWR_MGMT_1 = 0x01`, `SMPLRT_DIV = 0x09`, `CONFIG = 0x03`, `GYRO_CONFIG = 0x00`, and `ACCEL_CONFIG = 0x00`, then reads 14-byte IMU bursts every 100 ms on USART1 PA9/PA10 at 115200 8N1.

No Phase 3.2D physical evidence is committed. MPU6050 ACK, WHO_AM_I, register readback, live acceleration/angular-rate/temperature telemetry, axis orientation, calibration, shared-I2C concurrency, and complete full-hardware operation remain UNVERIFIED.

## Phase 3.2E OpenRF1 HC-SR04 Bring-Up

Phase 3.2E adds an HC-SR04-only firmware target under `firmware/openrf1/hcsr04_bringup/` with Keil project `firmware/openrf1/keil/OpenRF1_HCSR04_Bringup.uvprojx`. Its output is isolated under `Objects_HCSR04_Bringup/` as `OpenRF1_HCSR04_Bringup.hex`.

AUTHORITATIVE_VENDOR_DOCUMENTED facts from the OpenRF1 vendor control-board package, ultrasonic sensor example, and OpenRF1 schematic revision dated 2024-07-01: CN6 B4B-PH-K-S(LF)(SN), pin 1: VCC_5V, pin 2: GND, pin 3: PA5_TRIG, pin 4: PA4_ECHO; TRIG: PA5; ECHO: PA4; TIM6 with prescaler 71 and period 30000 for nominal 1 us timing.

Do not connect HC-SR04 ECHO directly to CN6 pin 4. The software phase locks the external protection design as HC-SR04 ECHO -> 10 kOhm series resistor -> protected PA4 / CN6-pin-4 node; protected PA4 node -> 15 kOhm resistor -> GND. Physical resistor installation, connector orientation, ECHO voltages, trigger pulse, echo pulse, real distance data, timeout behavior, and absolute distance accuracy remain UNVERIFIED.

## Phase 3.2F OpenRF1 Ground-Sensor Bring-Up

Phase 3.2F adds a ground-sensor-only firmware target under `firmware/openrf1/ground_sensors_bringup/` with Keil project `firmware/openrf1/keil/OpenRF1_GroundSensors_Bringup.uvprojx`. Its output is isolated under `Objects_GroundSensors_Bringup/` as `OpenRF1_GroundSensors_Bringup.hex`.

AUTHORITATIVE_VENDOR_DOCUMENTED facts from the OpenRF1 vendor control-board package, OpenRF1 four-channel tracking example, and OpenRF1 schematic revision dated 2024-07-01: connector pin 1: GND, pin 2: X4 / schematic PC14, pin 3: X3 / PB0, pin 4: X2 / PC5, pin 5: X1 / PC4, pin 6: VCC_5V; signal 1 / X1 / PC4, signal 2 / X2 / PC5, and signal 3 / X3 / PB0. The old example maps X4 to PB1, so signal 4 / X4 is unused and excluded from Phase 3.2F.

The design-locked wiring contract powers both TCRT5000 modules from STM32 3.3 V, powers the Hall module from 5 V, and routes Hall S through the external 10 kOhm / 15 kOhm divider before PB0. Do not connect Hall S directly to PB0. Do not share one VCC rail across all three modules. Runtime telemetry reports numeric `raw_level` and `debounced_level` only; semantic polarity remains unverified.

## Preserved Verified C1 Facts

- Exact model in earlier verified files: SLAMTEC RPLIDAR C1M1-R2.
- Connector: XH2.54-5P housing, four active conductors and one unused position.
- Interface: 3.3 V TTL UART, 460800 baud, 8 data bits, no parity, 1 stop bit.
- Power: regulated 5.0 V supply, 4.8 V to 5.2 V allowed.
- Startup current: approximately 800 mA.
- Typical operating current: approximately 230 mA at 10 Hz.
- Maximum normal operating current: approximately 260 mA.
- Maximum specified supply ripple: 150 mV.
- Motor control: internal closed-loop motor control. There is no external motor PWM conductor.

Do not connect the LiDAR red wire to the ESP32 3.3 V pin. Do not invent GPIO, UART, I2C address, active polarity, connector order, or mounting-offset values.

## System Responsibilities

```text
RPLIDAR C1
    -> ESP32 -> WiFi -> PC visualization/recording

STM32 sensors and rover state
    -> ESP32 -> WiFi -> PC

HC-SR04 / TCRT5000 / relevant local state
    -> STM32 safety decision -> motor control -> rover motion

rover motion
    -> encoders / MPU6050 / sensors -> STM32 -> ESP32 -> PC
```

STM32 owns planned low-level motor safety and low-rate sensor acquisition. ESP32 is the planned WiFi/data bridge. PC software owns visualization, recording, replay, export, and later short-range accumulated mapping.

## Coordinate Convention

- `ScanPoint.angle_deg`: degrees, `0` forward, positive counterclockwise.
- `ScanPoint.distance_mm`: millimetres.
- Cartesian distances: metres.
- `+x`: rover forward.
- `+y`: rover left.
- Native C1 clockwise angles must be converted before `ScanFrame` creation.

Phase 2.3 polar view shows zero degrees at the top and positive angles counterclockwise. The point-cloud display shows rover forward at image top and rover left at image left.

## Recording And Replay

Phase 2.4 implements a human-readable, streamable UTF-8 JSON Lines format named `mars_scout_multisensor_recording` version `1`. The first line is a header containing the sensor inventory. Each following line is one complete record.

Create a deterministic two-C1 room session with auxiliary synthetic streams:

```powershell
python -m rplidar_c1_tools.cli record-synthetic --scene room --frames 3 --lidar-count 2 --include-aux --output .verification\phase2.4\synthetic_multisensor_room.jsonl
```

Inspect the recording:

```powershell
python -m rplidar_c1_tools.cli inspect-recording .verification\phase2.4\synthetic_multisensor_room.jsonl --output .verification\phase2.4\inspection.txt
```

Replay immediately:

```powershell
python -m rplidar_c1_tools.cli replay-recording .verification\phase2.4\synthetic_multisensor_room.jsonl
```

Render final replayed frames:

```powershell
python -m rplidar_c1_tools.cli render-recording .verification\phase2.4\synthetic_multisensor_room.jsonl --output-dir .verification\phase2.4
```

Generated recordings and figures under `.verification/` are ignored by Git.

## PC-Direct C1 Capture

Phase 2.5 adds `capture-c1`. Manual hardware capture requires a user-verified serial port; no COM port is guessed:

```powershell
python -m rplidar_c1_tools.cli capture-c1 --sensor-id c1_1 --port <USER_VERIFIED_PORT> --frames 1 --points-per-frame 360 --output data\raw\c1_1_pc_direct.jsonl
```

Automated verification uses safe hex fixture bytes instead of serial access:

```powershell
python -m rplidar_c1_tools.cli capture-c1 --sensor-id c1_1 --sample-hex 3d0100a00f3e012da00f3e015aa00f3e0187a00f --frames 1 --points-per-frame 4 --output .verification\phase2.5\c1_1_pc_direct_capture.jsonl
```

Captured files use the existing `mars_scout_multisensor_recording` JSONL schema. The driver converts native C1 clockwise angles into the project rover-frame `ScanPoint.angle_deg` convention before recording.

## Phase Verification

Supported phases include `phase1`, `phase2.1`, `phase2.2`, `phase2.3`, `phase2.4`, `phase2.5`, `phase3.1`, `phase3.2a`, `phase3.2b`, `phase3.2c`, `phase3.2d`, `phase3.2e`, and `phase3.2f`.

Development verification:

```powershell
.\tools\verify_phase.cmd phase2.5 -AllowDirty
.\tools\verify_phase.cmd phase3.1 -AllowDirty
.\tools\verify_phase.cmd phase3.2a -AllowDirty
.\tools\verify_phase.cmd phase3.2b -AllowDirty
.\tools\verify_phase.cmd phase3.2c -AllowDirty
.\tools\verify_phase.cmd phase3.2d -AllowDirty
.\tools\verify_phase.cmd phase3.2e -AllowDirty
.\tools\verify_phase.cmd phase3.2f -AllowDirty
```

Normal verification after commit and push:

```powershell
.\tools\verify_phase.cmd phase2.5
.\tools\verify_phase.cmd phase3.1
.\tools\verify_phase.cmd phase3.2a
.\tools\verify_phase.cmd phase3.2b
.\tools\verify_phase.cmd phase3.2c
.\tools\verify_phase.cmd phase3.2d
.\tools\verify_phase.cmd phase3.2e
.\tools\verify_phase.cmd phase3.2f
```

The verifier checks Git state, Python selection, pytest import, targeted tests, regressions, the complete PC suite, and configured smoke workflows. Hardware and safety facts still require physical verification.

## Revised Roadmap

- Phase 2.4: multi-sensor recording, replay, reproducible datasets, current hardware inventory update, and project-plan rebaseline.
- Phase 2.5: PC-direct testing of both RPLIDAR C1 units separately, real scan acquisition, distance/orientation checks, device identification, recording, and visualization.
- Phase 3.1: STM32 low-rate sensor telemetry software foundation, deterministic simulator, PC parser, recording bridge, and manual bring-up checklist.
- Phase 3.2A: OpenRF1 STM32F103RCT6 + GY-302/BH1750 firmware foundation, mocked serial-capture workflow, and manual bring-up procedure.
- Phase 3.2B: OpenRF1 multisensor and communications software foundation; physical integration remains future manual validation.
- Phase 3.2C: OpenRF1 BMP280-only physical bring-up firmware and recorded isolated BMP280 evidence; absolute accuracy and full shared-bus operation remain unverified.
- Phase 3.2D: OpenRF1 MPU6050-only software bring-up firmware; physical ACK, WHO_AM_I, live IMU telemetry, calibration, and axis orientation remain unverified.
- Phase 3.2E: OpenRF1 HC-SR04-only software bring-up firmware; physical wiring, pulses, real distance data, timeout behavior, and accuracy remain unverified.
- Phase 3.2F: OpenRF1 ground-sensor-only software bring-up firmware; physical wiring, voltage levels, active polarity, surface behavior, magnetic behavior, and serial periodicity remain unverified.
- Phase 4: wheel encoders, MPU6050, mecanum kinematics, closed-loop motion, and odometry.
- Phase 5: STM32-ESP32-computer communication, WiFi transport, one-C1 baseline integration, then optional dual-C1 feasibility evaluation.
- Phase 6: real-time PC visualization, rover trajectory, and short-range encoder/IMU-assisted accumulated 2D mapping.
- Phase 7: local autonomous obstacle stop/turn behavior.
- Phase 8: full Mars-like venue integration, environmental experiments, validation, reliability testing, and final presentation evidence.

Optional future extensions, not current requirements: reusable global SLAM mapping, loop closure, global path planning, autonomous frontier exploration, ROS, ROS 2, Nav2, AMCL, Gmapping, `slam_toolbox`, Raspberry Pi, Jetson, and vehicle-mounted Linux computers.
