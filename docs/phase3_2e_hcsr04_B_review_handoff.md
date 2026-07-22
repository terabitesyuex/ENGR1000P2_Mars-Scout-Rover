# Phase 3.2E HC-SR04 Independent B Review Handoff

B works in a separate clean review worktree. B may inspect the diff, run tests/verifiers, audit protocol/parser/capture/evidence lifecycle, and return `APPROVE` or `REQUEST_CHANGES`.

B must not share C's development worktree, modify C's branch, push implementation, run an HC-SR04 physical test, create or merge a PR, or turn fixture/template data into physical evidence.

## Review checklist

- [ ] Confirm head branch `feature/c-hcsr04-validation-readiness` and the documented integration base; reject out-of-scope changes.
- [ ] Verify every legal firmware line fits 512 bytes including newline and the 513-byte buffer includes the NUL.
- [ ] Verify exact-fit success, one-byte-too-small rejection, overlong-input rejection, and no silent startup identity drop.
- [ ] Confirm the serial port is required/parameterized and no concrete COM port or local path is committed.
- [ ] Confirm unopened `serial.Serial()` construction; all properties plus `dtr=False` and `rts=False` precede `open()`.
- [ ] Confirm success retains raw pulse and converted distance; timeout/error retains null pulse/distance plus error metadata.
- [ ] Confirm a valid 1 us pulse rounding to 0 mm remains distinguishable from timeout.
- [ ] Confirm strict missing/unknown/negative/out-of-range/inconsistent field rejection and neutral sensor-ID rules.
- [ ] Confirm each capture is a new session, sequence/timestamp checks, gap/duplicate/rollback statistics, and timeout recovery.
- [ ] Inspect fixtures for credentials, user paths, concrete ports, unique IDs, or physical claims.
- [ ] Confirm template and fixture are not treated as real evidence; only sanitized `*_candidate.json` files may enter structural validation.
- [ ] Confirm validator PASS means only candidate structure is valid and physical status remains `PHYSICAL_VERIFICATION_REQUIRED`.
- [ ] Confirm bounded synchronous polling is described as isolated diagnostic-only, potentially blocking to timeout, and not the final runtime.
- [ ] Run HC-SR04 targeted/parser/capture/evidence/protocol regression tests.
- [ ] Run `python -m pytest pc/tests -q`.
- [ ] Run `cmd /c "tools\verify_phase.cmd phase3.1 -AllowDirty"` in review if the checkout is intentionally dirty, otherwise omit `-AllowDirty`.
- [ ] Run `cmd /c "tools\verify_phase.cmd phase3.2e -AllowDirty"` under the same rule.
- [ ] Run `git diff --check` and inspect `git status --short`.

The review response must list the exact reviewed commit and commands/results. `APPROVE` covers software readiness only; it is not `MANUAL_EVIDENCE_VERIFIED` and does not authorize hardware work, push, PR creation, or merge.
