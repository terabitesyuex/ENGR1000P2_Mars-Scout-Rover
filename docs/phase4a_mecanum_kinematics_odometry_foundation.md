# Phase 4A Mecanum Kinematics and Odometry Foundation

## Status and scope

Phase 4A is a **SOFTWARE_VERIFIED software-only foundation** for standard X-layout mecanum kinematics, explicit encoder-count conversion, rover body-twist estimation, exact constant-twist SE(2) pose integration, deterministic simulation, and version-1 telemetry/recording compatibility.

It performs no hardware access. It does not implement motor control, PWM, encoder GPIO/timers/interrupts, MPU6050 fusion, calibration, PID control, closed-loop motion, obstacle avoidance, ESP32/WiFi, RPLIDAR integration, mapping, or SLAM. Phase 4 is not physically complete.

## Coordinates, units, and wheel order

- Rover body `+x`: forward.
- Rover body `+y`: left.
- Positive yaw and yaw rate: counterclockwise.
- World pose: `x_m`, `y_m`, `yaw_rad`.
- Linear velocity: metres per second.
- Wheel and body angular velocity: radians per second.
- Angles are radians internally; integrated yaw is normalized to `[-pi, pi)`.
- Telemetry timestamps use milliseconds; persistent recording timestamps use microseconds as required by their existing version-1 contracts.
- Wheel order is `front_left`, `front_right`, `rear_left`, `rear_right`.

Positive wheel rotation is a purely mathematical convention defined by the formulas below. It is independent of motor wiring, encoder polarity, motor polarity, or the rover's physically installed roller orientation. Raw-to-mathematical encoder direction multipliers must be supplied explicitly for all four wheels and may only be `+1` or `-1`. Physical multiplier values remain **UNVERIFIED**.

## Explicit required configuration

Every caller must provide:

- `wheel_radius_m`;
- `half_length_m`, measured mathematically from the rover centre to a wheel axis along `x`;
- `half_width_m`, measured mathematically from the rover centre to a wheel axis along `y`;
- `counts_per_wheel_revolution`;
- four raw-encoder direction multipliers.

The first four numeric values must be finite and strictly positive. No rover geometry, resolution, gear ratio, or encoder sign is defaulted. `counts_per_wheel_revolution` means wheel-side counts per one complete wheel revolution. A motor-shaft resolution is not accepted as a silent substitute, and no gear ratio is inferred.

Counter wrap handling is disabled unless `counter_width_bits` is explicitly supplied. With an explicit width, both counter samples must fit that unsigned width and the helper returns the minimum signed modular delta. The exactly half-range case follows the negative half-range convention and should be avoided by sampling frequently enough in later hardware work.

## Standard X-layout kinematics

Let:

```text
k = half_length_m + half_width_m
```

For body twist `(vx, vy, yaw_rate)` and wheel radius `r`, inverse kinematics are:

```text
front_left  = (vx - vy - k * yaw_rate) / r
front_right = (vx + vy + k * yaw_rate) / r
rear_left   = (vx + vy - k * yaw_rate) / r
rear_right  = (vx - vy + k * yaw_rate) / r
```

For mathematical wheel angular velocities `(front_left, front_right, rear_left, rear_right)`, forward kinematics are:

```text
vx = r / 4 * (front_left + front_right + rear_left + rear_right)
vy = r / 4 * (-front_left + front_right + rear_left - rear_right)
yaw_rate = r / (4 * k) * (-front_left + front_right - rear_left + rear_right)
```

These formulas define software signs only. A physical X-layout roller orientation has not been inspected or verified by this phase.

## Encoder conversion

A signed raw count delta `delta_count`, explicit direction multiplier `direction`, and wheel-side resolution `counts_per_wheel_revolution` produce:

```text
wheel_displacement_rad =
    2 * pi * delta_count * direction / counts_per_wheel_revolution

wheel_velocity_rad_s = wheel_displacement_rad / dt_s
```

`dt_s` must be finite and strictly positive. Raw deltas and sign-corrected deltas remain distinct in telemetry and recordings. This preserves the evidence needed to revise direction configuration after later physical validation.

## Pose integration

`integrate_constant_body_twist` applies the exact constant body-frame twist exponential over positive `dt_s`. With `theta = yaw_rate * dt_s`, it uses the standard `sin(theta) / theta` and `(1 - cos(theta)) / theta` terms, rotates the resulting body displacement by the initial world yaw, updates `x_m`, `y_m`, and `yaw_rad`, then normalizes yaw to `[-pi, pi)`.

A series expansion is used near zero `theta` to avoid cancellation. This is wheel-odometry integration, not sensor fusion. MPU6050 data is not read or used.

## Deterministic simulator and CLI

The simulator covers `stationary`, `forward`, `left_strafe`, `counterclockwise_rotation`, and `combined_curved_motion`. It converts a fixed synthetic scenario twist to ideal wheel rates, deterministically quantizes cumulative encoder counts, reconstructs wheel velocity and body twist, and integrates pose.

The following values are **synthetic test values, not rover measurements**:

```powershell
python -m rplidar_c1_tools.cli simulate-mecanum-odometry `
  --wheel-radius-m 0.05 `
  --half-length-m 0.18 `
  --half-width-m 0.16 `
  --counts-per-wheel-revolution 2048 `
  --front-left-direction 1 `
  --front-right-direction 1 `
  --rear-left-direction 1 `
  --rear-right-direction 1 `
  --scenario combined_curved_motion `
  --steps 5 `
  --interval-ms 100 `
  --output .verification/phase4a/mecanum_odometry.jsonl
```

Output is deterministic UTF-8 JSONL. Existing files are refused unless `--overwrite` is supplied. Invalid or missing geometry, resolution, direction, interval, or scenario arguments produce a visible error and nonzero exit status.

## Telemetry and recording compatibility

The existing `mars_scout_stm32_sensor_telemetry` version 1 parser accepts four additive message types without changing prior types or semantics:

- `wheel_encoder_delta`: raw and explicitly sign-corrected four-wheel deltas plus `interval_ms`, with `status: simulated` for the Phase 4A simulator;
- `wheel_angular_velocity`: four wheel rates in rad/s, with `status: software_derived`;
- `body_twist`: `vx_m_s`, `vy_m_s`, and `yaw_rate_rad_s`, with `status: software_derived`;
- `odometry_pose`: `x_m`, `y_m`, `yaw_rad`, and the `se2_constant_twist_exponential` method identifier, with `status: software_derived`.

The recording bridge writes corresponding additive record types inside `mars_scout_multisensor_recording` version 1. Existing Phase 2.x and Phase 3.x records, fixtures, parser behavior, replay behavior, and message meanings remain unchanged.

## UNVERIFIED physical facts and future boundary

Phase 4A does not establish any of the following:

- actual wheel radius, half length, or half width;
- counts per wheel revolution, motor-shaft counts, or gear ratio;
- encoder counter width, GPIO, timer, interrupt, sampling interval, or timestamp source;
- motor, encoder, or wheel direction signs;
- physical mecanum roller orientation;
- wheel slip, floor interaction, chassis rigidity, or odometry accuracy;
- motor/PWM behavior, closed-loop control, calibration, or MPU6050 fusion.

Later encoder/motor hardware work must measure or evidence these values, supply them explicitly, preserve raw counts, validate signs one wheel at a time under safe conditions, and record physical accuracy separately. Passing Phase 4A proves only the host-side software contracts and deterministic mathematics.
