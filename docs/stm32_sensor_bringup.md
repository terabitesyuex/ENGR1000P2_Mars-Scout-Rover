# STM32 Sensor Bring-Up Design

Phase 3.1 is a software foundation only. Physical STM32 sensor bring-up has not started.

## Firmware Audit Result

CONFIRMED:

- A `firmware/` directory exists.
- Existing `firmware/platformio.ini` targets ESP32-C3 Arduino/PlatformIO, not an authoritative STM32 target.
- Existing firmware files are LiDAR/transport/application skeletons and compile-time guards for unverified ESP32 LiDAR pins.

ABSENT:

- Authoritative STM32 MCU part number.
- Authoritative STM32 board revision.
- STM32CubeIDE `.ioc` project.
- STM32 HAL/LL target configuration.
- STM32 linker script or startup file.
- Keil project.
- Local STM32 compile command.

UNVERIFIED:

- GPIO assignments.
- Timer channels.
- UART assignments.
- I2C peripheral assignments.
- I2C bus addresses on real hardware.
- Connector orientation and pin order.
- Sensor supply voltage and logic voltage.

Because the exact STM32 target and toolchain are not authoritative, Phase 3.1 does not add production STM32 HAL code.

## Phase 3.2A OpenRF1 Update

The Phase 3.2A request supersedes the earlier unknown STM32 target for the BH1750 path only.

CONFIRMED for Phase 3.2A:

- Board: OpenRF1 robot controller.
- Manufacturer/manual source family: Yeahbot / Hangzhou Songjia Technology.
- MCU: STM32F103RCT6, 64 pins, ARM Cortex-M3, 256 KB flash, 48 KB SRAM.
- Intended toolchain: Keil MDK/uVision 5.
- Vendor examples use STM32F10x Standard Peripheral Library.
- Vendor target: STM32F103RC.
- Vendor defines: `STM32F10X_HD` and `USE_STDPERIPH_DRIVER`.
- Vendor examples include `startup_stm32f10x_hd.s`.
- Software I2C SCL: PB1.
- Software I2C SDA: PC3.
- I2C pull-ups: 10 kOhm to 3.3 V on PB1/SCL and PC3/SDA.
- I2C header supplies duplicated PC3/SDA, PB1/SCL, GND, and 5V rows.
- USART1 reference: PA9 TX, PA10 RX, 115200 baud, 8N1, CH340 USB serial path.

ABSENT from this repository:

- OpenRF1 vendor Keil project.
- STM32F10x Standard Peripheral Library source tree.
- Keil scatter/linker target metadata.
- `startup_stm32f10x_hd.s`.
- Local command-line Keil build configuration.

Phase 3.2A therefore adds application-layer source under `firmware/openrf1/app/` and manual Keil integration instructions. Recorded manual evidence verifies firmware flash, CH340/USART1 telemetry, BH1750 communication at configured address `0x23`, a 500 ms telemetry period, and physical light response. Absolute lux calibration remains UNVERIFIED.

## Phase 3.2B OpenRF1 Update

Phase 3.2B adds an isolated full-hardware software foundation under `firmware/openrf1/full_hardware/` and the separate Keil project `OpenRF1_FullHardware.uvprojx`. It prepares software for BMP280, MPU6050, HC-SR04, TCRT5000, Hall, RPLIDAR C1 byte transport, and STM32-to-ESP32 transport without performing hardware access.

CONFIRMED values include the Phase 3.2A OpenRF1 facts: PB1/SCL, PC3/SDA, USART1 PA9/PA10, STM32F103RCT6, and the compatible Keil/SPL toolchain. Recorded manual evidence verifies the BH1750-only `0x23` communication path and physical light response. USART2 pins, USART3 pins, PWM channel pins, line-input pins, BMP280/MPU6050 ACKs, HC-SR04 Echo VOH, Hall output voltage, physical polarity, and real full-system sensor data remain UNVERIFIED.

## Phase 3.2C OpenRF1 BMP280 Update

Phase 3.2C adds the isolated BMP280-only target `OpenRF1_BMP280_Bringup.uvprojx` and source under `firmware/openrf1/bmp280_bringup/`. It is for one BMP280 module on PB1/SCL and PC3/SDA only, with USART1 JSONL debug telemetry at 115200 8N1. It does not run BH1750, MPU6050, HC-SR04, TCRT5000, Hall, RPLIDAR, ESP32, motors, or encoders.

