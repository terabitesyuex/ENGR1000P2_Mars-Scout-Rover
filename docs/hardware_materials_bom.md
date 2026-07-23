# Hardware Materials And Connector BOM

For installation order and point-to-point destinations, use
[`openrf1_rover_wiring_plan_zh.md`](openrf1_rover_wiring_plan_zh.md). This BOM
retains procurement quantities, evidence boundaries, and acceptance checks.
The user subsequently reported that the complete vehicle was assembled.
Exterior and underside-sensor photographs plus supplied geometry are archived,
but electrical acceptance measurements and controller-bay evidence remain
missing. Continue from
[`near_term_vehicle_bringup_handoff.md`](near_term_vehicle_bringup_handoff.md);
do not treat this purchasing list as proof of installed or accepted hardware.

This document is the current purchasing and bench-preparation baseline for the Mars Scout Rover. It separates confirmed inventory from materials that may be purchased now and interfaces that still require measurement. Do not substitute a connector family only because the pin count looks correct.

## Locked Physical Inventory

CONFIRMED:

- RPLIDAR C1: 1 physical unit.
- HC-SR04: 3 physical units.
- TCRT5000 digital tracking module: 2 physical units.
- Hall sensor module: 1 physical unit.
- MPU6050: 1 physical unit.
- BH1750: 1 physical unit.
- BMP280: 1 physical unit.
- OpenRF1 STM32 controller: 1 physical unit.
- ESP32 board: 1 physical unit.
- Four encoded motors, four mecanum wheels, chassis, seller-documented 11.1 V
  7800 mAh 5C Li-ion pack, and seller-documented 12.6 V/1 A charger.

There is no second physical C1. Do not buy or plan around a second C1 unless the inventory is deliberately changed later.

## Immediate Purchase List

| Priority | Item | Minimum quantity | Purchase requirement | Purpose |
| --- | --- | ---: | --- | --- |
| Required | 10 kOhm resistors | 10 | 1%, 1/4 W, through-hole | Four independent divider assemblies plus spares |
| Required | 15 kOhm resistors | 10 | 1%, 1/4 W, through-hole | Four independent divider assemblies plus spares |
| Required | OpenRF1 CN6 cable | 2 | JST PH 2.0 mm, 4 positions, `PHR-4` housing with correctly crimped leads | One working cable and one spare for the single CN6 HC-SR04 path |
| Required | OpenRF1 tracking cable | 2 | Matching `HDGC2001H-6P` housing with `HDGC2001-T` terminals, or an explicitly matched pre-crimped cable | One working cable and one spare for the six-pin ground-sensor connector |
| Required | 2.54 mm Dupont jumper assortment | 1 set of each missing style | Male-male, male-female, and female-female | Module-side bench adaptation only; never force into PH 2.0 mm |
| Required | Breadboard or terminal fan-out | 1 | Sufficient independent rows for four dividers and split power/ground | Safe, inspectable prototype connections |
| Required | Hook-probe or mini-grabber leads | 2 pairs | Insulated, suitable for fine connector pins | Voltage checks without hand-slipping probes |
| Required | Multicolor signal wire | About 3 m per color, 6 colors | 26 to 28 AWG stranded | Sensor signal and low-current wiring; add 30% to measured route lengths |
| Required | Red and black low-voltage power wire | About 3 m each | 22 to 24 AWG stranded | 5 V and ground distribution; add 30% to measured route lengths |
| Required | Heat-shrink assortment | 1 set | Fits resistor joints and wire splices | Insulation and strain relief |
| Required | Wire labels and cable ties | 1 set each | Writable or numbered labels | Preserve sensor identity and connector orientation |
| Required | Vernier caliper | 1 | 0.1 mm or better resolution | Connector pitch, mounting-hole, and wire-route measurement |
| Required | Solder, flux, and insulating tape | 1 suitable set | Electronics grade | Harness assembly, rework, and temporary insulation |

For the CN6 cable, a factory pre-crimped PH 2.0 mm four-position pigtail is preferred. If assembling it, use official JST-compatible parts:

- Board header: `B4B-PH-K-S(LF)(SN)`.
- Line housing: `PHR-4`.
- Terminal for AWG 30 to 24: `SPH-002T-P0.5S`.
- Terminal for AWG 32 to 28: `SPH-004T-P0.5S`.
- Low-insertion-force terminal option for AWG 28 to 24: `SPH-002T-P0.5L`.

