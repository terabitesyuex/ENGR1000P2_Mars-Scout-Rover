# Hardware Information TODO

This table is the single unresolved-hardware checklist for the unified
OpenRF1 rover-control application. unknown means no mapping may be encoded in
firmware. unverified means a proposed or module-level fact still needs
authoritative board evidence or controlled physical validation.

| Item | Status | Information needed |
|---|---|---|
| Four motor connector pinouts | unknown | OpenRF1 schematic and vendor connector definition |
| Motor connector to logical wheel mapping | unknown | Chassis wiring trace and controlled wheel-on-blocks test |
| Motor PWM GPIO | unknown | OpenRF1 schematic |
| Motor PWM timer and channel | unknown | MCU mapping and timer resource table |
| Motor direction GPIO or driver command scheme | unknown | Motor-driver part number and OpenRF1 schematic |
| Motor enable and brake/coast behavior | unknown | Motor-driver datasheet and board schematic |
| Motor PWM frequency and polarity | unknown | Motor-driver requirements and vendor firmware reference |
| Motor command sign per wheel | unknown | Verified wheel mounting and controlled wheel-on-blocks test |
| Encoder connector pinouts | unknown | OpenRF1 schematic and connector definition |
| Encoder A GPIO for all four wheels | unknown | OpenRF1 schematic |
| Encoder B GPIO for all four wheels | unknown | OpenRF1 schematic |
| Encoder timer/EXTI resources | unknown | MCU mapping and resource conflict review |
| Encoder electrical input levels and pull configuration | unknown | Encoder output specification and board input circuit |
| Encoder sign per logical wheel | unknown | Verified wheel mounting and controlled rotation test |
| Encoder 11 PPR interpretation | unverified | Motor vendor datasheet: cycles versus edges |
| 30:1 gearbox ratio tolerance | unverified | JGB37-520 exact purchased variant datasheet |
| 1320 counts/output revolution | unverified | Controlled one-revolution count test after x4 decoding |
| Wheel radius | unknown | Loaded-wheel measurement in millimetres |
| Half wheelbase | unknown | Axle-centre measurement in millimetres |
| Half track width | unknown | Left/right wheel-centre measurement in millimetres |
| Maximum usable wheel speed | unknown | Motor, supply, load, and encoder measurement |
| Mecanum roller orientation and wheel placement | unknown | Wheel markings, chassis assembly record, and motion test |
| Battery voltage/current telemetry ADC path | unknown | OpenRF1 schematic and divider/current-sense definition |
| RPLIDAR C1 STM32 UART and pins | unknown | OpenRF1 connector-to-MCU mapping and resource review |
| ESP32 STM32 UART and pins | unknown | OpenRF1 connector-to-MCU mapping and resource review |
| ESP32-C3 SuperMini selected pins | unverified | Exact module revision and integration wiring |
| Two additional HC-SR04 paths | unknown | GPIO/timer/connectors and one divider per ECHO path |
| Shared MPU6050/BMP280/BH1750 I2C concurrency | unverified | Combined-bus firmware and physical validation |
| Final sensor mounting positions and axes | unknown | Mechanical assembly and measured offsets |
| Final power distribution and current budget | unknown | Battery/regulator ratings and measured startup/runtime load |

Known software inputs from the current task, retained without converting them
into physical verification:

- JGB37-520 nominal motor supply range: 6-12 V.
- User-provided encoder figures: 11 PPR motor side, nominal 30:1 gearbox,
  330 PPR output side, proposed x4 count of 1320 counts/output revolution.
- Motor wire colours: red Motor+, white Motor-.
- Encoder wire colours: blue VCC, black GND, yellow A, green B.

No hardware was connected, powered, flashed, or accessed while creating this
foundation.
