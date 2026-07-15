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

