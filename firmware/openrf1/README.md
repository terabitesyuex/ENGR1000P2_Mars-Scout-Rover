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

Compilation, flashing, serial readout, ACK verification at `0x23`, and lux validation are MANUAL_ACTION_REQUIRED until performed and documented.
