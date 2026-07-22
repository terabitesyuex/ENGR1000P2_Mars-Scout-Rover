# OpenRF1 Unified Rover Application

This directory now contains two intentionally separate application families:

- The original root-level main.c, bh1750.c, soft_i2c.c, and related files
  remain the isolated Phase 3.2A BH1750 application. They are not moved or
  linked into rover control.
- The subdirectories below form the Phase 4 software-only rover-control
  architecture. Hardware mappings are injected through HAL callbacks and
  centralized configuration.

## Layering

    app/
      config/
        board_config.h
        sensor_config.h
      drivers/
        motor/
        encoder/
      rover_control/
        main_rover_control_foundation.c
      control/
        mecanum.c
        mecanum.h

Implemented in the current software foundation:

- drivers/motor: four-channel logical Motor HAL with an injected output
  backend and signed command range -1000..1000 permille.
- drivers/encoder: four-channel Encoder HAL with injected cumulative counts,
  software reset, and signed speed in counts per second.
- control/mecanum: fixed-point inverse kinematics from rover-frame
  vx_mm_s, vy_mm_s, and omega_mrad_s to four logical wheel speeds in
  milliradians per second. Callers must explicitly select the supported
  X-roller layout; the UNVERIFIED zero value is rejected.

Planned but not implemented by this task:

- PID speed control.
- Wheel odometry and IMU fusion.
- Unified sensor manager.
- STM32-to-ESP32 command/telemetry integration.
- RPLIDAR C1 UART integration.

Planned directories are added only when their implementation and tests exist;
README-only placeholders are intentionally omitted.

## Hardware Boundary

config/board_config.h contains every unresolved motor, encoder, geometry, and
future UART mapping as UNKNOWN, with readiness flags set to zero. No source in
the Motor HAL, Encoder HAL, or mecanum layer includes STM32 peripheral headers
or selects GPIO, timers, UARTs, connectors, wheel polarity, or a PWM frequency.

The encoder backend contract supplies a signed, cumulative 32-bit count after
quadrature decoding. A future STM32 backend must extend narrow hardware timer
wraps before exposing that value. Successive polls must be less than 2^31
counts apart so modulo-32-bit direction remains unambiguous. The Motor backend
translates a logical direction and duty permille into the vendor-specific
PWM/direction/enable scheme only after those details are verified.

The existing sensor bring-up directories remain independent:

- bmp280_bringup/
- ground_sensors_bringup/
- hcsr04_bringup/
- mpu6050_bringup/
- Phase 3.2A BH1750 root-level application files

No physical operation is verified by this architecture.

## Build And Test

Keil V5 project:

    firmware/openrf1/keil/OpenRF1_RoverControl_Foundation.uvprojx

The target uses ARM Compiler 6 for STM32F103RC and writes generated files only
under Objects_RoverControl_Foundation/. Its main function uses inert callbacks
and exists only to compile and link the software boundary. Do not flash this
foundation target.

Focused software checks:

    .\pc\.venv\Scripts\python.exe -m pytest pc\tests\test_openrf1_rover_control_foundation.py -v

Current status:

- Motor HAL, Encoder HAL, inverse kinematics, and the ARM Compiler 6 build are
  SOFTWARE_VERIFIED.
- Real PWM, direction control, encoder acquisition, wheel geometry, wheel
  motion, and all other physical behavior remain UNVERIFIED.