Committed Phase 3.2C evidence verifies the isolated BMP280-only path: firmware flash, CH340/USART1 JSONL telemetry, I2C ACK/address `0x76`, chip ID `0x58`, configuration readback `ctrl_meas = 0x27` and `config = 0x80`, calibration-register path sufficient for compensated output, live compensated temperature and pressure telemetry, exact 500 ms periodicity, no I2C errors, and a stable 30-second capture.

Absolute temperature accuracy, absolute pressure accuracy, environmental-reference comparison, operation beyond the 30-second capture, full multi-device shared-I2C concurrency, and complete full-hardware operation remain UNVERIFIED.

## Phase 3.2D OpenRF1 MPU6050 Update

Phase 3.2D adds the isolated MPU6050-only target `OpenRF1_MPU6050_Bringup.uvprojx` and source under `firmware/openrf1/mpu6050_bringup/`. It is for one GY-521/MPU6050 module on PB1/SCL and PC3/SDA only, with USART1 JSONL debug telemetry at 115200 8N1. It does not run BH1750, BMP280, HC-SR04, TCRT5000, Hall, RPLIDAR, ESP32, motors, or encoders.

The software target uses planned address `0x68` with AD0 grounded, expects WHO_AM_I `0x68`, writes and reads back `PWR_MGMT_1 = 0x01`, `SMPLRT_DIV = 0x09`, `CONFIG = 0x03`, `GYRO_CONFIG = 0x00`, and `ACCEL_CONFIG = 0x00`, then reads 14-byte IMU bursts from `ACCEL_XOUT_H = 0x3B` at a 100 ms telemetry period.

MPU6050 ACK, WHO_AM_I, configuration readback, live acceleration/angular-rate/temperature telemetry, absolute accuracy, gyro bias, accelerometer offsets, yaw drift, axis orientation, full multi-device shared-I2C concurrency, and complete full-hardware operation remain UNVERIFIED.

## Phase 3.2E OpenRF1 HC-SR04 Update

Phase 3.2E adds the isolated HC-SR04-only target `OpenRF1_HCSR04_Bringup.uvprojx` and source under `firmware/openrf1/hcsr04_bringup/`. It is for one HC-SR04 on the OpenRF1 CN6 ultrasonic connector only, with USART1 JSONL debug telemetry at 115200 8N1. It does not run BH1750, BMP280, MPU6050, TCRT5000, Hall, RPLIDAR, ESP32, motors, or encoders.

AUTHORITATIVE_VENDOR_DOCUMENTED values from the OpenRF1 vendor control-board package, ultrasonic sensor example, and OpenRF1 schematic revision dated 2024-07-01: CN6 B4B-PH-K-S(LF)(SN), pin 1: VCC_5V, pin 2: GND, pin 3: PA5_TRIG, pin 4: PA4_ECHO; TRIG: PA5; ECHO: PA4; TIM6 with prescaler 71 and period 30000 for a nominal 1 us count.

Do not connect HC-SR04 ECHO directly to CN6 pin 4. The external 10 kOhm / 15 kOhm divider is required before ECHO reaches PA4. Actual connector orientation, cable orientation, installed resistor values, ECHO voltage before/after division, physical trigger pulse, physical echo pulse, real distance data, physical timer accuracy, and physical timeout behavior remain UNVERIFIED.

## Future Runtime Constraints

- Do not use long blocking delays in embedded runtime paths.
- HC-SR04 acquisition should use a nonblocking state machine, input capture, or equivalent bounded timing design.
- Do not ping all three HC-SR04 units simultaneously.
- Make timeout and stale data explicit.
- Low-rate I2C sensors must not block local safety processing.
- TCRT5000 and Hall raw states must remain observable while polarity is verified.
- Safety behavior must not depend on a PC connection.

## Software Path Implemented

```text
deterministic STM32 telemetry simulator
    -> mars_scout_stm32_sensor_telemetry v1
    -> strict PC parser
    -> Phase 2.4 recording bridge
    -> inspect-recording
```

No serial port, USB device, GPIO, I2C bus, timer, network socket, or real sensor is accessed by this path.