The existing 2.54 mm Dupont leads do not fit the 2.0 mm PH CN6 connector and must not be forced into it.

For the ground-sensor cable:

- Board header: `HDGC2001WV-6P`.
- Matching line housing: `HDGC2001H-6P`.
- Matching crimp terminal: `HDGC2001-T`.

Use the matching family or an explicitly documented mate. Do not assume a generic six-position JST-style housing has the same keying or contact geometry.

## Divider Allocation

DESIGN_LOCKED:

Four independent 10 kOhm / 15 kOhm divider assemblies are required for the final planned sensor set:

| Divider | Source | Protected STM32 input | Current status |
| --- | --- | --- | --- |
| 1 | HC-SR04 unit 1 ECHO | CN6 PA4 for isolated baseline | Wiring not yet physically verified |
| 2 | HC-SR04 unit 2 ECHO | GPIO/interface UNVERIFIED | Do not connect until assigned |
| 3 | HC-SR04 unit 3 ECHO | GPIO/interface UNVERIFIED | Do not connect until assigned |
| 4 | Hall sensor S | Ground connector PB0 | Required before PB0; formal voltage evidence incomplete |

Each divider is wired as follows:

`5 V logic source -> 10 kOhm series resistor -> protected input node -> 15 kOhm resistor -> common GND`

Do not share the midpoint of a divider between sensors. Each HC-SR04 ECHO and the Hall output must have its own divider pair in final simultaneous wiring.

MANUAL_EVIDENCE_VERIFIED for preliminary loose-component screening only:

- A nominal 10 kOhm resistor displayed 9.56 kOhm. This is within a 5% tolerance band of 9.50 to 10.50 kOhm.
- A nominal 15 kOhm resistor displayed 14.05 kOhm. This is below the 5% lower limit of 14.25 kOhm and must not be used for formal divider evidence.

These readings do not verify an installed divider, meter calibration, loaded voltage, or the final wiring. Use the recommended 1% parts and record the actual installed values before connection to STM32 inputs.

## HC-SR04 Three-Unit Constraint

The repository currently defines only one authoritative HC-SR04 hardware path:

- CN6 pin 1: 5 V.
- CN6 pin 2: GND.
- CN6 pin 3: PA5 TRIG.
- CN6 pin 4: PA4 ECHO after the required divider.
- Firmware timer: TIM6.

The single CN6 path can test the three physical HC-SR04 modules one at a time using the same known-good cable. Two CN6 pigtails are sufficient for this isolated stage because they provide a working cable and a spare. Label each module and each evidence capture so sequential tests are not mistaken for simultaneous operation.

UNVERIFIED:

- GPIO assignments for HC-SR04 units 2 and 3.
- Connector assignments for HC-SR04 units 2 and 3.
- Timer/capture resources for HC-SR04 units 2 and 3.
- Final identities and mounting locations for all three units.
- Staggered-trigger scheduling and cross-talk behavior.
- Three-sensor simultaneous power and signal integrity.

Do not claim that three sensors can connect to CN6. Do not repurpose the lower six-pin motor/encoder connectors or the ground-sensor connector without a separately reviewed schematic, firmware target, conflict analysis, and physical validation.

## Fan-Out Materials

One-to-many wiring is required in several places. Plan the split explicitly rather than twisting conductors together:

- Common ground: OpenRF1, all active sensors, ESP32 communication ground, and measurement equipment reference require a controlled common-ground distribution point.
- HC-SR04 power: three modules will eventually need separate 5 V branches from a suitable distribution point.
- Divider ground: all four 15 kOhm pulldown legs need their own reliable return to common ground.
- I2C signals: BH1750, BMP280, and MPU6050 share SCL/SDA signal lines, but their power rails are not one shared VCC connection.
- I2C power: BH1750 and MPU6050 use the documented 5 V module supply; BMP280 uses the documented 3.3 V module supply.
- Tracking connector: the two TCRT5000 modules use 3.3 V while the Hall module uses 5 V; only ground is common.

Suitable fan-out materials include a solderless breadboard for bring-up, screw terminal distribution blocks for a stable bench, and soldered stripboard or a small distribution PCB for final installation. Do not use a loose one-to-many Dupont stack as permanent vehicle wiring.

