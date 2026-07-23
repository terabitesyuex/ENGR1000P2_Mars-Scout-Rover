# Near-Term Vehicle Bring-Up Handoff

Date: 2026-07-23

This document hands the Mars Scout Rover from wiring preparation to the next
software-development agent. It is intentionally conservative: the user reports
that the complete vehicle has been assembled according to the repository wiring
plan, but no new photographs, continuity records, voltage measurements, serial
captures, motor motion, or integrated-system evidence accompanied that report.
Physical installation is therefore still `UNVERIFIED`.

## Repository Snapshot

- Repository: the current `<repository-root>` workspace
- Expected working branch: `main`
- Snapshot HEAD when this handoff was prepared: `0442dc3`
- `main` and `origin/main` were synchronized and the working tree was clean
  before this handoff edit.
- Do not create another branch unless the user explicitly asks for one.
- Do not commit or push unless the user explicitly asks.
- The latest `phase3.2e-hcsr04-bringup` tip `17c6cd5` contains only generated
  Keil `Objects_HCSR04_Bringup` files. The HC-SR04 source is already represented
  in `main`; do not merge those generated artifacts into `main`.

## Current Physical Status

The user reports that the complete rover has been assembled according to:

- [`openrf1_rover_wiring_plan.md`](openrf1_rover_wiring_plan.md)
- [`openrf1_rover_wiring_plan_zh.md`](openrf1_rover_wiring_plan_zh.md)

This report is useful scheduling information, not evidence that the following
have passed:

- connector pin-1 orientation and point-to-point continuity;
- battery and charger barrel polarity;
- battery, OpenRF1 VIN, 5 V, 3.3 V, and independent-buck voltages;
- BMS current limits, fuse selection, wire gauge, and transient margin;
- four encoder pull-ups and four 10 kOhm / 15 kOhm divider networks;
- motor and encoder wheel identities or signs;
- shared I2C, three-HC-SR04 operation, USART2, USART3, or full-rover operation.

Do not describe the vehicle as electrically accepted, powered, commissioned, or
drive-ready until controlled evidence exists.

## Source-Of-Truth Order

Use these files in order when facts appear to conflict:

1. `AGENTS.md` for scope, safety, evidence, and workflow rules.
2. `HARDWARE_LOCK.md` for confirmed facts and evidence boundaries.
3. `docs/openrf1_rover_wiring_plan.md` for engineering wiring decisions.
4. `docs/openrf1_rover_wiring_plan_zh.md` for the field assembly sequence.
5. `TODO_HARDWARE.md` for unresolved measurements and signs.
6. Vendor schematic/example facts already summarized in those files.
7. Historical phase documents only for the isolated phase they describe.

Never replace an `UNVERIFIED` value with a common convention or a plausible
number.

## Hardware Baseline

### Controller And Power

- OpenRF1 controller with STM32F103RCT6.
- Seller-documented Li-ion pack: 11.1 V nominal, 7800 mAh, 5C advertised,
  12.6 V fully charged, DC 5.5 x 2.5 mm male connector.
- Direct battery-to-OpenRF1 VIN through the main fuse and latching disconnect is
  `USER_APPROVED_DESIGN`; physical polarity/current/transient acceptance remains
  `UNVERIFIED`.
- RPLIDAR C1 and ESP32 use an independent regulated 5.0 V branch. H5 pin 1 and
  H6 pin 1 remain disconnected. ESP32 external 5 V must be removable before USB.

### Motor And Encoder Mapping

| Logical wheel | Connector | PWM | Direction | Encoder timer/pins |
| --- | --- | --- | --- | --- |
| front_left | CN2 | PC7 / TIM8_CH2 | PA11 | TIM3, PA6/PA7 |
| front_right | CN4 | PC9 / TIM8_CH4 | PC10 | TIM4, PB6/PB7 |
| rear_left | CN1 | PC6 / TIM8_CH1 | PA8 | TIM5, PA0/PA1 |
| rear_right | CN3 | PC8 / TIM8_CH3 | PA12 | TIM2 full remap, PA15/PB3 |

Motor/encoder connector rule:

| Connector pin | Harness function |
| ---: | --- |
| 1 | white Motor- to AT8236 OUT2 |
| 2 | no wire; board 5 V cavity remains isolated |
| 3 | yellow encoder A plus independent 10 kOhm pull-up to 3.3 V |
| 4 | green encoder B plus independent 10 kOhm pull-up to 3.3 V |
| 5 | black encoder GND |
| 6 | red Motor+ to AT8236 OUT1 |
| external CN5 pin 3 | blue encoder VCC at 3.3 V |

Nominal motor/encoder data are 6-12 V, 0.36 A no-load, 3.2 A stall, 330 rpm
no-load output, 30:1 ratio, 11 A cycles and 11 B cycles per motor revolution,
and nominal 1320 x4 counts per output revolution. The count and all signs still
require controlled validation.

