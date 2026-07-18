# OpenRF1 MPU6050 Bring-Up

Phase 3.2D adds an isolated MPU6050-only firmware target for future bench bring-up on the OpenRF1 STM32F103RCT6 controller. Repository automation validates source, tests, and project structure only; it does not flash the MCU, open a COM port, access GPIO/I2C, or physically read the sensor.

## Hardware Facts

| Item | Value | Status |
| --- | --- | --- |
| Controller | OpenRF1 robot controller, STM32F103RCT6 | CONFIRMED by Phase 3.2A evidence |
| Sensor ID | `mpu6050_1` | PLANNED neutral ID |
| MPU6050 module count | x1 | CONFIRMED inventory |
| Module supply | GY-521/MPU6050 VCC -> OpenRF1 5 V | CONFIRMED_MODULE_EVIDENCE for module capability; not physically tested here |
| Ground | GY-521/MPU6050 GND -> OpenRF1 GND | PLANNED; PHYSICAL_VERIFICATION_REQUIRED |
| I2C SCL | PB1 / connector B1 | CONFIRMED OpenRF1 software-I2C signal |
| I2C SDA | PC3 / connector C3 | CONFIRMED OpenRF1 software-I2C signal |
| Address strap | AD0 -> GND | PLANNED for deterministic address `0x68` |
| Unused pins | INT, XDA, XCL, FSYNC disconnected | PLANNED polling bring-up |
| Address | `0x68` | PLANNED; ACK remains PHYSICAL_VERIFICATION_REQUIRED |
| WHO_AM_I register | `0x75` -> expected `0x68` | PHYSICAL_VERIFICATION_REQUIRED |
| Debug UART | USART1 PA9 TX / PA10 RX, 115200 8N1 through CH340 | CONFIRMED path from Phase 3.2A; port user-selected |

Do not mark the MPU6050 address, ACK, WHO_AM_I, configuration readback, live IMU telemetry, axis orientation, accelerometer offset, gyro bias, yaw drift, shared-I2C behavior, or full-hardware operation as verified until real evidence exists.

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
12. Read 14 bytes from `ACCEL_XOUT_H = 0x3B`.
13. Emit raw and scaled IMU telemetry every 100 ms.

The 100 ms wake-up wait is an initialization-only settle interval. Runtime sampling uses a monotonic deadline update and bounded telemetry writes.

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

No firmware path fabricates acceleration, angular rate, or temperature when I2C access, WHO_AM_I validation, configuration write/readback, or burst reading fails. The scaled `accel_g`, `gyro_dps`, and `temperature_c` values are raw-register conversions only; they are not calibrated motion, orientation, odometry, or navigation estimates.

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
9. Pass criteria: identity line reports `status:"ok"`, `who_am_i:"0x68"`, the configured registers match the expected values above, and IMU samples arrive every approximately 100 ms with changing raw values when the module is moved.

Future physical evidence must keep raw files sanitized and must not record concrete port numbers, Windows usernames, absolute paths, Desktop paths, MCU unique serial numbers, or unrelated device identifiers.

## Remaining Limitations

- MPU6050 ACK and WHO_AM_I are PHYSICAL_VERIFICATION_REQUIRED.
- Configuration readback is PHYSICAL_VERIFICATION_REQUIRED.
- Live acceleration, angular-rate, and temperature telemetry are PHYSICAL_VERIFICATION_REQUIRED.
- Absolute acceleration accuracy, gyro bias, accelerometer offsets, yaw drift, axis orientation relative to the rover, and temperature accuracy remain UNVERIFIED.
- Shared-I2C operation with BH1750 and BMP280 remains UNVERIFIED.
- Complete full-hardware operation remains UNVERIFIED.
