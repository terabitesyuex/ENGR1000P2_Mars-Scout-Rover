# Phase 4B Closed-Loop Wheel-Speed Control and Motion Safety Foundation

## Status and scope

Phase 4B is a **SOFTWARE_VERIFIED software-only foundation** for validated body-motion commands, Phase 4A wheel-target generation, proportional desaturation, angular-acceleration limiting, four independent discrete PID controllers, command-watchdog handling, local permit-or-stop safety arbitration, and deterministic synthetic closed-loop simulation.

It performs no hardware access. It does not read encoders or sensors and does not access serial ports, USB, GPIO, I2C, timers, motors, motor-driver registers, PWM, Keil, FlyMcu, or flashing tools. Phase 4 is not physically complete.

The implementation does not provide real geometry, wheel size, encoder resolution, gear ratio, counter width, motor/encoder/wheel polarity, roller orientation, PID tuning, feedforward, deadband, minimum duty, voltage compensation, wheel-slip compensation, MPU6050 fusion, obstacle-navigation decisions, path planning, ESP32/WiFi, RPLIDAR integration, mapping, or SLAM.

## Inherited Phase 4A conventions

- Rover `+x` is forward and `+y` is left.
- Positive yaw is counterclockwise.
- Linear values use metres and metres per second.
- Internal angles and angular rates use radians and radians per second.
- Control intervals use seconds; telemetry timestamps use milliseconds.
- Wheel order is `front_left`, `front_right`, `rear_left`, `rear_right`.
- Wheel signs use the Phase 4A mathematical convention. Physical direction multipliers remain explicit and UNVERIFIED.

`MecanumGeometry`, `BodyTwist2D`, `WheelAngularVelocities`, inverse kinematics, forward kinematics, and SE(2) pose integration are reused from Phase 4A. Phase 4B does not duplicate or redefine those conventions.

## Control pipeline

Every update applies independently testable stages in this order:

```text
validated BodyMotionCommand
  -> Phase 4A inverse mecanum kinematics
  -> proportional desaturation of all four wheel targets
  -> independent wheel angular-acceleration limits
  -> watchdog and local safety arbitration
  -> four independent wheel-speed PID updates
  -> dimensionless normalized control efforts
```

If safety suppresses motion, all applied wheel targets are replaced with zero before output generation, all normalized efforts are zero, and all PID state is reset. The next permitted update therefore restarts deterministically from zero shaped targets and fresh PID state.

## Body-command validation

`BodyMotionCommand` requires finite `vx_m_s`, `vy_m_s`, and `yaw_rate_rad_s`, plus a non-negative `command_timestamp_ms`. Optional command IDs must be non-empty strings. The source is explicit, and `motion_requested: false` yields a zero twist.

No physical speed maximum is embedded. `MotionCommandLimits` is optional and is applied only when a caller supplies explicit positive limits for forward, lateral, and yaw-rate magnitudes. Validation occurs before Phase 4A kinematics.

## Wheel proportional desaturation

For requested wheel rates and an explicit positive `max_wheel_speed_rad_s`:

```text
peak = max(abs(front_left), abs(front_right), abs(rear_left), abs(rear_right))

scale = 1                                      when peak <= maximum
scale = max_wheel_speed_rad_s / peak           when peak > maximum
output_wheel = requested_wheel * scale
```

This is proportional desaturation: all four wheel values use one scale, so signs and ratios are preserved. Wheels are not clamped independently. The result exposes `desaturated` and `scale_factor`.

## Wheel angular-acceleration limiting

Each wheel has an explicit positive limit in rad/s². A deliberately shared limit can be expanded to four explicit fields. For positive `dt_s`:

```text
maximum_change = max_acceleration_rad_s2 * dt_s
new_setpoint = clamp(requested, previous - maximum_change, previous + maximum_change)
```

The four rate-limited flags are exposed independently. Reversal is handled by the same rule. No jerk behavior or motor dynamics is implied.

## Discrete wheel-speed PID

For one wheel and positive `dt_s`:

```text
error = target_rad_s - measured_rad_s
P = kp * error
integral_candidate = clamp(previous_integral + error * dt_s,
                           integral_min, integral_max)
measurement_derivative = 0                                      on first sample
measurement_derivative = (measurement - previous_measurement) / dt_s otherwise
D = -kd * measurement_derivative
raw_output = P + ki * integral + D
normalized_effort = clamp(raw_output, output_min, output_max)
```

The controller uses **derivative on measurement**, reducing setpoint kick. The first derivative sample is deterministically zero. All gains and output/integral limits are explicit and finite; no rover gains are defaulted.

The anti-windup rule is **conditional integration** combined with explicit integral-state clamping. If the integral candidate would saturate output high while error is positive, or saturate output low while error is negative, the prior clamped integral is retained. Integration is allowed when the error would unwind saturation. Tests cover sustained positive and negative unreachable demand, recovery, disable, and reset.

Disable returns zero effort and a fresh `PIDState`. Four-wheel coordination holds a separate `PIDState` for each wheel, supports distinct configurations, and never shares integral state.

The output is a **dimensionless normalized control effort** with mathematical sign. The commonly demonstrated `-1.0` to `+1.0` interval is an explicit synthetic fixture, not a hard-coded requirement. Effort is not PWM duty, verified PWM polarity, motor voltage, or a battery-voltage command. Hardware mapping, deadband, minimum duty, voltage compensation, and feedforward belong to later physical work.

## Command watchdog

The watchdog uses supplied timestamps only; it never reads an operating-system clock:

