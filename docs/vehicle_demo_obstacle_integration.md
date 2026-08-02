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