## Already Available Or Previously Used

CONFIRMED or MANUAL_EVIDENCE_VERIFIED:

- Digital multimeter is now available.
- 2.54 mm Dupont leads are available, but they are not a substitute for PH 2.0 mm or other keyed connector housings.
- Keil MDK/uVision and the OpenRF1 build flow have been used.
- FlyMcu and the OpenRF1 bootloader flashing flow have been used.
- CH340/USART1 serial telemetry has been used.
- OpenRF1 Micro-USB data connection has been used; the number and quality of spare data cables remain UNVERIFIED.

Before relying on any existing USB cable, confirm it carries data rather than power only.

## Recommended Bench Tools

These are not all mandatory for the next isolated test, but they materially reduce risk and diagnosis time:

| Tool | Recommended capability | Main use |
| --- | --- | --- |
| Oscilloscope | 2 channels, at least 20 MHz | Verify TRIG width, ECHO amplitude, divider output, timing, ripple, and noise |
| Logic analyzer | 8 channels, at least 24 MHz, 3.3 V compatible | Compare staggered triggers, UART, I2C, and GPIO timing |
| Bench power supply | Adjustable, current limited, voltage/current display | Controlled first power-up and current measurement |
| Fine hook probes | Insulated, low-slip | Probe small connector and divider nodes safely |
| JST/compatible crimp tool | Correct die for the selected terminals | Only needed when not buying pre-crimped leads |
| Wire stripper and flush cutter | Suitable for 22 to 30 AWG | Harness assembly |
| Soldering iron and heat gun | Temperature controlled | Final divider/harness assembly and insulation |
| ST-Link V2 with SWD cable | STM32F1 compatible | Backup debug/programming route, not required for the current FlyMcu flow |

Do not connect a measurement instrument until its ground-reference implications are understood. Keep motor power off during low-level sensor bring-up.

## Power Materials

### RPLIDAR C1

The single physical C1 should use its original `XH2.54-5P` harness and supplied USB adapter where available. The five-position connector has four active conductors and one unused position in the documented kit wiring. A spare housing or breakout is optional and must be checked against the actual keyed connector before purchase; do not order an `XHP-5` solely because it appears to be a plausible candidate.

Required C1 supply contract:

- Independent regulated 5 V source rated at least 2 A for one C1 bench/integration path.
- Operating range: 4.8 to 5.2 V.
- Startup-current planning value: approximately 800 mA.
- Supply ripple: less than 150 mV.
- UART: 3.3 V TTL, 460800 baud, 8N1.

Do not add an external C1 motor PWM wire. C1 motor control is internal to the unit.

### Whole Rover

The battery product page documents 11.1 V nominal, 7800 mAh, 5C, 12.6 V fully
charged, 70 x 55 x 23 mm, and a DC 5.5 x 2.5 mm male connector. Its matching
charger is advertised as 12.6 V/1 A with a DC 5.5 x 2.5 mm female connector.
These facts resolve the advertised voltage, capacity, rate, dimensions, and
connector size, but not polarity or BMS continuous/peak current. The final
whole-rover wire gauge, fuse value, and distribution remain blocked on those
values and controlled motor-current measurements. Useful purchases after those
checks include:

- Main power switch or emergency disconnect.
- Replaceable fuse holder and correctly sized fuse.
- Separate fused logic/sensor power branch.
- Proper power distribution block.
- DC 5.5 x 2.5 mm female battery adapter with sufficient current rating and a
  rover-side plug selected only after measuring the actual OpenRF1 jack.
- Bulk and local decoupling selected from measured transients and ripple, not guesswork.

Do not choose the final fuse from nominal motor current alone.
Do not charge while the battery is connected to the rover, and do not use the
12.6 V/1 A charger as the rover operating supply.

### ESP32

Plan four controlled connections for the STM32 communication path: 5 V, GND, TX, and RX. Add a removable 5 V jumper or switch so external OpenRF1 5 V and ESP32 USB power cannot be applied simultaneously. Buy a USB data cable only after confirming the actual ESP32 connector type.

## Vehicle Installation Materials

Purchase exact fastener sizes only after measuring the modules and chassis:

