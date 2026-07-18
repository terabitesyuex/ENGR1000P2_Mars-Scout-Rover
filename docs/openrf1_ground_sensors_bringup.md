# OpenRF1 Ground-Sensor Bring-Up

Phase 3.2F implements the isolated software bring-up path for two TCRT5000 digital reflective modules and one HW-477/A3144 Hall module on the OpenRF1 STM32F103RCT6 controller. No physical verification has yet occurred.

## Source Status

AUTHORITATIVE_VENDOR_DOCUMENTED:

- Source family: OpenRF1 vendor control-board package.
- Firmware reference: OpenRF1 four-channel tracking example.
- Schematic source: OpenRF1 schematic revision dated 2024-07-01.
- Connector: OpenRF1 four-channel tracking connector, HDGC2001WV-6P.
- signal 1 / X1 / PC4.
- signal 2 / X2 / PC5.
- signal 3 / X3 / PB0.
- Vendor tracking example input mode: floating input.
- Connector pin 1: GND.
- Connector pin 2: X4 / schematic PC14.
- Connector pin 3: X3 / PB0.
- Connector pin 4: X2 / PC5.
- Connector pin 5: X1 / PC4.
- Connector pin 6: VCC_5V.
- Schematic X4 mapping: PC14.
- The old example maps X4 to PB1.

The project logical assignment for this phase is:

| Logical channel | Planned module signal | Connector signal | MCU pin | Status |
| --- | --- | --- | --- | --- |
| left TCRT5000 OUT | left TCRT5000 OUT | signal 1 / X1 / PC4 | PC4 | AUTHORITATIVE_VENDOR_DOCUMENTED mapping; physical wiring UNVERIFIED |
| right TCRT5000 OUT | right TCRT5000 OUT | signal 2 / X2 / PC5 | PC5 | AUTHORITATIVE_VENDOR_DOCUMENTED mapping; physical wiring UNVERIFIED |
| Hall S protected node | Hall S after external divider | signal 3 / X3 / PB0 | PB0 | AUTHORITATIVE_VENDOR_DOCUMENTED mapping; physical wiring UNVERIFIED |

## X4 Conflict

The schematic says PC14 for signal 4 / X4. The old example maps X4 to PB1. PB1 is already used and physically verified in this repository as the software-I2C SCL line.

DESIGN_LOCKED:

- signal 4 / X4 is unused in Phase 3.2F.
- Do not initialize signal 4.
- Do not read signal 4.
- Do not include signal 4 in periodic telemetry.
- Do not adopt the old example's PB1 mapping.
- Do not modify PB1.
- Do not infer a resolved X4 physical mapping from the conflict.

## Wiring Contract

Disconnect all power before changing wiring. Verify printed pin labels and connector orientation from labels, keying, or schematic references. Do not infer pin order from wire colours, apparent left-to-right order in a photograph, cable orientation, or connector position alone.

Do not share one VCC rail across all three modules. The connector's VCC_5V pin is vendor-documented, but it is not the controlled bring-up supply for the TCRT5000 modules.

- do not share one VCC rail across all three modules.

LEFT TCRT5000:

- OUT -> connector signal 1 / X1 / PC4.
- VCC -> STM32 3.3 V.
- GND -> common GND.
- do not power the TCRT modules from the connector's 5 V pin during controlled bring-up.

RIGHT TCRT5000:

- OUT -> connector signal 2 / X2 / PC5.
- VCC -> STM32 3.3 V.
- GND -> common GND.
- do not power the TCRT modules from the connector's 5 V pin during controlled bring-up.

HALL MODULE:

- + -> 5 V.
- - -> common GND.
- S -> external 10 kOhm / 15 kOhm divider -> connector signal 3 / X3 / PB0.

Do not connect Hall S directly to PB0.

Use the required external divider:

- Hall S -> 10 kOhm resistor -> protected PB0 node.
- protected PB0 node -> 15 kOhm resistor -> GND.
- Resistor tolerance: 5 percent or better.
- Nominal divider behavior: 5.0 V input -> approximately 3.0 V at PB0; 5.5 V input -> approximately 3.3 V at PB0.

Only these modules should be connected during isolated validation. Signal 4 remains unused. Physical polarity is unverified, and raw GPIO values are not semantic detection states.

## Electrical Notes

The TCRT5000 modules are three-pin digital modules labelled OUT, VCC, and GND. The module PCB appears to contain digital conditioning logic, but the exact logic-chip identity, threshold, output topology, active polarity, black/white behavior, and edge/open-space behavior are UNVERIFIED.

The physical Hall module is marked HW-477 V0.2 and the sensor is marked 3144. The A3144 sensor-level datasheet establishes that the sensor output is open collector, needs a pull-up path, and is active-low for the appropriate magnetic pole. The HW-477 module-level pull-up and LED circuit are not authoritatively documented, so Hall S voltage before and after the divider remains UNVERIFIED. The user currently does not have a multimeter.

## IMPLEMENTED / SOFTWARE_READY

- Isolated firmware path under `firmware/openrf1/ground_sensors_bringup/`.
- Dedicated Keil target `firmware/openrf1/keil/OpenRF1_GroundSensors_Bringup.uvprojx`.
- Output directory `Objects_GroundSensors_Bringup`.
- Expected HEX name `OpenRF1_GroundSensors_Bringup.hex`.
- PC4, PC5, and PB0 configured as floating input.
- Startup state initialized from a real GPIO read of all three active inputs.
- Deterministic 5 ms GPIO sampling.
- Independent 4-sample debounce per channel.
- Effective 20 ms stability requirement.
- Deterministic 50 ms strict JSONL telemetry.
- Raw and debounced numeric levels for all three active channels.
- signal 4 / X4 excluded from firmware sampling and telemetry.
- USART1 / CH340 JSONL output only; no startup prose or debug banner.
- Host-side tests and Phase 3.2F software audit.

