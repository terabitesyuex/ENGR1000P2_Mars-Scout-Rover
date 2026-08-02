# OpenRF1 Fail-Disabled One-Wheel Motor Bring-Up

## Scope

`OpenRF1_Motor_Bringup` is a software-prepared Phase 4C target for a later
raised-wheel, one-connector-at-a-time motor and encoder test. It is not
authorized for present hardware use and is not four-wheel motion firmware.

At startup the target has no selected connector, motor sign, encoder sign,
maximum test duty, or watchdog duration. TIM8 runs with all CCR values zero,
all CCER channel enables off, and BDTR/MOE off. All direction outputs are low.
No nonzero output is possible until a complete runtime configuration, explicit
ARM, and valid RUN command have been received.

## Fixed Software Mapping

| Neutral connector | PWM | Direction | Encoder |
| --- | --- | --- | --- |
| CN1 | PC6 / TIM8_CH1 | PA8 | PA0/PA1 / TIM5 |
| CN2 | PC7 / TIM8_CH2 | PA11 | PA6/PA7 / TIM3 |
| CN3 | PC8 / TIM8_CH3 | PA12 | PA15/PB3 / TIM2 full remap |
| CN4 | PC9 / TIM8_CH4 | PC10 | PB6/PB7 / TIM4 |

This vendor-documented electrical mapping does not identify physical wheel
positions or signs. SWD remains enabled while JTAG is disabled for PA15/PB3.

## Command Contract

Commands are ASCII lines terminated by LF:

- `CONFIG <CN 1..4> <motor sign -1|1> <encoder sign -1|1> <reviewed max duty permille> <watchdog ms>`
- `ARM`
- `RUN <direction -1|1> <duty permille>`
- `HEARTBEAT`
- `STOP` or `DISARM`
- `RESET`

The firmware deliberately contains no default values for the four user-supplied
fields in `CONFIG`. The numeric representation accepts duty up to 1000 and a
watchdog up to 10000 ms; those are protocol bounds, not safe physical
recommendations. A reviewed session must select a substantially justified
test limit based on electrical preflight. RUN must not exceed that selected
limit. Any malformed/out-of-range command, serial fault, telemetry failure, or
watchdog expiry removes CCER/MOE and clears all CCR values.

Status JSONL reports neutral connector identity, explicit configuration,
requested/electrical direction, applied duty, four raw counters, and only the
configured encoder-sign-adjusted selected delta. It must not be used as
odometry until physical mapping, direction, and counts/revolution are measured.

## Build And Manual Gate

Keil project:
`firmware/openrf1/keil/OpenRF1_Motor_Bringup.uvprojx`.

Building alone does not authorize flashing. Before any manual use, obtain:

1. measured battery polarity and battery/VIN/5 V/3.3 V voltages;
2. verified encoder A/B high levels and installed 3.3 V pull-ups;
3. fuse/current-limit and raised-or-removed wheel evidence;
4. power-off CN1-CN4-to-wheel trace and roller-layout record;
5. a user-selected CH340 COM port;
6. a reviewed connector, motor sign, encoder sign, maximum test duty, and
   watchdog duration;
7. separate explicit authorization to flash, open the port, energize the
   controller, and issue a nonzero command.

The first powered action, when separately authorized, is one raised wheel at
the minimum reviewed duty, immediately followed by STOP and a physical
stop-response check. Do not proceed to another wheel if the selected wheel,
direction, counter response, watchdog, or STOP behavior differs from the
reviewed test card.

