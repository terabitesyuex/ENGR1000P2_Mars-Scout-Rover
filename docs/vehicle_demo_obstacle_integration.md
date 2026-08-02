# Vehicle Demo Obstacle Integration

Status: SOFTWARE_PREPARED / PHYSICAL_CONFIRMATION_REQUIRED

This accelerated demo target integrates the useful parts of the hardware
team's supplied three-ultrasonic obstacle-avoidance source without importing
its generated Keil files, machine-local paths, or stale build metadata.

## Supplied Source Audit

Source archive: `AutoObstacleAvoidance_3US_STABLE_v1.zip`

- Archive SHA-256: `2517591E28A14592A9CB46B4C2760F0276EAF5FB764E40C2F1CDE8232C8DC4B8`.
- Embedded HEX SHA-256 calculated directly from the archive:
  `84F6B4A0033462692C0E0C396DD9E0B9209887A98920C1A22FD403B4B2C90E5B`.
- The calculated HEX hash matches the supplied README but conflicts with
  `ARTIFACT_SHA256.txt`, which records
  `1543028D47F0F44D34B3154F8EE738036D8FD96C5D0CE5921FE59A0A1BEC32E8`.
- The supplied source reports stable physical obstacle avoidance. This is a
  USER_REPORTED result, not repository-validated physical evidence.
- Generated objects, HEX, logs, absolute paths, and local user information from
  the archive are not imported.

## Current Demo Pin Mapping

The user confirmed this mapping on 2026-08-02. The supplied screenshot is
1508 x 502 pixels and has SHA-256
`E018B695861391BFB3ED7EF4EA6F5560A13D6BBD409FBBF0FABCE86E6E16B3F0`.

The supplied hardware-team source uses:

| Position | TRIG | ECHO |
| --- | --- | --- |
| Left | PB9 | PB8 |
| Centre | PB5 | PB4 |
| Right | PD2 | PC11 |

The earlier assembly proposal assigned the first sensor to CN6 PA5/PA4, the
second to PB9/PB8, and the third to PD2/PC11. The user's current confirmation
supersedes that proposal for the vehicle-demo target, which now identifies its
profile as `hardware_group_3us_user_confirmed`. Historical isolated CN6 bring-up
facts remain unchanged.

The user also reports that all three current ECHO paths are directly connected
without resistor dividers and that obstacle avoidance works in practice. Record
this as USER_REPORTED_OPERATIONAL_DIRECT_ECHO. It demonstrates functional
operation, not measured voltage compatibility or long-term electrical safety.
The actual ECHO-high voltage at PB8, PB4, and PC11 remains UNVERIFIED.

## Software Safety Changes

- Startup remains stopped; motion requires `ARM` followed by `START`, and
  `START` is rejected while any current sample reports a hazard.
- `HEARTBEAT` must arrive more frequently than the 2000 ms command watchdog.
- `STOP`, `DISARM`, an unknown command, UART fault, stale measurement, timeout,
  or invalid pulse forces all motor outputs to zero and revokes arming.
- Timeout is invalid data with JSON `null` distance, never a valid 0 mm sample.
- Three HC-SR04 channels run as a nonblocking state machine with one active
  transmitter and a 35000 us inter-channel gap.
- TIM6 provides a 1 MHz counter extended in its overflow interrupt; the supplied
  DWT division timebase and its short physical wrap period are not used.
- USART1 RX and TX use interrupt-driven rings, so telemetry does not spin-wait.
- Motor direction logic and CN1/CN2 101%, CN3/CN4 75% trims are retained from
  the supplied source and remain USER_REPORTED physical calibration.
- The demo also samples the vendor-documented Hall path `X3 / PB0` every 5 ms
  and emits numeric raw and four-sample-debounced values in status JSONL. Hall
  is telemetry-only in this target: it does not arm, stop, steer, or otherwise
  alter the obstacle controller. Hall physical behavior and polarity remain
  UNVERIFIED.
- PC-side `vehicle_demo_hall` adaptation validates VehicleDemo JSONL, ignores
  identity/motor-diagnostic records, and writes replay-compatible
  `hall_landmark` records with both raw and debounced numeric states. It never
  converts either level into a magnetic-landmark claim.
- A read-only connector encoder path configures CN1/TIM5, CN2/TIM3,
  CN3/TIM2-full-remap, and CN4/TIM4 in TI12 mode. It samples every 50 ms and
  emits unsigned 16-bit raw counts, modular deltas, and bounded cumulative
  counts. It neither reads nor applies encoder direction signs and does not
  alter motor or obstacle control.
- `inspect-vehicle-demo-encoder` validates saved JSONL ordering, intervals,
  wrap arithmetic, and cumulative consistency. It intentionally retains CN1-CN4
  identities until connector-to-wheel tracing is physically verified.

### Read-Only Encoder Boundary