```text
command_age_ms = current_timestamp_ms - command_timestamp_ms
stale = command_age_ms >= timeout_ms
```

A command is stale exactly when its age is equal to or greater than the explicit positive timeout. Negative timestamps and current time preceding command time are rejected. Timestamp wrap is not guessed or supported without a future explicit-width contract.

## Safety precedence

`MotionSafetyPolicy` explicitly selects which unavailable or hazardous inputs are fatal. Its default is conservative: watchdog, communication, ground-edge, ultrasonic, critical-sensor, and external-stop checks are enabled. A caller may explicitly make a noncritical unavailable input nonfatal. Emergency stop and controller fault cannot be disabled by policy.

Stop reasons are evaluated in this precedence:

1. `emergency_stop`;
2. `controller_fault`;
3. `disabled`;
4. `external_stop` when enabled by policy;
5. `stale_command` when the watchdog is enabled;
6. `communication_fault` when enabled by policy;
7. `ground_edge` when enabled by policy;
8. `ultrasonic_obstacle` when enabled by policy;
9. `critical_sensor_invalid` when enabled by policy;
10. `none`.

The decision exposes motion permission, forced-stop status, reason, command age/staleness, non-latched status, and target replacement. Phase 4B only permits or suppresses requested motion; it does not choose a turn direction or implement obstacle avoidance.

## Deterministic synthetic plant

The simulator uses a **synthetic first-order wheel plant**, independently parameterized for each wheel:

```text
d(omega) / dt = (gain * normalized_effort - omega) / time_constant
alpha = 1 - exp(-dt / time_constant)
omega_next = omega + alpha * (gain * effort - omega)
```

Every gain and time constant is explicit and labelled SYNTHETIC. They are not rover measurements. The exact discrete update is deterministic for any positive interval. The simulator combines Phase 4A inverse/forward kinematics, Phase 4B shaping/safety/PID, the synthetic plant, and optional Phase 4A SE(2) pose integration.

Available scenarios are `stationary`, `forward`, `left_strafe`, `counterclockwise_rotation`, `combined_curved_motion`, `command_desaturation`, `acceleration_limited_transition`, `stale_command_watchdog_stop`, `emergency_stop`, `ground_edge_forced_stop`, `ultrasonic_forced_stop`, and `slow_front_left_wheel`. The last scenario requires an explicit distinct synthetic front-left time constant.

Each sample distinguishes the requested body command, requested wheel speeds, desaturated wheel speeds, acceleration-limited speeds, safety-applied speeds, synthetic measurements, normalized efforts, estimated body twist, synthetic pose, and safety state.

## CLI

The following values are synthetic test values, not rover measurements, safety limits, or physical PID tuning:

```powershell
python -m rplidar_c1_tools.cli simulate-motion-control `
  --wheel-radius-m 0.05 `
  --half-length-m 0.18 `
  --half-width-m 0.16 `
  --max-wheel-speed-rad-s 20 `
  --wheel-acceleration-rad-s2 10 `
  --pid-kp 0.05 --pid-ki 0.02 --pid-kd 0 `
  --pid-output-min -1 --pid-output-max 1 `
  --pid-integral-min -2 --pid-integral-max 2 `
  --plant-gain-rad-s-per-effort 20 `
  --plant-time-constant-s 0.2 `
  --command-timeout-ms 250 `
  --scenario combined_curved_motion `
  --steps 20 --interval-ms 100 `
  --output .verification/phase4b/motion_control.jsonl
```

The command writes deterministic UTF-8 JSONL, refuses an existing output unless `--overwrite` is supplied, prints a success path, and returns nonzero with a visible error for invalid input. It never opens serial ports, enumerates COM ports, accesses USB, or accesses hardware.

## Telemetry and recording compatibility

`mars_scout_stm32_sensor_telemetry` remains version 1. Phase 4B adds six message types with `status: software_derived` and `origin: synthetic_phase4b_motion_control`:

- `body_motion_command`;
- `wheel_speed_setpoint`;
- `wheel_speed_measurement`;
- `wheel_control_effort`;
- `motion_safety_state`;
- `motion_control_snapshot`.

The existing `mars_scout_multisensor_recording` also remains version 1. The recording bridge writes matching additive record types and preserves the validated control payload. Existing message and record types, fields, parser semantics, inspection, replay, and older recordings remain valid; older files do not require Phase 4B fields.

## Boundary to future phases and UNVERIFIED physical facts

- Phase 4A is the software-only mecanum kinematics, explicit encoder conversion, and odometry foundation.
- Phase 4B is the software-only closed-loop wheel-speed, command shaping, watchdog, safety arbitration, and synthetic plant foundation.
- Future Phase 4C is real motor and encoder bring-up: electrical checks, physical direction discovery, timer/interrupt/PWM validation, and measured wheel response.
- Later Phase 4 work covers physical PID tuning, MPU6050-assisted pose estimation, real closed-loop motion, and physical odometry validation.
- Phase 5 remains STM32-ESP32-PC communication and WiFi integration and has not begun.

## UNVERIFIED physical facts

Passing Phase 4B does not prove that motors rotate, encoder counts are readable, wheel direction is correct, PWM polarity is correct, synthetic PID gains are usable, mecanum rollers are mounted in the assumed layout, the rover follows a trajectory, or stopping distance is safe. Actual wheel dimensions, encoder resolution, gear ratio, counter width, voltage, battery behavior, motor response, controller timing, traction, wheel slip, closed-loop performance, trajectory accuracy, and physical odometry accuracy remain **UNVERIFIED**.
