# Phase 1 Hardware Audit

Date: 2026-07-14.

Current Phase 1 scope: repository audit, hardware-fact locking, interface inventory, documentation consistency, and validation tooling. Live LiDAR communication is outside this phase.

## Supersession Note

On 2026-07-15, Phase 2.4 rebaselined the inventory and project plan. This Phase 1 audit is HISTORICAL context only. Current authoritative inventory is maintained in `HARDWARE_LOCK.md`, `PROJECT_SPEC.md`, and `README.md`; the current physical LiDAR inventory is one RPLIDAR C1M1-R2 with ID `c1_1`. Older two-C1 statements in this audit are retained as historical evidence and do not prove a second current physical device.

## Source-Of-Truth Review

Priority used for this audit:

1. Existing repository files that clearly contain verified project decisions.
2. Confirmed facts explicitly provided in the current task.
3. Device labels and user-provided physical observations documented in the repository.
4. Official manufacturer documentation already stored or cited in the repository.
5. Everything else remains UNVERIFIED.

The audit did not use internet browsing and did not read files outside the Git repository.

## VERIFIED Hardware Facts

- LiDAR model: SLAMTEC RPLIDAR C1M1-R2.
- Connector housing: XH2.54-5P.
- Active conductors: four active wires plus one unused connector position.
- Wire functions: red VCC, yellow LiDAR TX, green LiDAR RX, black GND.
- LiDAR supply: 4.8 V to 5.2 V, typical 5.0 V.
- Startup current: approximately 800 mA.
- Typical operating current: approximately 230 mA at 10 Hz.
- Maximum normal operating current: approximately 260 mA.
- Maximum supply ripple: 150 mV.
- UART voltage: 3.3 V TTL.
- UART baud rate: 460800.
- UART format: 8 data bits, no parity, 1 stop bit.
- External motor PWM conductor: not present.

## UNVERIFIED Values

- ESP32-C3 SuperMini LiDAR RX GPIO.
- ESP32-C3 SuperMini LiDAR TX GPIO.
- Physical confirmation that GPIO20 and GPIO21 are available on the exact board.
- Power-supply model.
- Physical wiring verification date.
- Device firmware version.
- Device hardware revision.
- Redacted device serial identifier.
- Successful PC-direct evidence date: MANUAL_EVIDENCE_VERIFIED on 2026-07-22.
- Exact connector orientation on the physical harness.
- Voltage and polarity measurement evidence for the assembled wiring.

## Documentation Conflicts

### Resolved: Phase 1 Scope

Existing Phase 0 documents described Phase 1 as live PC-direct verification. The current task supersedes that assumption and defines Phase 1 as repository audit, hardware-fact locking, interface inventory, documentation consistency, and validation tooling.

Resolution:

- Updated `PROJECT_SPEC.md` Phase 1 acceptance criteria.
- Updated `README.md`, `docs/test_plan.md`, `docs/architecture.md`, `pc_direct/README.md`, and PC-direct placeholder messages.
- Kept PC-direct verification as a future hardware procedure.
- Did not implement live PC-direct communication.

## Safety Notes

- Do not mark physical wiring safe until voltage, polarity, and connector orientation have direct evidence.
- Do not set ESP32 UART GPIO values until the exact ESP32-C3 SuperMini board labels and documentation are verified.
- Do not connect the LiDAR red wire to the ESP32 3.3 V pin.
- Do not drive LiDAR RX from both the USB adapter and ESP32.
- Do not add an external motor PWM configuration.

## Validation

The Phase 1 validation tool checks the hardware lock, unresolved GPIO policy, firmware compile-time guards, and documentation consistency. It is intentionally implemented with the Python standard library.
