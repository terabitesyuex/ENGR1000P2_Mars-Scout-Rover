# SUPERSEDED HISTORICAL COPY

Use repository-root `docs/wiring.md` for current wiring guidance. This mirror is historical and must not be used to infer a second C1, current GPIOs, current sensor voltages, or Phase 3.2F completion.

# Wiring

Electrical safety is the first project priority. Do not connect the LiDAR until the wiring checklist is complete.

## Confirmed Wire Functions

| LiDAR wire | Function | Destination |
| --- | --- | --- |
| Red | VCC, 5 V | Independent regulated 5 V supply |
| Yellow | LiDAR TX | ESP32 UART RX |
| Green | LiDAR RX | ESP32 UART TX |
| Black | GND | ESP32 GND and supply ground |
| Fifth position | Unused | Leave unused |

## ESP32 Connection Rules

- LiDAR yellow TX goes to ESP32 UART RX.
- LiDAR green RX goes to ESP32 UART TX.
- LiDAR black GND goes to ESP32 GND.
- LiDAR red VCC goes to an independent regulated 5 V supply.
- ESP32 and LiDAR grounds must be connected.
- Never connect LiDAR TX to ESP32 TX.
- Never connect LiDAR RX to ESP32 RX.
- Never connect the LiDAR red wire to ESP32 3.3 V.

## Power Rules

- Use a regulated 5 V supply capable of at least 1 A.
- Keep supply voltage between 4.8 V and 5.2 V.
- Keep supply ripple below 150 mV.
- Use short power wires.
- Keep motor power wiring away from LiDAR UART wiring.
- Add local bulk decoupling near the LiDAR connector if required.

## Harness Rules

- Do not cut the original cable.
- Use a non-destructive XH2.54-5P breakout or adapter harness.
- Do not simultaneously drive LiDAR RX from the supplied USB adapter and the ESP32.
- Label each connection before applying power.

## GPIO Status

GPIO values are not selected in Phase 0. GPIO20 as ESP32 RX and GPIO21 as ESP32 TX are only candidates after the ESP32-C3 SuperMini board silkscreen and board documentation confirm availability.
