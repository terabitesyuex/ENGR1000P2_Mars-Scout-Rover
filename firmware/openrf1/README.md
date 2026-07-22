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

The BMP280 target is for one module on PB1/SCL and PC3/SDA with VCC on 3.3 V, CSB tied to 3.3 V, and SDO tied to GND for `0x76`. It does not run the BH1750 or full-hardware application. Committed Phase 3.2C evidence verifies isolated BMP280 ACK/address `0x76`, chip ID `0x58`, configuration readback, compensated live temperature/pressure telemetry, and 500 ms periodicity; absolute accuracy and full shared-bus operation remain UNVERIFIED.

Phase 3.2D adds a separate MPU6050-only bring-up target:

- MPU6050 bring-up source: `firmware/openrf1/mpu6050_bringup/`.
- MPU6050 bring-up project: `firmware/openrf1/keil/OpenRF1_MPU6050_Bringup.uvprojx`.
- MPU6050 bring-up output: `firmware/openrf1/keil/Objects_MPU6050_Bringup/OpenRF1_MPU6050_Bringup.hex`.

The MPU6050 target is for one GY-521/MPU6050 module on PB1/SCL and PC3/SDA with VCC on 5 V and AD0 tied to GND for the planned address `0x68`. It does not run the BH1750, BMP280, or full-hardware application. Physical MPU6050 ACK, WHO_AM_I, configuration readback, live IMU telemetry, calibration, axis orientation, and full shared-bus operation remain UNVERIFIED.

Phase 3.2E adds a separate HC-SR04-only bring-up target:

- HC-SR04 bring-up source: `firmware/openrf1/hcsr04_bringup/`.
- HC-SR04 bring-up project: `firmware/openrf1/keil/OpenRF1_HCSR04_Bringup.uvprojx`.
- HC-SR04 bring-up output: `firmware/openrf1/keil/Objects_HCSR04_Bringup/OpenRF1_HCSR04_Bringup.hex`.

The physical inventory contains three HC-SR04 modules, but this target is for one module on OpenRF1 CN6 only. Vendor-documented design locks CN6 pin 1: VCC_5V, pin 2: GND, pin 3: PA5_TRIG, pin 4: PA4_ECHO; TRIG: PA5; ECHO: PA4; timer: TIM6. CN6 uses a JST PH 2.0 mm `B4B-PH-K-S(LF)(SN)` header and requires a matching `PHR-4` cable; 2.54 mm Dupont leads must not be forced into it. Do not connect ECHO directly to CN6 pin 4; the external 10 kOhm / 15 kOhm divider is required before PA4 receives the signal.

The three modules may be validated sequentially, one at a time, on the single CN6 path. GPIO, connector, and timer resources for two additional simultaneous paths are UNVERIFIED and are not implemented by this target. Each future simultaneous ECHO path requires its own divider; divider midpoints must not be shared. Physical wiring, pulses, real distance data, timeout behavior, accuracy, staggered triggering, cross-talk, and simultaneous three-module operation remain UNVERIFIED. See the [hardware materials BOM](../../docs/hardware_materials_bom.md) and [HC-SR04 bring-up guide](../../docs/openrf1_hcsr04_bringup.md) before procurement or wiring.

Phase 3.2F adds a separate ground-sensor-only bring-up target:

- Ground-sensor bring-up source: `firmware/openrf1/ground_sensors_bringup/`.
- Ground-sensor bring-up project: `firmware/openrf1/keil/OpenRF1_GroundSensors_Bringup.uvprojx`.
- Ground-sensor bring-up output: `firmware/openrf1/keil/Objects_GroundSensors_Bringup/OpenRF1_GroundSensors_Bringup.hex`.

The Phase 3.2F target is for two TCRT5000 digital modules and one planned HW-477/A3144 Hall module on the OpenRF1 four-channel tracking connector only. Vendor-documented design locks signal 1 / X1 / PC4, signal 2 / X2 / PC5, signal 3 / X3 / PB0, and connector order; signal 4 remains unused because the X4 sources conflict. The target samples PC4, PC5, and PB0 as floating inputs every 5 ms, applies independent 4-sample debounce, and emits 50 ms JSONL numeric levels. A's isolated evidence verifies build/flash, installed PC4/PC5 TCRT connections, live raw/debounced response, and four gap-free 100-frame captures with exact 50 ms steady-state timestamps. Use TCRT5000 VCC -> 3.3 V, Hall + -> 5 V, and Hall S -> external 10 kOhm / 15 kOhm divider -> protected PB0. Do not connect Hall S directly to PB0. Actual voltages, polarity semantics, black/white/drop classification, Hall behavior, and full-hardware operation remain UNVERIFIED.

The Phase 3.2B source prepares bounded software foundations for the shared I2C signal bus, BMP280, MPU6050, HC-SR04, TCRT5000, Hall, RPLIDAR C1 byte transport, and STM32-to-ESP32 link. Module-specific evidence revises the proposed power domains, but USART2/USART3 pins, line-input pins, BMP280/MPU6050 ACKs, physical HC-SR04 Echo voltage, Hall output voltage, physical polarity, RPLIDAR operation, ESP32 operation, power integrity, and real full-system sensor data remain UNVERIFIED.

Build only; do not flash until the manual safety checklist is complete.
