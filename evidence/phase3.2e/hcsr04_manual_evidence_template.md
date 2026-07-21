# TEMPLATE ONLY — NOT PHYSICAL EVIDENCE

This blank form is a workflow aid. It is not evidence, does not establish `MANUAL_EVIDENCE_VERIFIED`, and does not change `physical_status: PHYSICAL_VERIFICATION_REQUIRED`.

Before sharing or committing a completed candidate, remove the MCU unique ID, real username, absolute paths, credentials, proxy information, and any unredacted real COM port. Do not commit an unsanitized full FlyMcu log. A candidate must be converted to the validator's JSON schema and pass structural validation; that result still requires human review.

## Source and build record

- branch:
- full commit:
- test date:
- Keil project: `firmware/openrf1/keil/OpenRF1_HCSR04_Bringup.uvprojx`
- Keil target: `OpenRF1_HCSR04_Bringup`
- build date:
- build result:
- errors (A records actual count; expected acceptance is 0):
- warnings (A records actual count; expected acceptance is 0):
- HEX filename: `OpenRF1_HCSR04_Bringup.hex`
- HEX SHA256:
- firmware sensor_id:

## Wiring and electrical record — A MUST MEASURE

- actual connector orientation: UNVERIFIED UNTIL RECORDED
- common ground check: UNVERIFIED UNTIL RECORDED
- actual VCC: UNVERIFIED UNTIL RECORDED
- installed series resistor: UNVERIFIED UNTIL RECORDED
- installed resistor to GND: UNVERIFIED UNTIL RECORDED
- ECHO before divider voltage: UNVERIFIED UNTIL RECORDED
- ECHO after divider voltage: UNVERIFIED UNTIL RECORDED
- TRIG pulse: UNVERIFIED
- ECHO pulse: UNVERIFIED
- timer tick: UNVERIFIED

It is acceptable to retain `TRIG pulse: UNVERIFIED`, `ECHO pulse: UNVERIFIED`, and `timer tick: UNVERIFIED` when no oscilloscope measurement was performed. Do not invent results.

## Behavior and distance record — MANUAL EVIDENCE REQUIRED

- near-test reference distance:
- near-test reported distance:
- far-test reference distance:
- far-test reported distance:
- timeout behavior (must be error/null, never zero-distance substitution):
- recovery behavior after timeout:
- sequence/timestamp summary:

## Sanitized artifacts

- sanitized JSONL repository-relative path:
- sanitized summary repository-relative path:
- A manual conclusion:
- software PASS/FAIL:
- manual_review_required: true
- physical_status: PHYSICAL_VERIFICATION_REQUIRED
- still UNVERIFIED: absolute accuracy, useful range, field of view, long-duration stability, three-sensor operation, and full-hardware operation

The template itself is not evidence. A validator PASS means only “candidate evidence structurally valid”; only an independent human review can decide whether recorded manual evidence is acceptable.
