# Phase 3.2E HC-SR04 A Test Card

`C SOFTWARE PREP ONLY` — C did not access hardware, did not run Keil or FlyMcu, and did not open a real serial port. Every result below is `UNVERIFIED UNTIL RECORDED` by A.

## Exact source and build

- Branch: `feature/c-hcsr04-validation-readiness`
- Exact commit: `<EXACT_COMMIT_FROM_C_HANDOFF>`
- Keil project: `firmware/openrf1/keil/OpenRF1_HCSR04_Bringup.uvprojx`
- Keil target: `OpenRF1_HCSR04_Bringup`
- Expected HEX: `firmware/openrf1/keil/Objects_HCSR04_Bringup/OpenRF1_HCSR04_Bringup.hex`

A must checkout/pull the stated branch and confirm the exact commit before building. Rebuild the exact target and record the real date, result, HEX filename/hash, error count, and warning count. Acceptance requires 0 errors and 0 warnings.

`C DID NOT RUN KEIL` — `A MUST RECORD THE REAL BUILD RESULT`. Select the exact generated HEX in FlyMcu; do not reuse a similarly named or older image.

## Wiring safety — A MUST MEASURE

1. Disconnect all power before changing wiring.
2. Check printed board/module labels; actual connector and cable orientation are unverified.
3. Connect only one HC-SR04 for this isolated test, using neutral ID `ultrasonic_1`.
4. Confirm common ground.
5. Direct HC-SR04 ECHO-to-PA4/CN6-pin-4 is prohibited.
6. Install and measure the required divider: ECHO → 10 kOhm series → protected PA4 node; protected node → 15 kOhm → GND.
7. Before connecting the protected node to PA4, power safely and record actual VCC and ECHO voltages before/after the divider. Remove power again before final connection.

These checks are `MANUAL EVIDENCE REQUIRED`. Do not infer actual resistance, voltage, connector orientation, pulse timing, range, or accuracy from the software constants.

## Capture

A chooses the real port locally and must redact it from submitted evidence. Run from the prepared Python environment:

```powershell
python -m rplidar_c1_tools capture-openrf1-hcsr04 --port "<USER_VERIFIED_COM_PORT>" --baud 115200 --duration 30 --raw-output ".verification/phase3.2e/A_raw.jsonl" --summary-output ".verification/phase3.2e/A_summary.json"
```

The startup grace is a configurable host allowance, not a physically verified sensor-start time. Keep the unmodified raw JSONL locally, prepare sanitized repository-relative artifacts for review, and do not submit a real COM port or absolute path.

## Behavior sequence — MANUAL EVIDENCE REQUIRED

- Near test: record reference distance and reported pulse/distance behavior with a stable hard target.
- Far test: move the same target farther and record reference distance and changed pulse/distance behavior.
- Timeout test: safely remove or strongly angle the target; verify an explicit error with null `echo_pulse_us` and null `distance_mm`, never a fabricated zero distance.
- Recovery test: restore the target and confirm a later valid success record in the same session.
- Optional instrumentation: record TRIG, ECHO, and timer timing if actually measured. Otherwise record each as `UNVERIFIED`.

## Files A must return

- Completed sanitized evidence candidate containing branch/full commit/date, exact Keil project/target, actual build result/counts, HEX filename/SHA256, sensor ID, wiring/electrical records, behavior records, capture summary, relative artifact paths, and A conclusion.
- Sanitized raw JSONL and sanitized summary referenced by that candidate, with local identifiers removed.
- Explicit software PASS/FAIL plus `manual_review_required: true`.

Even a software PASS leaves actual waveform, exact 100 ms timing, actual 10 us trigger, voltages, timer accuracy, connector orientation, divider values, range, field of view, and absolute accuracy `UNVERIFIED` unless each is measured and independently accepted. Physical status remains `PHYSICAL_VERIFICATION_REQUIRED` pending review.
