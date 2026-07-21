# OpenRF1 HC-SR04 Bring-Up

Phase 3.2E implements the isolated HC-SR04 software bring-up path for one sensor on the OpenRF1 STM32F103RCT6 controller. No physical verification has yet occurred.

## Source Status

AUTHORITATIVE_VENDOR_DOCUMENTED:

- Source family: OpenRF1 vendor control-board package.
- Firmware reference: ultrasonic sensor example.
- Schematic source: OpenRF1 schematic revision dated 2024-07-01.
- HC-SR04 connector: CN6, B4B-PH-K-S(LF)(SN).
- CN6 pin 1: VCC_5V.
- CN6 pin 2: GND.
- CN6 pin 3: PA5_TRIG.
- CN6 pin 4: PA4_ECHO.
- TRIG: PA5, GPIOA, push-pull output.
- ECHO: PA4, GPIOA, digital input.
- Timer resource: TIM6.
- Timer configuration: prescaler 71, period 30000, nominal 1 us count at the established 72 MHz timer clock.
- External ECHO divider requirement: HC-SR04 ECHO -> 10 kOhm series resistor -> protected PA4 / CN6-pin-4 node; protected PA4 node -> 15 kOhm resistor -> GND; resistors 5 percent tolerance or better.

These facts are design-locked from vendor material. They are not physical evidence for this rover.

## Electrical Safety Contract

Do not connect HC-SR04 ECHO directly to CN6 pin 4.

- HC-SR04 VCC for the vendor CN6 connector is VCC_5V.
- STM32 PA5 TRIG output is a 3.3 V GPIO output.
- HC-SR04 ECHO output may reach the module supply voltage.
- The OpenRF1 schematic connects CN6 pin 4 directly to PA4_ECHO.
- No board-level resistor divider, buffer, or level shifter is present on PA4_ECHO.
- PA4 is not treated as 5 V tolerant in this project.
- The external 10 kOhm / 15 kOhm divider is required before ECHO reaches PA4.
- Nominal divider behavior: 5.0 V ECHO becomes approximately 3.0 V; 5.5 V ECHO becomes approximately 3.3 V.

Disconnect all power before changing wiring. Check printed module labels rather than assuming left-to-right order. Only HC-SR04 should be connected for isolated validation. ECHO voltage compatibility must be confirmed before connection, and raw 5 V must not be applied to an unverified STM32 input. Measurements are nominal and uncalibrated.

Soft materials and angled surfaces may produce weak or missing echoes. Very close objects may fall inside the module practical blind region.

## IMPLEMENTED / SOFTWARE_READY

- Isolated firmware path under `firmware/openrf1/hcsr04_bringup/`.
- Dedicated Keil target `firmware/openrf1/keil/OpenRF1_HCSR04_Bringup.uvprojx`.
- Output directory `Objects_HCSR04_Bringup`.
- Expected HEX name `OpenRF1_HCSR04_Bringup.hex`.
- PA5 trigger setup and PA4 echo setup represented in source.
- TIM6 1 MHz timer contract represented in source.
- Bounded wait for ECHO low before trigger.
- Bounded rising-edge timeout.
- Bounded falling-edge timeout.
- 30000 us timeout contract.
- Timer-wrap-safe pulse-width subtraction.
- 100 ms scheduled measurement attempts.
- Raw `echo_pulse_us` preserved.
- Nominal integer distance conversion: `distance_mm = round(pulse_width_us * 343 / 2000)`.
- Explicit JSONL startup identity, success, and error records.
- Error records do not emit fake zero distance or stale distance.
- Host-side tests and Phase 3.2E software audit.
- Strict host parser and dedicated `capture-openrf1-hcsr04` mockable capture path.
- Maximum serialized JSONL line contract: 512 ASCII bytes including newline and excluding the C-string NUL.
- Firmware buffer contract: 513 bytes including the trailing NUL. This replaces the former 768-byte buffer and reduces static RAM use by 255 bytes.
- Formatter failure is surfaced with `telemetry_format_failure`; it is not silently dropped.

The bounded synchronous polling in this isolated diagnostic firmware can block one measurement attempt for up to the 30000 us timeout. It is intentionally retained for low-risk isolated bring-up and is not a non-blocking production runtime. Future full-hardware integration must use the existing non-blocking state-machine foundation; this phase does not implement three-sensor concurrent acquisition.

