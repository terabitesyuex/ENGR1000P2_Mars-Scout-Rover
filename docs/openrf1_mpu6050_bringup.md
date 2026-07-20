# OpenRF1 MPU6050 Bring-Up

Phase 3.2D adds an isolated MPU6050-only firmware target for bring-up on the OpenRF1 STM32F103RCT6 controller. Repository automation validates source, tests, fixtures, evidence documentation, and project structure only; it does not flash the MCU, open a COM port, access GPIO/I2C, or physically read the sensor.

## Hardware Facts

| Item | Value | Status |
| --- | --- | --- |
| Controller | OpenRF1 robot controller, STM32F103RCT6 | CONFIRMED by Phase 3.2A evidence |
| Sensor ID | `mpu6050_1` | MANUAL_EVIDENCE_VERIFIED for isolated bring-up |
| MPU6050 module count | x1 | CONFIRMED inventory |
| Module supply | GY-521/MPU6050 VCC -> OpenRF1 H4 5 V | MANUAL_EVIDENCE_VERIFIED for isolated bring-up |
| Ground | GY-521/MPU6050 GND -> OpenRF1 H4 GND | MANUAL_EVIDENCE_VERIFIED for isolated bring-up |
| I2C SCL | PB1 / SCL | MANUAL_EVIDENCE_VERIFIED for isolated bring-up |
| I2C SDA | PC3 / SDA | MANUAL_EVIDENCE_VERIFIED for isolated bring-up |
| Address strap | AD0 measured at 0 V | MANUAL_EVIDENCE_VERIFIED for deterministic address `0x68` |
| Unused pins | INT, XDA, XCL, FSYNC disconnected | PLANNED polling bring-up |
| Address | `0x68` | MANUAL_EVIDENCE_VERIFIED for isolated bring-up |
| WHO_AM_I register | `0x75` -> `0x68` | MANUAL_EVIDENCE_VERIFIED for isolated bring-up |
| Debug UART | USART1 PA9 TX / PA10 RX, 115200 8N1 through CH340 | CONFIRMED path from Phase 3.2A; port user-selected |

Do not mark absolute accuracy, calibration-time movement detection, calibration motion rejection, final rover-frame axis orientation, accelerometer offsets, yaw drift, shared-I2C behavior, or full-hardware operation as verified until real evidence exists.

## Firmware Target

- Source: `firmware/openrf1/mpu6050_bringup/`.
- Keil project: `firmware/openrf1/keil/OpenRF1_MPU6050_Bringup.uvprojx`.
- Output directory: `firmware/openrf1/keil/Objects_MPU6050_Bringup/`.
- Output HEX: `OpenRF1_MPU6050_Bringup.hex`.
- Shared reusable driver: `firmware/openrf1/full_hardware/mpu6050.c/.h`.

The target reuses the established STM32F103RC, `STM32F10X_HD`, `USE_STDPERIPH_DRIVER`, Arm Compiler 6, startup, system, USART1, SysTick, and software-I2C foundation. It does not modify the Phase 3.2A BH1750 target, the Phase 3.2C BMP280 target, or the Phase 3.2B full-hardware runtime.

## Initialization Sequence

1. Platform init with SysTick and bounded USART1 debug output.
2. Software-I2C init and bus recovery.
3. Probe address `0x68`.
4. Read WHO_AM_I register `0x75`.
5. Require WHO_AM_I value `0x68`.
6. Write and read back `PWR_MGMT_1 = 0x01`.
7. Wait a bounded 100 ms after wake-up.
8. Write and read back `SMPLRT_DIV = 0x09`.
9. Write and read back `CONFIG = 0x03`.
10. Write and read back `GYRO_CONFIG = 0x00`.
11. Write and read back `ACCEL_CONFIG = 0x00`.
12. Wait 5000 ms for startup warmup.
13. Collect 500 gyro samples at approximately 10 ms intervals.
14. Average X/Y/Z gyro bias from converted mdps values.
15. Read 14 bytes from `ACCEL_XOUT_H = 0x3B`.
16. Emit raw and scaled IMU telemetry every 100 ms.

The 100 ms wake-up wait is an initialization-only settle interval. Runtime sampling uses a monotonic deadline update and bounded telemetry writes.
The startup gyro-bias calibration is initialization-only and assumes the module remains still for approximately 12 seconds after power-on or reset. It does not implement movement detection or motion rejection.

## Telemetry

Each USART1 line is one UTF-8 JSON object using protocol `mars_scout_stm32_sensor_telemetry`, version `1`, sensor ID `mpu6050_1`.

Startup identity example:

```json
{"protocol":"mars_scout_stm32_sensor_telemetry","version":1,"sequence":0,"timestamp_ms":10,"message_type":"sensor_identity","sensor_id":"mpu6050_1","status":"ok","payload":{"sensor":"mpu6050","configured_address":"0x68","expected_who_am_i":"0x68","who_am_i":"0x68","initialization_stage":"running","error_code":null,"pwr_mgmt_1":"0x01","smplrt_div":"0x09","config":"0x03","gyro_config":"0x00","accel_config":"0x00","accel_range_g":2,"gyro_range_dps":250,"telemetry_period_ms":100}}
```

