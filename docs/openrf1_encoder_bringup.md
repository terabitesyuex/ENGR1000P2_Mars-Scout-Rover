# OpenRF1 Isolated Encoder Bring-Up

## Scope

`OpenRF1_Encoder_Bringup` is a read-only, software-prepared STM32F103RCT6
target for observing the four OpenRF1 encoder connector counters. It does not
initialize TIM8, motor direction GPIO, ultrasonic sensors, Hall input, or a
command receiver. It cannot intentionally command wheel motion.

The target is not physical evidence. Connector-to-wheel assignment, phase
order, count direction, counts per wheel revolution, signal voltage, pull-up
installation, and operation on the assembled rover remain `UNVERIFIED`.

## Software Mapping

| Neutral ID | Timer | Input pins | Counter |
| --- | --- | --- | --- |
| `CN1` | TIM5 | PA0 / PA1 | unsigned 16-bit |
| `CN2` | TIM3 | PA6 / PA7 | unsigned 16-bit |
| `CN3` | TIM2 full remap | PA15 / PB3 | unsigned 16-bit |
| `CN4` | TIM4 | PB6 / PB7 | unsigned 16-bit |

PA15/PB3 require JTAG to be disabled; SWD remains enabled. All eight encoder
inputs are configured floating because the board/encoder interface is expected
to supply suitable 3.3 V pull-ups. That electrical expectation must be measured
before connection or power-up.

USART1 is transmit-only on PA9 at 115200 8N1. A 100 ms schedule emits
`vehicle_demo_encoder` JSONL records. Raw, modular signed delta, and bounded
signed cumulative counts are provided for CN1–CN4. No physical wheel name or
direction sign is applied.

## Build

Open this project in Keil MDK ARM Compiler 6:

`firmware/openrf1/keil/OpenRF1_Encoder_Bringup.uvprojx`

Building creates ignored output under
`firmware/openrf1/keil/Objects_Encoder_Bringup/`.

## Manual Gate

Do not flash or open a serial port merely because the target builds. Before a
manual session:

1. keep the rover battery disconnected and motors unable to receive power;
2. verify common ground and measure encoder A/B high levels at or below 3.3 V;
3. verify external pull-ups are present and suitable;
4. identify the user-selected OpenRF1 CH340 COM port;
5. obtain explicit authorization to flash and open that port;
6. raise the wheels or otherwise prevent unintended vehicle motion.

After authorization, rotate exactly one wheel by hand while motors remain
unpowered. Record CN1–CN4 before, during, and after the rotation. Repeat in the
opposite direction, then trace all four connector-to-wheel assignments. A
successful changing counter proves only observation for that setup; direction
sign and counts per revolution require separate controlled measurements.

Use the existing strict PC command on the captured JSONL:

`python -m rplidar_c1_tools.cli inspect-vehicle-demo-encoder <capture.jsonl>`

Any sequence gap, invalid interval, impossible wrap delta, cumulative mismatch,
mapping claim, or direction-verification claim must fail inspection.