### Sensors And Communications

- I2C: PB1/SCL and PC3/SDA. BH1750 `0x23`, MPU6050 `0x68`, BMP280 `0x76`.
- HC-SR04 1: PA5 TRIG / PA4 ECHO through its own divider.
- HC-SR04 2: PB9 TRIG / PB8 ECHO through its own divider.
- HC-SR04 3: PD2 TRIG / PC11 ECHO through its own divider.
- TCRT5000: PC4/X1 and PC5/X2, powered from 3.3 V.
- Hall: PB0/X3 after its own divider, Hall module powered from 5 V.
- C1: H5 USART2, PA2/TX2 to C1 RX and PA3/RX2 from C1 TX, 460800 8N1.
- ESP32-C3 SuperMini: H6 USART3; STM32 PB10/TX3 to GPIO20/RX and STM32
  PB11/RX3 from GPIO21/TX. Proposed baud 921600 remains physically unverified.

## Software Reality

### What Exists

- Isolated BH1750, BMP280, MPU6050, HC-SR04, and ground-sensor bring-up targets.
- A Phase 3.2B full-hardware software foundation with scheduler, pure sensor
  helpers, telemetry framing, UART ring buffers, and STM32-to-ESP32 frame codec.
- Motor and encoder HAL interfaces under `firmware/openrf1/app/drivers/`.
- Fixed-point embedded mecanum inverse kinematics.
- PC-side Phase 4A mecanum/encoder/odometry algorithms and deterministic tests.
- PC-side Phase 4B command shaping, acceleration limits, four-wheel PID,
  watchdog, safety arbitration, telemetry, and deterministic tests.
- PC recording, replay, visualization, and physical C1 evidence tools.

### What Does Not Yet Exist

- A real STM32 motor backend that configures TIM8 PWM and direction GPIOs.
- A real STM32 encoder backend for TIM2/TIM3/TIM4/TIM5.
- Embedded four-wheel PID/safety integration. Phase 4B is not yet an operational
  STM32 controller.
- A drive-ready firmware image. `OpenRF1_RoverControl_Foundation` uses inert
  motor callbacks and returns encoder count zero; it must not be flashed as
  operational firmware.
- Complete full-hardware acquisition. The Phase 3.2B target still contains no-op
  MPU6050/BMP280 tasks and placeholder digital inputs.
- Real GPIO/timer support for HC-SR04 2 and 3.
- ESP32-C3 firmware, WiFi transport, provisioning, reconnect behavior, or
  command-timeout implementation.
- Integrated C1 command/scan forwarding through STM32-ESP32-PC.
- Physical odometry, calibrated PID, autonomous stop/turn behavior, or final
  full-rover acceptance.

## Immediate Development Phase: Phase 4C

The next agent is authorized to begin **software-only Phase 4C preparation**.
This does not authorize hardware access, opening a serial port, flashing,
energizing motors, or moving the vehicle.

### Phase 4C-A: Isolated Motor/Encoder Software Target

Implement an isolated OpenRF1 motor/encoder bring-up target that:

- uses the documented mapping above from one centralized configuration;
- initializes all motor outputs into an explicit disabled/zero-output state;
- supports selecting exactly one logical wheel for a bounded test command;
- configures TIM8 PWM without starting vehicle motion during initialization;
- configures TIM2/3/4/5 encoder interfaces, including required remaps;
- exposes raw signed counts, deltas, timestamps, and bounded telemetry;
- retains unknown motor and encoder signs as explicit runtime/config values;
- refuses motion when geometry, sign, enable, or safety state is invalid;
- includes command timeout, explicit stop, and controller-reset behavior;
- remains separate from every existing sensor bring-up target.

Do not begin with four-wheel closed-loop control. First make one-wheel and
encoder behavior observable and independently stoppable.

### Phase 4C-B: Host Tests And Build Verification

Add tests for:

- logical-wheel-to-connector/PWM/direction/encoder mapping;
- PWM command clamping, zero command, sign application, and stop behavior;
- signed encoder extension/wrap handling and sample timing;
- command timeout and invalid-configuration stop;
- telemetry field bounds and exact buffer-fit behavior;
- no hardware access by automated tests;
- isolation from all existing bring-up targets.

Add a dedicated Keil ARM Compiler 6 target. Do not commit `Objects_*`, `Listings`,
`.axf`, `.o`, `.d`, `.dep`, `.lnp`, build-log HTML, or other generated output.

### Phase 4C-C: Manual Physical Gates

Stop and request explicit user authorization before any of these actions:

- opening the OpenRF1 CH340 COM port;
- flashing the isolated target;
- energizing OpenRF1 from the vehicle battery;
- issuing a nonzero motor command;
- rotating a wheel under software control.

