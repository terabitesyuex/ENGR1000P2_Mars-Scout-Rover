# OpenRF1 STM32F103RCT6 Firmware Foundation

Phase 3.2A adds an application-layer firmware foundation for one GY-302/BH1750 illuminance sensor on the OpenRF1 controller.

This directory is not a complete standalone Keil project because the repository does not contain the OpenRF1 vendor project, STM32F10x Standard Peripheral Library, startup file, scatter file, or Keil target metadata. Apply the files in `app/` to the vendor Keil MDK/uVision 5 STM32F103RC project that already provides those licensed components.

## Confirmed Target Facts

- Board: OpenRF1 robot controller.
- MCU: STM32F103RCT6, vendor target STM32F103RC.
- Toolchain intended by vendor material: Keil MDK/uVision 5.
- Vendor defines: `STM32F10X_HD` and `USE_STDPERIPH_DRIVER`.
- Vendor examples use STM32F10x Standard Peripheral Library and `startup_stm32f10x_hd.s`.
- Software I2C SCL: PB1.
- Software I2C SDA: PC3.
- BH1750 sensor ID: `bh1750_1`.
- BH1750 public 7-bit address: `0x23` with GY-302 ADDR planned to GND.
- Telemetry UART: USART1, PA9 TX, PA10 RX, 115200 baud, 8N1.

## Manual Keil Integration

1. Open the vendor OpenRF1 STM32F103RC Keil project.
2. Confirm the target is STM32F103RC/F1, not STM32F4.
3. Confirm `STM32F10X_HD` and `USE_STDPERIPH_DRIVER` are defined.
4. Confirm `startup_stm32f10x_hd.s` and the matching STM32F103RC memory layout are used.
5. Ensure the project include path can find `stm32f10x.h` and Standard Peripheral Library headers.
6. Provide definitions for the three platform interfaces declared by `app/main.h`:
   - `openrf1_platform_init()` initializes the required platform time base and USART1 at 115200 baud, 8N1.
   - `openrf1_millis()` returns a monotonic wrapping `uint32_t` millisecond tick.
   - `openrf1_usart1_write()` transmits a null-terminated telemetry JSONL string through USART1.
7. If the vendor project already contains `main()`, merge the Phase 3.2A initialization and polling loop into that existing function; do not compile two `main()` definitions.
8. Add the remaining files from `app/` to the application group.
9. Build only and resolve every compiler and linker error; do not flash until wiring and safety checks are complete.

Keil build is SOFTWARE_VERIFIED for the local baseline project. Recorded manual evidence verifies firmware flash, CH340/USART1 telemetry, BH1750 communication at configured address `0x23`, a 500 ms telemetry period, and physical light response. Absolute lux calibration remains UNVERIFIED.

## Phase 3.2B Full-Hardware Software Foundation

Phase 3.2B adds a separate full-hardware software foundation under `full_hardware/` and a separate Keil project:

- BH1750-only source: `firmware/openrf1/app/`.
- BH1750-only project: `firmware/openrf1/keil/OpenRF1_BH1750.uvprojx`.
- BH1750-only output: `firmware/openrf1/keil/Objects/OpenRF1_BH1750.hex`.
- Full-hardware source: `firmware/openrf1/full_hardware/`.
- Full-hardware project: `firmware/openrf1/keil/OpenRF1_FullHardware.uvprojx`.
- Full-hardware output: `firmware/openrf1/keil/Objects_FullHardware/OpenRF1_FullHardware.hex`.

Phase 3.2C adds a separate BMP280-only bring-up target:

- BMP280 bring-up source: `firmware/openrf1/bmp280_bringup/`.
- BMP280 bring-up project: `firmware/openrf1/keil/OpenRF1_BMP280_Bringup.uvprojx`.
- BMP280 bring-up output: `firmware/openrf1/keil/Objects_BMP280_Bringup/OpenRF1_BMP280_Bringup.hex`.

The BMP280 target is for one module on PB1/SCL and PC3/SDA with VCC on 3.3 V, CSB tied to 3.3 V, and SDO tied to GND for the planned `0x76` address. It does not run the BH1750 or full-hardware application. Physical BMP280 ACK, chip ID, and live readings remain manual validation.

The Phase 3.2B source prepares bounded software foundations for the shared I2C signal bus, BMP280, MPU6050, HC-SR04, TCRT5000, Hall, RPLIDAR C1 byte transport, and STM32-to-ESP32 link. Module-specific evidence revises the proposed power domains, but USART2/USART3 pins, PWM channel pins, line-input pins, BMP280/MPU6050 ACKs, HC-SR04 Echo VOH, Hall output voltage, physical polarity, RPLIDAR operation, ESP32 operation, power integrity, and real full-system sensor data remain UNVERIFIED.

Build only; do not flash until the manual safety checklist is complete.
