# OpenRF1 BMP280 Bring-Up

Phase 3.2C adds an isolated BMP280-only firmware target for physical bench bring-up on the OpenRF1 STM32F103RCT6 controller. Repository automation builds and tests software only; it does not flash the MCU, open a COM port, access GPIO/I2C, or prove real sensor readings.

## Hardware Facts

| Item | Value | Status |
| --- | --- | --- |
| Controller | OpenRF1 robot controller, STM32F103RCT6 | CONFIRMED by Phase 3.2A evidence |
| Sensor ID | `bmp280_1` | PLANNED neutral ID |
| BMP280 module count | x1 | CONFIRMED inventory |
| Supply | BMP280 VCC -> OpenRF1 3.3 V only | CONFIRMED_MODULE_EVIDENCE |
| Ground | BMP280 GND -> OpenRF1 GND | PLANNED for this bring-up |
| I2C SCL | PB1 / connector B1 | CONFIRMED OpenRF1 software-I2C signal |
| I2C SDA | PC3 / connector C3 | CONFIRMED OpenRF1 software-I2C signal |
| I2C mode strap | CSB -> 3.3 V | PLANNED |
| Address strap | SDO -> GND | PLANNED |
| Expected address | `0x76` | PLANNED from SDO grounded; real ACK UNVERIFIED |
| Expected chip ID register | `0xD0` -> `0x58` | PLANNED register check; physical read UNVERIFIED |
| Debug UART | USART1 PA9 TX / PA10 RX, 115200 8N1 through CH340 | CONFIRMED path from Phase 3.2A; COM port user-selected |

Do not power the BMP280-3.3 module from the OpenRF1 I2C 5 V pin. Power off before changing wiring. Do not connect BH1750, MPU6050, ultrasonic, TCRT5000, Hall, RPLIDAR, ESP32, motors, or encoders for this target.

## Firmware Target

- Source: `firmware/openrf1/bmp280_bringup/`.
- Keil project: `firmware/openrf1/keil/OpenRF1_BMP280_Bringup.uvprojx`.
- Output directory: `firmware/openrf1/keil/Objects_BMP280_Bringup/`.
- Output HEX: `OpenRF1_BMP280_Bringup.hex`.
- Shared reusable driver: `firmware/openrf1/full_hardware/bmp280.c/.h`.

The target reuses the established STM32F103RC, `STM32F10X_HD`, `USE_STDPERIPH_DRIVER`, Arm Compiler 6, startup, system, USART1, SysTick, and software-I2C foundation. It does not modify the Phase 3.2A BH1750 target or enable the Phase 3.2B full-hardware runtime.

## Initialization Sequence

1. Platform init with SysTick and bounded USART1 debug output.
2. Software-I2C init and bus recovery.
3. Probe address `0x76`.
4. Read chip ID register `0xD0`.
5. Require chip ID `0x58`.
6. Read BMP280 calibration registers.
7. Write `config = 0x80` for 500 ms standby and filter off.
8. Write `ctrl_meas = 0x27` for temperature x1, pressure x1, normal mode.
9. Read back configuration registers.
10. Emit compensated temperature and pressure every 500 ms.

## Telemetry

Each USART1 line is one UTF-8 JSON object using protocol `mars_scout_stm32_sensor_telemetry`, version `1`, sensor ID `bmp280_1`.

Startup identity example:

```json
{"protocol":"mars_scout_stm32_sensor_telemetry","version":1,"sequence":0,"timestamp_ms":12,"message_type":"sensor_identity","sensor_id":"bmp280_1","status":"ok","payload":{"configured_address":"0x76","expected_chip_id":"0x58","chip_id":"0x58","initialization_stage":"running","error_code":null,"ctrl_meas":"0x27","config":"0x80"}}
```

Successful sample example:

```json
{"protocol":"mars_scout_stm32_sensor_telemetry","version":1,"sequence":1,"timestamp_ms":512,"message_type":"environmental","sensor_id":"bmp280_1","status":"ok","payload":{"temperature_c":25.08,"pressure_pa":100653}}
```

Error sample example:

```json
{"protocol":"mars_scout_stm32_sensor_telemetry","version":1,"sequence":1,"timestamp_ms":512,"message_type":"environmental","sensor_id":"bmp280_1","status":"nack","payload":{"temperature_c":null,"pressure_pa":null,"initialization_stage":"probe_address","error_code":"nack"}}
```

No firmware path fabricates temperature or pressure when I2C access, chip ID validation, calibration read, configuration, raw read, or compensation fails.

## Manual Bring-Up Procedure

1. Confirm OpenRF1 is unpowered.
2. Wire only the BMP280 module: VCC -> 3.3 V, GND -> GND, SCL -> PB1/B1, SDA -> PC3/C3, CSB -> 3.3 V, SDO -> GND.
3. Confirm 3.3 V polarity and common ground with a meter before attaching the module.
4. Build `OpenRF1_BMP280_Bringup.uvprojx` in Keil.
5. Flash `OpenRF1_BMP280_Bringup.hex` with FlyMcu or the established OpenRF1 flashing workflow.
6. Open the user-identified CH340 serial port at 115200 8N1.
7. Capture JSONL without recording the COM number in committed files.
8. Pass criteria: identity line reports `status:"ok"`, `chip_id:"0x58"`, `ctrl_meas:"0x27"`, `config:"0x80"`, and environmental samples arrive every approximately 500 ms with plausible live values.

Physical BMP280 ACK, chip ID, calibration read, configuration readback, live temperature, and live pressure are MANUAL_ACTION_REQUIRED. They must not be marked verified until captured telemetry evidence is sanitized and committed in a later requested phase.