## UNVERIFIED

- Physical HC-SR04 validation status: PHYSICAL_VERIFICATION_REQUIRED.
- Actual board connector orientation.
- Actual cable orientation.
- Installed resistor values.
- Real ECHO voltage before division.
- Real ECHO voltage after division.
- Actual sensor power wiring.
- Physical trigger pulse.
- Physical echo pulse.
- Real distance data.
- Physical timer accuracy.
- Physical timeout behavior.
- Actual 100 ms serial timing.
- Minimum useful distance.
- Maximum useful distance.
- Angle sensitivity.
- Surface sensitivity.
- Absolute distance accuracy.
- Temperature compensation.
- Long-duration stability.
- Full-hardware operation.

## JSONL Identity Record

The firmware emits one identity record after successful local GPIO/timer initialization. It is software configuration only and does not claim the sensor replied.

```json
{"protocol":"mars_scout_stm32_sensor_telemetry","version":1,"sequence":0,"timestamp_ms":0,"message_type":"sensor_identity","sensor_id":"ultrasonic_1","status":"ok","payload":{"sensor":"hc-sr04","connector":"CN6","trigger_pin":"PA5","echo_pin":"PA4","timer":"TIM6","timer_tick_hz":1000000,"trigger_pulse_us":10,"echo_timeout_us":30000,"measurement_period_ms":100,"distance_unit":"mm","distance_model":"nominal_343_m_per_s_uncalibrated"}}
```

## JSONL Success Record

```json
{"protocol":"mars_scout_stm32_sensor_telemetry","version":1,"sequence":1,"timestamp_ms":100,"message_type":"ultrasonic","sensor_id":"ultrasonic_1","status":"ok","payload":{"echo_pulse_us":2000,"distance_mm":343,"distance_model":"nominal_343_m_per_s_uncalibrated"}}
```

## JSONL Error Record

```json
{"protocol":"mars_scout_stm32_sensor_telemetry","version":1,"sequence":1,"timestamp_ms":100,"message_type":"ultrasonic","sensor_id":"ultrasonic_1","status":"error","payload":{"echo_pulse_us":null,"distance_mm":null,"distance_model":"nominal_343_m_per_s_uncalibrated"},"error":{"code":"echo_rise_timeout","operation":"wait_for_echo_rising_edge","timeout_us":30000}}
```

Supported error codes:

- `echo_not_low_before_trigger`
- `echo_rise_timeout`
- `echo_fall_timeout`
- `timer_configuration_failure`
- `timer_measurement_failure`
- `pulse_width_out_of_bounds`
- `telemetry_format_failure`
- `internal_state_error`

The PC rejects an encoded line longer than 512 bytes, invalid UTF-8 input, unknown fields, inconsistent pulse/distance pairs, incorrect sensor IDs, non-increasing sequence values, and timestamp rollback. Firmware output remains ASCII-compatible JSON. The fixture-backed capture summary always retains `manual_review_required: true` and `physical_status: PHYSICAL_VERIFICATION_REQUIRED`.

## Future Physical Validation Checklist

- [ ] Confirm official Keil build success.
- [ ] Record generated HEX SHA-256.
- [ ] Remove board power.
- [ ] Verify TRIG and ECHO pin mapping.
- [ ] Verify ECHO voltage-divider or level-shifter wiring.
- [ ] Confirm common ground.
- [ ] Connect only HC-SR04.
- [ ] Flash with FlyMcu.
- [ ] Reset and capture the startup identity record.
- [ ] Confirm 100 ms scheduled attempts.
- [ ] Place a flat hard target at a stable near distance.
- [ ] Capture stable pulse-width and distance telemetry.
- [ ] Move the target farther away.
- [ ] Confirm pulse width and nominal distance increase.
- [ ] Move the target closer.
- [ ] Confirm pulse width and nominal distance decrease.
- [ ] Temporarily remove or strongly angle the target.
- [ ] Confirm bounded timeout/error telemetry rather than fake distance.
- [ ] Restore a valid target.
- [ ] Confirm successful measurements resume.
- [ ] Save raw JSONL without modification.
- [ ] Record capture hash.
- [ ] Record the actual reference distances separately.
- [ ] Do not claim calibrated absolute accuracy unless compared with a reference instrument under a defined method.

Future formal evidence should demonstrate successful distance records and at least one observable bounded error path if safely reproducible.