The encoder GPIOs use floating-input configuration because the wiring design
requires eight external 10 kOhm pull-ups to the independent 3.3 V encoder
supply. Software does not claim those pull-ups or encoder power are installed.
TIM2 full remap disables JTAG while retaining SWD so PA15/PB3 are available.
No encoder timer interrupt is enabled; the main loop reads each 16-bit counter
atomically at 50 ms. Missed sample slots are dropped instead of backfilled.

The modular delta range is `[-32768, 32767]`; more than half a counter revolution
between samples is ambiguous and therefore outside the software contract. The
seller nominal motor/encoder figures suggest substantially less than this at
50 ms, but real maximum count rate remains unverified. Cumulative overflow
invalidates the sample instead of wrapping silently. Encoder telemetry failure
is reported but does not become a motion command or safety input.

### Hall Mapping Landmarks

The supplied course places three centreline magnets at `(600, 400)`,
`(1800, 400)`, and `(2200, 400)` millimetres. VehicleDemo samples PB0 every
5 ms, requires four stable samples, and establishes its polarity-independent
baseline from 20 stable startup samples. A stable departure from that baseline
creates one latched `vehicle_demo_hall_event`; returning to baseline rearms the
next event. The event carries the first stable-candidate timestamp rather than
the later 250 ms status timestamp, so a short crossing cannot disappear between
status records.

Hall remains outside `obstacle_control`. The PC adapter associates sequential
events with the three course coordinates and preserves them for later pose-drift
checking. Because the corrected mounting measurements place the Hall sensing
point at planar `base_link x=0 mm, y=0 mm`, the adapter also records each known
magnet coordinate as a `known_base_link_x_mm/y_mm` position observation and
marks the zero planar offset as applied. It does not create a yaw observation.
Missing a landmark is evidence of possible lateral path error, not
proof: pole orientation, effective magnetic range, and the Hall-to-rover
physical response remain unverified. A single centre Hall sensor also cannot
determine whether a miss was to the left or right.

Offline conversion command:

```powershell
python -m rplidar_c1_tools record-vehicle-demo-hall --input vehicle.jsonl --output recording.jsonl
python -m rplidar_c1_tools inspect-vehicle-demo-hall --input vehicle.jsonl --output hall_report.txt
python -m rplidar_c1_tools inspect-recording recording.jsonl
```

The command accepts files only. It does not open a serial port or access the
rover.

The Hall report counts numeric 0/1 samples, raw/debounced mismatches, and
observed transition sequence/timestamps. It also reports how many of the three
known course checkpoints have been observed, whether the expected sequence is
complete, the next expected index, and any extra events after checkpoint 3. It
intentionally does not label either electrical level as magnet present or
absent.

The Hall scheduler deliberately drops missed 5 ms sample slots instead of
catching up with repeated immediate GPIO reads. A delayed main loop therefore
cannot satisfy the four-sample debounce or 20-sample startup baseline faster
than real elapsed sampling opportunities. Because polarity is inferred from the
startup baseline, the rover should start clear of a course magnet; software
cannot distinguish "started over a magnet" from an ordinary baseline without
external polarity knowledge.

## Hall Mounting Evidence Boundary

The user supplied an underside photograph on 2026-08-02 and explicitly stated
that the Hall module is installed under the rover and the top of the photograph
is the rover-front direction. Corrected sensing-point clearances are 185 mm to
the front body boundary, 135 mm to the rear boundary, 75 mm to each side, and
95 mm to each axle centre. Together with the 190 mm wheelbase, these establish
the planar Hall-to-`base_link` offset as x=0 mm, y=0 mm. The referenced 320 x
150 mm body envelope has a different centre, from which Hall is x=-25 mm,
y=0 mm (`+x` forward, `+y` left). The supplied sensing-point height is 65 mm
above the floor, deriving `base_link z=+25.5 mm` from the supplied 39.5 mm
loaded wheel radius. Sensing face, connector wiring, active polarity,
triggering magnetic pole, working distance, and real magnetic response remain
UNVERIFIED.

## Build

Keil project:

`firmware/openrf1/keil/OpenRF1_VehicleDemo.uvprojx`

Expected generated output:

`firmware/openrf1/keil/Objects_VehicleDemo/OpenRF1_VehicleDemo.hex`

The project uses repository-relative paths and a unique ignored output folder.
On this workstation the uVision command-line attempt failed because uVision
selected a missing `ArmCC` executable despite the project requesting ARM
Compiler 6. Direct ARM Compiler 6 strict syntax checks pass with no diagnostics.
This is not a successful linked Keil build and no HEX is accepted from it.

## Remaining Manual Gate

Pin mapping is now user-confirmed. Before declaring the direct ECHO interface
electrically accepted, measure the ECHO-high voltage at PB8, PB4, and PC11 and
compare it with authoritative limits for each exact board input path. Initial
motion testing still requires wheels raised, a clear area, an accessible power
disconnect, and continuous heartbeat input. No hardware, serial port, flashing
tool, or motor was accessed during this software work.
