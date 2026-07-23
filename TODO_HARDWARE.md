# Hardware Information TODO

This table is the single unresolved-hardware checklist for the unified
OpenRF1 rover-control application. unknown means no mapping may be encoded in
firmware. unverified means a proposed or module-level fact still needs
authoritative board evidence or controlled physical validation.
authoritative_vendor_documented and vendor_software_documented record resolved
board/source facts without claiming physical operation. design_locked records a
project wiring choice that still requires the named firmware or manual checks.
Use `docs/openrf1_rover_wiring_plan_zh.md` as the on-vehicle assembly checklist;
items below remain stop conditions where that checklist requires measurement.

| Item | Status | Information needed |
|---|---|---|
| Complete vehicle assembly | manual_evidence_verified exterior only | 2026-07-23 top/front/front-right/underside sensor photographs archived; controller wiring, continuity, rail voltages, protection, and integrated operation remain unverified |
| Four motor connector pinouts | authoritative_vendor_documented | CN1-CN4 pins 1 OUT2, 2 encoder 5 V, 3 A, 4 B, 5 GND, 6 OUT1; verify physical pin-1 orientation |
| Motor connector to logical wheel mapping | design_locked; physical validation required | Vendor mapping A/L1=CN2, B/R1=CN4, C/L2=CN1, D/R2=CN3; confirm FL/FR/RL/RR on blocks |
| Motor PWM GPIO | authoritative_vendor_documented | PC6, PC7, PC8, PC9 |
| Motor PWM timer and channel | vendor_software_documented | TIM8_CH1 through TIM8_CH4 |
| Motor direction GPIO or driver command scheme | vendor_software_documented | AT8236 IN1 GPIO PA8, PA11, PA12, PC10 plus IN2 PWM |
| Motor enable and brake/coast behavior | partially_resolved | AT8236 truth table and vendor drive code known; final explicit coast/brake/emergency-stop policy still required |
| Motor PWM frequency and polarity | vendor_software_documented | PWM1 active high, approximately 17.99 kHz from 72 MHz, PSC 1, ARR 2000 |
| Motor command sign per wheel | unknown | Verified wheel mounting and controlled wheel-on-blocks test |
| Encoder connector pinouts | authoritative_vendor_documented | Encoder supply/A/B/GND are motor-connector pins 2/3/4/5 |
| Encoder A GPIO for all four wheels | authoritative_vendor_documented | CN1 PA0, CN2 PA6, CN3 PA15, CN4 PB6 |
| Encoder B GPIO for all four wheels | authoritative_vendor_documented | CN1 PA1, CN2 PA7, CN3 PB3, CN4 PB7 |
| Encoder timer/EXTI resources | vendor_software_documented | CN1 TIM5, CN2 TIM3, CN3 TIM2 full remap, CN4 TIM4 in encoder TI12 mode |
| Encoder electrical input levels and pull configuration | design_locked; output topology unknown | Encoder accepts 3.3-5 V and output high follows VCC; leave connector pin 2 unused, power blue wires at 3.3 V, add eight 10 kOhm A/B pull-ups |
| Encoder sign per logical wheel | unknown | Verified wheel mounting and controlled rotation test |
| Encoder 11 PPR interpretation | user_confirmed | 11 A cycles and 11 B cycles per motor-shaft revolution |
| 30:1 gearbox ratio | user_confirmed_nominal | Exact mechanical tolerance remains unverified |
| 1320 counts/output revolution | user_confirmed_nominal | 11 x 30 x 4; retain controlled one-revolution validation |
| Wheel diameter / radius | manual_evidence_verified supplied measurement | 79 mm diameter / 39.5 mm radius; verify tolerance and loaded-condition repeatability |
| Wheelbase / half wheelbase | manual_evidence_verified supplied measurement | 190 mm / 95 mm axle-centre value |
| Track width / half track width | manual_evidence_verified supplied measurement | 217 mm / 108.5 mm wheel-centre value |
| Motor current and no-load speed | user_confirmed | 0.36 A no-load, 3.2 A stall per motor, 330 rpm no-load output speed |
| Maximum usable wheel speed | unknown | Loaded motor, supply, chassis, and encoder measurement |
| Mecanum roller orientation and wheel placement | partially documented | Assembly photos show four mecanum wheels and marked vehicle front; exact handedness/X-layout still requires a clear wheel record or controlled motion test |
| Battery advertised electrical values | seller_documented | Li-ion, 11.1 V nominal, 7800 mAh, 5C, 12.6 V fully charged; source images and hashes archived |
| Battery advertised physical values | seller_documented | 70 x 55 x 23 mm and DC 5.5 x 2.5 mm male barrel connector; verify actual fit and dimensions |
| Battery-to-OpenRF1 VIN topology | user_approved_design | Direct connection through main fuse and latching disconnect; physical validation still required |
| Battery BMS current limits | unverified | Exact continuous/peak discharge, overcurrent-trip, and recovery specifications or controlled measurement; advertised 5C only calculates to 39 A and is not a BMS rating |
| Battery connector polarity and measured voltage | unverified | Multimeter-confirm centre/sleeve polarity, no-load voltage, and fully charged voltage before adapter construction |
| Battery charger | seller_documented; physical validation required | 110-240 VAC 50/60 Hz input, 12.6 V/1 A output, DC 5.5 x 2.5 mm female, 100 cm cable; verify polarity/regulation and charge only with rover disconnected |
| Battery voltage/current telemetry ADC path | unknown | OpenRF1 schematic and divider/current-sense definition |
| RPLIDAR C1 STM32 UART and pins | authoritative_vendor_documented | H5 pin 3 PA2/TX2, pin 4 PA3/RX2; physical C1 link still unverified |
| ESP32 STM32 UART and pins | authoritative_vendor_documented | H6 pin 3 PB11/RX3, pin 4 PB10/TX3; physical ESP32 link still unverified |
| ESP32-C3 SuperMini model and UART pins | user_confirmed | GPIO21 TX and GPIO20 RX; installed link still needs physical validation |
| ESP32-C3 SuperMini LDO | unverified | Physical regulator marking or exact board schematic; AMS1117-class rating is provisional |
| Two additional HC-SR04 paths | design_locked; firmware required | H3 PB9 TRIG/PB8 ECHO and PD2 TRIG/PC11 ECHO, one 10 kOhm/15 kOhm divider per ECHO |
| Shared MPU6050/BMP280/BH1750 I2C concurrency | unverified | Combined-bus firmware and physical validation |
| Final sensor mounting positions and axes | unknown | Mechanical assembly and measured offsets |
| Final power distribution and current budget | unknown | Battery/regulator ratings and measured startup/runtime load |

