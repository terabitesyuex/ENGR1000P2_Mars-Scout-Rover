# SUPERSEDED HISTORICAL COPY

Use repository-root `docs/lidar_hardware_profile.md` for current LiDAR hardware notes. Historical statements below may be stale.

# LiDAR Hardware Profile

## Device

- Manufacturer: SLAMTEC.
- Product family: RPLIDAR.
- Exact model: RPLIDAR C1M1-R2.
- Ranging principle: fusion DTOF.

## Performance

- Maximum sample rate: approximately 5000 samples per second.
- Scanning frequency: 8 Hz to 12 Hz.
- Typical scanning frequency: 10 Hz.
- Typical angular resolution: approximately 0.72 degrees.
- White-object range: approximately 0.05 m to 12 m.
- Low-reflectivity black-object range: approximately 0.05 m to 6 m.

## Electrical Interface

- Communication interface: 3.3 V TTL UART.
- UART baud rate: 460800.
- UART format: 8 data bits, no parity, 1 stop bit.
- Supply voltage: 4.8 V to 5.2 V.
- Typical supply voltage: 5.0 V.
- Typical startup current: approximately 800 mA.
- Typical operating current: approximately 230 mA at 10 Hz.
- Approximate maximum normal operating current: 260 mA.
- Maximum specified supply ripple: 150 mV.

## Connector

- Connector housing: XH2.54-5P.
- Active conductors: four.
- Unused connector position: one.

## Motor Control

The C1M1-R2 has internal closed-loop motor-speed control. There is no separate external motor PWM conductor in this cable. Firmware must not define a `MOTOR_PWM_GPIO` setting.
