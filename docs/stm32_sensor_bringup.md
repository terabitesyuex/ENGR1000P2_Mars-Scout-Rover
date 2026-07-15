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

Phase 3.2A therefore adds application-layer source under `firmware/openrf1/app/` and manual Keil integration instructions. Successful compilation, flashing, ACK at `0x23`, CH340 COM-port identity, and real lux telemetry remain MANUAL_ACTION_REQUIRED.

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