Before such authorization is actionable, request the information in the next
section and require wheels to be raised or removed.

## Information Still Needed From The User

| Priority | Required information | Exact form |
| ---: | --- | --- |
| 1 | Assembly photos | top, front, underside, and OpenRF1 wiring close-up; mark rover front |
| 2 | Connector-to-wheel trace | `CN1=...`, `CN2=...`, `CN3=...`, `CN4=...` using FL/FR/RL/RR |
| 3 | Roller layout | top photo showing all four mecanum rollers |
| 4 | Electrical preflight | battery centre/sleeve polarity and measured battery, VIN, 5 V, 3.3 V, buck voltages in volts |
| 5 | Main protection | BMS continuous/peak current, installed fuse, and main-wire AWG/cross-section |
| 6 | Geometry | loaded wheel diameter, axle-centre wheelbase, wheel-centre track width in millimetres |
| 7 | Mounting poses | C1, MPU6050, three ultrasonic, two TCRT5000, and Hall positions/orientations |
| 8 | Motion requirements | maximum linear speed, yaw rate, acceleration, and stopping distance |
| 9 | ESP32 environment | PlatformIO/Arduino/ESP-IDF preference; USB connector type |
| 10 | PC control requirement | keyboard, gamepad, or browser; PC operating system |

The agent should ask for these incrementally, beginning with photographs and
power-off trace information. Do not request a stall-current test without a
separately reviewed, current-limited procedure.

## Parameters That Must Be Measured Or Tuned

Never insert synthetic Phase 4A/4B fixture values into rover firmware.

### Required Before Kinematics

- loaded wheel radius in millimetres;
- half wheelbase and half track width in millimetres;
- confirmed X roller layout;
- measured counts per wheel revolution;
- four motor command signs and four encoder signs.

### Required Before Closed-Loop Motion

- control period and encoder-speed filtering;
- per-wheel PWM start/deadband and maximum safe duty;
- maximum measured wheel speed;
- acceleration/deceleration limits;
- command watchdog timeout;
- explicit brake/coast/emergency-stop behavior;
- per-wheel `Kp`, `Ki`, and `Kd`, beginning with bounded low-duty tests and no
  assumed production gain values.

### Required Before Integrated Autonomy

- TCRT active polarity, installed height, surface/drop threshold, and debounce;
- Hall polarity, magnetic working distance, and debounce;
- HC-SR04 offsets, timeout, quiet time, and cross-talk schedule;
- MPU6050 axes, gyro bias, acceleration calibration, and mounting transform;
- C1 mounting translation/yaw and scan-frame transform;
- stable STM32-ESP32 baud rate, reconnect behavior, and end-to-end watchdog.

## Recommended Delivery Order

1. Software-only isolated motor/encoder target and host tests.
2. User-reviewed preflight evidence template and one-wheel test card.
3. Manual encoder-only observation with power-off wheel rotation.
4. One raised wheel at minimum bounded duty.
5. Four raised wheels, still open-loop and individually selectable.
6. One-wheel speed loop, then four independent loops.
7. Low-speed forward/reverse, rotate, and strafe on the floor.
8. Physical odometry and MPU6050 integration.
9. Full sensor scheduler and local safety inputs.
10. ESP32/WiFi/PC command and telemetry path.
11. Integrated C1 and obstacle stop/turn behavior.

Each step requires its own evidence and regression coverage. A later step must
not be used to hide a failure in an earlier one.

## Acceptance Definition For The Next Software Deliverable

The next agent's first deliverable is complete only when:

- the isolated target builds with Keil ARM Compiler 6;
- no existing bring-up target is modified into a multi-purpose target;
- mapping and safety behavior have deterministic host tests;
- generated build outputs are ignored and uncommitted;
- all current phase verifiers still pass;
- documentation and `CHANGELOG.md` describe the new interface;
- no hardware result is claimed;
- the final report clearly separates software verification from manual action.

## Verification Commands

Run at minimum:

```powershell
python tools\validate_hardware_lock.py
python -m pytest pc\tests -q --basetemp .verification\tmp\pytest-phase4c
.\tools\verify_phase.cmd phase3.2f -AllowDirty
.\tools\verify_phase.cmd phase4a -AllowDirty
.\tools\verify_phase.cmd phase4b -AllowDirty
```

If a new `phase4c` verifier is added, run it with `-AllowDirty` during
development and normally after an explicitly requested commit/push.

## Handoff Reporting Format

The next agent should report:

1. files changed and why;
2. exact hardware facts consumed and their evidence status;
3. unknown values deliberately left unresolved;
4. tests and verifiers actually run with results;
5. hardware actions not performed;
6. next manual gate and the exact evidence needed;
7. git branch, commit status, and working-tree status.
