# Phase 4C Agent Prompt

Copy the prompt below into the new software-development agent.

```text
You are taking over near-term software development for the ENGR1000P2 Mars
Scout Rover repository. Treat the current workspace as `<repository-root>` and
perform all work inside it.

The user reports that the complete rover has been assembled according to the
repository wiring plan. A 2026-07-23 evidence batch records exterior and
underside-sensor photographs, MPU6050 orientation, supplied geometry, C1
height, and HC-SR04 CAD tuples. Treat those records as bounded mounting evidence,
not electrical or operational evidence. No continuity results, voltage readings,
serial captures, motor motion, or integrated-system evidence have been recorded.

Your immediate scope is Phase 4C software-only preparation for real OpenRF1
motor and encoder bring-up. Do not access hardware, open a serial port, flash,
power motors, or issue motion commands unless the user separately and explicitly
authorizes those actions after the documented safety prerequisites are met.

Before editing:

1. Work only inside the repository.
2. Read AGENTS.md and all nested guidance.
3. Run git status and identify the current branch/HEAD.
4. Stay on main and do not create another branch unless explicitly requested.
5. Preserve all user changes and existing bring-up targets.
6. Read these sources in order:
   - docs/near_term_vehicle_bringup_handoff.md
   - HARDWARE_LOCK.md
   - TODO_HARDWARE.md
   - docs/openrf1_rover_wiring_plan.md
   - docs/openrf1_rover_wiring_plan_zh.md
   - docs/phase4a_mecanum_kinematics_odometry_foundation.md
   - docs/phase4b_closed_loop_motion_control_foundation.md
7. Do not merge phase3.2e-hcsr04-bringup tip 17c6cd5 into main. It contains
   generated Keil Objects_HCSR04_Bringup output only; the source implementation
   is already represented in main.

Current critical software facts:

- firmware/openrf1/app/rover_control/main_rover_control_foundation.c uses inert
  motor callbacks and returns encoder count zero. It is link-only and must not
  be flashed as operational firmware.
- firmware/openrf1/app/config/board_config.h still marks motor, encoder, geometry,
  C1 UART, and ESP32 UART readiness as zero.
- Phase 4A and Phase 4B algorithms are software-verified foundations. Supplied
  geometry is recorded at 0.1 mm precision, but signs, roller handedness,
  counts, tolerances, and physical performance remain unresolved; Phase 4B is
  not integrated as an operational STM32 motor loop.
- The Phase 3.2B full-hardware target still contains no-op/placeholder physical
  acquisition paths and is not a complete rover application.
- There is no operational ESP32-C3 WiFi firmware in the repository.

Implement the first bounded Phase 4C deliverable:

Progress recorded 2026-08-02: the separate encoder-only observation and
fail-disabled one-wheel motor subsets are complete under
`firmware/openrf1/encoder_bringup/` and
`firmware/openrf1/motor_bringup/`. Both have zero-error/zero-warning ARM
Compiler 6.24 builds and host boundary tests. Do not reimplement or broaden
them. Their physical gates remain pending.

1. Prepare the manual preflight/evidence workflow for power-off encoder
   observation and later one raised-wheel testing. Keep both Phase 4C targets
   and every existing
   BH1750, BMP280, MPU6050, HC-SR04, ground-sensor, full-hardware, and rover-
   control foundation target intact.
2. Centralize the documented motor/encoder mapping from the handoff. Do not
   invent geometry, wheel signs, encoder signs, speed limits, PID gains, fuse
   values, COM ports, or physical measurements.
3. Add a real STM32 peripheral backend for TIM8 PWM/direction; reuse the tested
   encoder helper/mapping without merging targets. Initialize all outputs
   disabled/zero and make motion impossible without an explicit validated enable.
4. Design the isolated target around one selected logical wheel at a time,
   bounded commands, explicit stop, command timeout, reset, and raw encoder
   telemetry. Do not start with four-wheel closed-loop motion.
5. Preserve nonblocking runtime behavior and bounded buffers. No dynamic memory.
6. Add host-testable pure helpers and tests for mapping, clamping, sign handling,
   stop behavior, timeout, count wrap/extension, timing, telemetry bounds, and
   isolation from other targets.
7. Add or update Keil ARM Compiler 6 project files using existing repository
   patterns. Do not commit Objects_*, Listings, .axf, .o, .d, .dep, .lnp, HTML
   build logs, or other generated files.
8. Update AGENTS.md/current guidance, TODO_HARDWARE.md, HARDWARE_LOCK.md only when
   evidence status genuinely changes. Update relevant docs and CHANGELOG.md for
   new software interfaces.
9. Add a Phase 4C verifier if the repository pattern supports it. Keep all prior
   phase verifiers passing.
10. Do not commit or push unless explicitly requested.

Development verification must include:

python tools\validate_hardware_lock.py
python -m pytest pc\tests -q --basetemp .verification\tmp\pytest-phase4c
.\tools\verify_phase.cmd phase3.2f -AllowDirty
.\tools\verify_phase.cmd phase4a -AllowDirty
.\tools\verify_phase.cmd phase4b -AllowDirty

If Keil ARM Compiler 6 is installed, compile the isolated target and report the
actual result. Do not claim physical operation from a successful build.

Stop before any manual hardware step and request these items incrementally:

- OpenRF1 wiring-bay photographs showing pin-1, dividers, fuse, and grounds;
- CN1-CN4 to FL/FR/RL/RR trace confirmation;
- mecanum roller top view;
- battery polarity and measured battery/VIN/5V/3.3V/buck voltages;
- BMS continuous/peak current, fuse, and main-wire gauge;
- loaded wheel diameter, wheelbase, and track width in millimetres;
- explicit authorization for serial access, flashing, and raised-wheel testing.

Your final response must lead with what was implemented, then tests, unresolved
hardware values, hardware actions not performed, next manual gate, and git
status. Do not call the rover drive-ready until physical evidence supports it.
```
