# Hardware Lock

This file records hardware facts that must not drift silently during development. Unknown values remain explicit until physically verified.

## VERIFIED LiDAR Facts

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

## VERIFIED Wire Functions

| Wire color | Function | Connection rule |
| --- | --- | --- |
| Red | VCC, 5 V supply | Independent regulated 5 V supply |
| Yellow | LiDAR TX | ESP32 UART RX |
| Green | LiDAR RX | ESP32 UART TX |
| Black | GND | ESP32 GND and power-supply ground |
| Unused position | None | Leave unused |

## VERIFIED Electrical Values

- Supply voltage: 4.8 V to 5.2 V.
- Typical supply voltage: 5.0 V.
- Typical startup current: approximately 800 mA.
- Typical operating current: approximately 230 mA at 10 Hz.
- Maximum normal operating current: approximately 260 mA.
- Maximum specified power-supply ripple: 150 mV.
- UART voltage: 3.3 V TTL.
- UART baud rate: 460800.
- UART format: 8 data bits, no parity, 1 stop bit.

## MIXED ESP32-C3 SuperMini Configuration

- Selected ESP32 RX pin: UNSET. Candidate GPIO20 only after board label and documentation verification.
- Selected ESP32 TX pin: UNSET. Candidate GPIO21 only after board label and documentation verification.
- External motor PWM pin: VERIFIED not present and not allowed.
- LiDAR red wire to ESP32 3.3 V: prohibited.
- LiDAR TX to ESP32 TX: prohibited.
- LiDAR RX to ESP32 RX: prohibited.
- LiDAR and ESP32 common ground: required.

## PC Transport

- PC-direct transport for Phase 1: supplied USB-to-UART adapter at 460800 baud.
- ESP32-to-PC transport for later phases: native USB CDC when available, framed binary protocol.
- CSV point-per-line transport: not allowed for normal high-rate operation.

## UNVERIFIED Physical Values

- Power-supply model: UNVERIFIED.
- Physical wiring verification date: UNVERIFIED.
- Device firmware version: UNVERIFIED.
- Device hardware revision: UNVERIFIED.
- Redacted device serial number: UNVERIFIED. Never publish the complete serial number.
- Successful PC-direct test date: NOT RUN.

## Phase 1 Audit Status

- Repository audit date: 2026-07-14.
- Current Phase 1 scope: repository audit, hardware-fact locking, interface inventory, documentation consistency, and validation tooling.
- Live PC-direct LiDAR communication: NOT IMPLEMENTED in current Phase 1.
- Hardware lock validation command: `python tools/validate_hardware_lock.py`.
- Hardware lock validation test: `python -m pytest pc/tests/test_hardware_lock_validation.py -v`.

## Verification Checklist

- Confirm LiDAR wire colors against the original harness.
- Confirm ESP32-C3 SuperMini GPIO20 and GPIO21 availability before use.
- Confirm independent 5 V regulator can supply at least 1 A.
- Confirm grounds are common before connecting UART.
- Confirm USB adapter and ESP32 do not drive LiDAR RX at the same time.
- Confirm serial port is released after PC-direct tests.
