# SUPERSEDED HISTORICAL COPY

This nested document is not the current hardware lock. Use the repository-root `HARDWARE_LOCK.md` for confirmed inventory, preserved electrical facts, planned responsibilities, and UNVERIFIED values. Historical statements below may describe earlier single-C1 assumptions.

# Hardware Lock

This file records historical hardware facts only. The authoritative hardware lock is the repository-root `HARDWARE_LOCK.md`. Current inventory has exactly one physical RPLIDAR C1M1-R2 (`c1_1`); there is no second physical C1. Unknown values remain explicit until physically verified.

## LiDAR

- Exact model: SLAMTEC RPLIDAR C1M1-R2.
- Connector type: XH2.54-5P.
- Active conductors: four.
- Unused connector position: one unused position in the five-pin housing.
- Ranging principle: fusion DTOF.
- Typical scan frequency: 10 Hz.
- Scan frequency range: 8 Hz to 12 Hz.
- Maximum sample rate: approximately 5000 samples per second.
- White-object range: approximately 50 mm to 12000 mm.
- Low-reflectivity black-object range: approximately 50 mm to 6000 mm.

## Wire Functions

| Wire color | Function | Connection rule |
| --- | --- | --- |
| Red | VCC, 5 V supply | Independent regulated 5 V supply |
| Yellow | LiDAR TX | ESP32 UART RX |
| Green | LiDAR RX | ESP32 UART TX |
| Black | GND | ESP32 GND and power-supply ground |
| Unused position | None | Leave unused |

## Electrical Values

- Supply voltage: 4.8 V to 5.2 V.
- Typical supply voltage: 5.0 V.
- Typical startup current: approximately 800 mA.
- Typical operating current: approximately 230 mA at 10 Hz.
- Maximum normal operating current: approximately 260 mA.
- Maximum specified power-supply ripple: 150 mV.
- UART voltage: 3.3 V TTL.
- UART baud rate: 460800.
- UART format: 8 data bits, no parity, 1 stop bit.

## ESP32-C3 SuperMini Configuration

- Selected ESP32 RX pin: UNSET. Candidate GPIO20 only after board label and documentation verification.
- Selected ESP32 TX pin: UNSET. Candidate GPIO21 only after board label and documentation verification.
- External motor PWM pin: not present and not allowed.
- LiDAR red wire to ESP32 3.3 V: prohibited.
- LiDAR TX to ESP32 TX: prohibited.
- LiDAR RX to ESP32 RX: prohibited.
- LiDAR and ESP32 common ground: required.

## PC Transport

- PC-direct transport for Phase 1: supplied USB-to-UART adapter at 460800 baud.
- ESP32-to-PC transport for later phases: native USB CDC when available, framed binary protocol.
- CSV point-per-line transport: not allowed for normal high-rate operation.

## Unresolved Physical Values

- Power-supply model: UNVERIFIED.
- Physical wiring verification date: UNVERIFIED.
- Device firmware version: UNVERIFIED.
- Device hardware revision: UNVERIFIED.
- Redacted device serial number: UNVERIFIED. Never publish the complete serial number.
- Successful PC-direct test date: NOT RUN.

## Verification Checklist

- Confirm LiDAR wire colors against the original harness.
- Confirm ESP32-C3 SuperMini GPIO20 and GPIO21 availability before use.
- Confirm independent 5 V regulator can supply at least 1 A.
- Confirm grounds are common before connecting UART.
- Confirm USB adapter and ESP32 do not drive LiDAR RX at the same time.
- Confirm serial port is released after PC-direct tests.