Successful sample example:

```json
{"protocol":"mars_scout_stm32_sensor_telemetry","version":1,"sequence":1,"timestamp_ms":110,"message_type":"imu","sensor_id":"mpu6050_1","status":"ok","payload":{"accel_raw":{"x":16384,"y":0,"z":0},"gyro_raw":{"x":131,"y":0,"z":0},"temperature_raw":0,"accel_g":{"x":1.000,"y":0.000,"z":0.000},"gyro_dps":{"x":1.000,"y":0.000,"z":0.000},"temperature_c":36.53}}
```

Error sample example:

```json
{"protocol":"mars_scout_stm32_sensor_telemetry","version":1,"sequence":1,"timestamp_ms":110,"message_type":"imu","sensor_id":"mpu6050_1","status":"nack","payload":{"accel_raw":null,"gyro_raw":null,"temperature_raw":null,"accel_g":null,"gyro_dps":null,"temperature_c":null,"initialization_stage":"read_who_am_i","operation":"read_who_am_i","register":"0x75","error_code":"nack"}}
```

No firmware path fabricates acceleration, angular rate, or temperature when I2C access, WHO_AM_I validation, configuration write/readback, calibration sampling, or burst reading fails. `gyro_raw` preserves raw register data. `gyro_dps` subtracts the startup dynamic gyro-bias estimate; `accel_g` and `temperature_c` are raw-register conversions. These values are not rover-frame orientation, odometry, navigation, or absolute-accuracy evidence.

## PC-Side Offline Fixtures

Small deterministic Phase 3.2D fixtures live under `data/test_vectors/phase3.2d/`.
They cover normal `sensor_identity`, normal `imu`, startup-delayed first output,
approximately 100 ms periodicity, error telemetry with null measurement fields,
malformed JSON rejection, wrong sensor ID rejection, sequence-gap rejection,
nondecreasing timestamp enforcement, and new-session sequence reset behavior.

## Manual Validation Procedure

Do not run this procedure from automated tests.

1. Confirm OpenRF1 is unpowered.
2. Wire only the GY-521/MPU6050 module: VCC -> 5 V, GND -> GND, SCL -> PB1/B1, SDA -> PC3/C3, AD0 -> GND.
3. Leave INT, XDA, XCL, and FSYNC disconnected for this polling bring-up.
4. Confirm supply voltage, polarity, common ground, and connector orientation with a meter before attaching the module.
5. Build `OpenRF1_MPU6050_Bringup.uvprojx` in Keil.
6. Flash `OpenRF1_MPU6050_Bringup.hex` with the established OpenRF1 flashing workflow.
7. Open the user-identified CH340 serial port at 115200 8N1.
8. Capture JSONL without recording the port number in committed files.
9. Keep the module still during startup warmup and gyro-bias calibration.
10. Pass criteria: identity line reports `status:"ok"`, `who_am_i:"0x68"`, the configured registers match the expected values above, and IMU samples arrive every approximately 100 ms with changing raw values when the module is moved.

Future physical evidence must keep raw files sanitized and must not record concrete port numbers, Windows usernames, absolute paths, Desktop paths, MCU unique serial numbers, or unrelated device identifiers.

## Recorded Manual Evidence

- Isolated firmware flashing and execution from Flash: MANUAL_EVIDENCE_VERIFIED.
- H4 connector order, MPU6050 wiring, AD0 at 0 V, 5 V supply level, SCL/SDA idle level, and continuity checks: MANUAL_EVIDENCE_VERIFIED.
- I2C ACK at `0x68`, WHO_AM_I `0x68`, and isolated configuration readback: MANUAL_EVIDENCE_VERIFIED.
- Live IMU JSON telemetry and approximately 10 Hz output: MANUAL_EVIDENCE_VERIFIED.
- Startup dynamic gyro-bias calibration and `gyro_raw` / bias-corrected `gyro_dps` semantics: MANUAL_EVIDENCE_VERIFIED.
- A's 15-second continuity test reported 151 frames, 15000 ms timestamp span, 100 ms median and maximum intervals, no sequence gaps greater than one, and largest sequence gap of one: MANUAL_EVIDENCE_VERIFIED.
- Manual rotation/flip produced expected isolated axis response: MANUAL_EVIDENCE_VERIFIED.

## Remaining Limitations

- Absolute acceleration accuracy, absolute angular-rate accuracy, calibration-time movement detection, calibration motion rejection, long-duration thermal drift, accelerometer offsets, yaw drift, axis orientation relative to the rover, and temperature accuracy remain UNVERIFIED.
- Shared-I2C operation with BH1750 and BMP280 remains UNVERIFIED.
- Complete full-hardware operation remains UNVERIFIED.