- One adjustable C1 mount with unobstructed scan plane.
- Three HC-SR04 brackets, each with angle adjustment.
- Two TCRT5000 height/angle-adjustable brackets.
- One Hall sensor bracket with repeatable magnet clearance.
- One rigid MPU6050 mount with known rover-frame orientation.
- Protected, ventilated mounts for BH1750 and BMP280.
- Standoffs for OpenRF1 and ESP32.
- M2, M2.5, and M3 fastener assortments after hole measurements.
- Thread-locking method appropriate for the fastener and plastic parts.
- Adhesive cable clips, reusable ties, braided sleeve, and strain relief.
- Labels for both ends of every harness.
- Perforated board or a small dedicated PCB for the four divider circuits.

Calibration/test targets:

- Flat hard target for HC-SR04 testing.
- Tape measure or rigid rule at least 3 m long.
- Light and dark surface samples for both TCRT5000 modules.
- Safe raised-edge/drop test board that cannot let the rover fall.
- Suitable magnet with a marked pole for the Hall sensor.
- Level surface and alignment square for mounting checks.

## Must Measure Before Purchasing More Connectors Or Power Parts

MANUAL_ACTION_REQUIRED:

1. Identify schematic-safe GPIO, connector, and timer resources for HC-SR04 units 2 and 3.
2. Measure and identify the exact family, pitch, keying, and pinout of the four lower motor/encoder connectors.
3. Confirm the mechanical connector and electrical mapping for USART2 and USART3.
4. Measure battery and charger barrel polarity and pack full-charge voltage;
   obtain the BMS continuous/peak current and overcurrent-trip specification.
5. Measure each motor's stall current using a controlled method before selecting final wire gauge, regulator, fuse, or connector.
6. Confirm the ESP32 board model and USB connector type.
7. Measure all sensor-module header pitches and mounting-hole diameters.
8. Measure final routed wire lengths and add at least 30% service/strain-relief allowance.
9. Confirm the quantity and data capability of existing Micro-USB cables.
10. Inspect the actual C1 harness keying and adapter before ordering a spare.

Until these measurements are recorded, use `UNVERIFIED` rather than a guessed connector or power rating.

## Do Not Buy Or Substitute Yet

- A second RPLIDAR C1; the current physical baseline contains one C1.
- Raspberry Pi, Jetson, other vehicle Linux computer, ROS, ROS 2, Nav2, AMCL, Gmapping, or `slam_toolbox` hardware/software as baseline requirements.
- Generic six-pin motor/encoder plugs chosen only by appearance.
- Generic PH/XH housings assumed to mate across families.
- Three CN6 cables on the assumption that CN6 accepts three HC-SR04 modules simultaneously.
- External I2C pull-ups or a level shifter without measuring the existing bus/module topology first.
- A generic I2C hub that ties every module VCC together.
- A final rover fuse or motor-wire gauge before BMS limits and controlled
  motor-current measurements are recorded.
- An external C1 motor-control/PWM cable.
- Permanent loose Dupont wiring for vehicle power, motor, or vibration-exposed connections.

## Acceptance On Receipt

Before using purchased parts:

1. Power off all boards.
2. Compare housing keying and latch position with the board connector.
3. Check every pre-crimped wire for retention.
4. Map pin numbers before assigning wire colors.
5. Continuity-test each cable end to end.
6. Check for shorts between adjacent contacts.
7. Measure each resistor and label accepted pairs.
8. Assemble one divider and verify its ratio with a current-limited 5 V source before connecting an STM32 input.
9. Record photos, measured values, batch/source, and the cable orientation used.

## Reference Sources

- JST PH series connector data: <https://www.jst-mfg.com/product/pdf/eng/ePH.pdf>
- Ground connector board header listing (`HDGC2001WV-6P`): <https://www.lcsc.com/product-detail/C5175234.html>
- Ground connector line housing listing (`HDGC2001H-6P`): <https://www.lcsc.com/product-detail/C5292555.html>
- Ground connector terminal listing (`HDGC2001-T`): <https://www.lcsc.com/product-detail/C5292557.html>
- RPLIDAR C1 data sheet: <https://wiki.slamtec.com/download/attachments/83066883/SLAMTEC_rplidar_datasheet_C1_v1.0_en.pdf?api=v2>
- RPLIDAR C1 kit manual: <https://wiki.slamtec.com/download/attachments/83066883/SLAMTEC_rplidarkit_usermanual_C1_v1.0_en.pdf?api=v2>