Known software inputs from the current task, retained without converting them
into physical verification:

- JGB37-520 nominal motor supply range: 6-12 V.
- User-reported motor values: 0.36 A no-load, 3.2 A stall, 330 rpm no-load
  output speed, and 30:1 nominal reduction.
- User-provided encoder figures: 11 PPR motor side, nominal 30:1 gearbox,
  330 A cycles per output revolution, and x4 count of 1320 counts/output
  revolution. The user defines 11 A cycles and 11 B cycles per motor revolution.
- Motor wire colours: red Motor+, white Motor-.
- Encoder wire colours: blue VCC, black GND, yellow A, green B.
- Encoder VCC range is user-reported as 3.3-5 V and output high follows VCC;
  push-pull versus open-drain topology remains unknown.
- Seller images document the exact advertised pack as Li-ion, 11.1 V nominal,
  7800 mAh, 5C, 12.6 V fully charged, 70 x 55 x 23 mm, and DC 5.5 x 2.5 mm
  male. The calculated nominal energy is 86.58 Wh and the advertised-rate
  calculation is 39 A; neither is measured, and 39 A is not a confirmed BMS
  continuous/peak rating.
- Seller images document a 12.6 V/1 A charger with 110-240 VAC 50/60 Hz input,
  DC 5.5 x 2.5 mm female connector, and 100 cm cable. Charge only while the
  battery is disconnected from the rover.

No hardware was connected, powered, flashed, or accessed while creating this
foundation.