## UNVERIFIED

- Physical ground-sensor validation status: PHYSICAL_VERIFICATION_REQUIRED.
- Physical connector orientation.
- Cable orientation.
- Actual 3.3 V rail.
- Actual 5 V rail.
- Actual TCRT output voltage.
- TCRT output topology.
- Left TCRT active polarity.
- Right TCRT active polarity.
- Hall module-level output voltage.
- Hall S high voltage.
- Hall S low voltage.
- Divider input voltage.
- Divider output voltage.
- Actual divider resistor values.
- Hall active polarity.
- Hall triggering magnetic pole.
- Hall release behavior.
- White-surface response.
- Black-surface response.
- Edge/open-space response.
- Magnetic activation.
- Magnetic release.
- Optical threshold.
- Hall trigger distance.
- Real debounce suitability.
- Disconnected-sensor behavior.
- Actual 50 ms serial periodicity.
- Long-duration stability.
- Moving-rover drop prevention.
- Full-hardware operation.

Semantic polarity remains unverified. The runtime emits electrical `raw_level` and `debounced_level` only.

## JSONL Identity Record

The firmware emits one identity record after GPIO and scheduler initialization. It is software configuration only and does not imply module presence.

```json
{"protocol":"mars_scout_stm32_sensor_telemetry","version":1,"sequence":0,"timestamp_ms":0,"message_type":"sensor_identity","sensor_id":"ground_sensors","status":"ok","payload":{"sensor_group":"ground_sensors","connector":"OpenRF1_four_channel_tracking","sample_period_ms":5,"telemetry_period_ms":50,"debounce_samples":4,"semantic_polarity":"unverified","channels":{"left_tcrt5000":{"connector_signal":1,"connector_label":"X1","mcu_pin":"PC4","supply":"3.3V"},"right_tcrt5000":{"connector_signal":2,"connector_label":"X2","mcu_pin":"PC5","supply":"3.3V"},"hall_sensor":{"connector_signal":3,"connector_label":"X3","mcu_pin":"PB0","module_supply":"5V","input_protection":"external_10k_15k_divider_required"}},"signal_4":{"status":"unused","mapping_conflict":"schematic_PC14_vendor_example_PB1"}}}
```

## JSONL Periodic Record

```json
{"protocol":"mars_scout_stm32_sensor_telemetry","version":1,"sequence":1,"timestamp_ms":50,"message_type":"ground_sensors","sensor_id":"ground_sensors","status":"ok","payload":{"left_tcrt5000":{"raw_level":0,"debounced_level":0},"right_tcrt5000":{"raw_level":1,"debounced_level":1},"hall_sensor":{"raw_level":1,"debounced_level":1}}}
```

Every output level is numeric `0` or `1`. No black, white, line, drop, edge, safe-ground, magnetic, or landmark semantic result is emitted in this phase.

## Future Physical Validation Checklist

Do not mark any item complete until real manual evidence exists.

1. [ ] Confirm official Keil build.
2. [ ] Record HEX SHA-256.
3. [ ] Remove all board power.
4. [ ] Verify connector orientation.
5. [ ] Verify signal 1 -> PC4.
6. [ ] Verify signal 2 -> PC5.
7. [ ] Verify signal 3 -> PB0.
8. [ ] Confirm signal 4 remains unused.
9. [ ] Confirm both TCRT modules receive 3.3 V.
10. [ ] Confirm Hall module receives 5 V.
11. [ ] Confirm all modules share common ground.
12. [ ] Confirm Hall S passes through the external 10 kOhm / 15 kOhm divider.
13. [ ] Confirm Hall S is not directly connected to PB0.
14. [ ] Flash isolated target.
15. [ ] Reset and capture identity record.
16. [ ] Confirm 50 ms periodic JSONL telemetry.
17. [ ] Record resting levels.
18. [ ] Test left TCRT over a light surface.
19. [ ] Test left TCRT over a dark surface.
20. [ ] Test left TCRT over a safe open edge or lifted condition.
21. [ ] Confirm only the left channel responds.
22. [ ] Repeat the same tests for the right TCRT.
23. [ ] Confirm only the right channel responds.
24. [ ] Test Hall with no magnet.
25. [ ] Approach the marked A3144 face with a suitable magnetic pole.
26. [ ] Observe raw and debounced transition.
27. [ ] Remove the magnet.
28. [ ] Confirm release transition.
29. [ ] Repeat transitions several times.
30. [ ] Determine actual electrical and semantic polarity.
31. [ ] Record Hall orientation and triggering pole.
32. [ ] Record whether 20 ms debounce is suitable.
33. [ ] Save raw JSONL without modification.
34. [ ] Hash raw evidence before integration.

When a multimeter later becomes available, add these incomplete checks:

- [ ] 3.3 V rail measurement.
- [ ] 5 V rail measurement.
- [ ] Left TCRT OUT high and low voltage.
- [ ] Right TCRT OUT high and low voltage.
- [ ] Hall S voltage before divider without magnet.
- [ ] Hall S voltage before divider with magnet.
- [ ] PB0 voltage after divider without magnet.
- [ ] PB0 voltage after divider with magnet.
- [ ] Actual divider resistor values when practical.
