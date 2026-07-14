# Troubleshooting

## No Power Or Motor Does Not Start

- Confirm the LiDAR red wire is on a regulated 5 V supply, not ESP32 3.3 V.
- Confirm the supply can provide at least 1 A during startup.
- Confirm common ground between supply, LiDAR, and ESP32 or USB adapter.
- Confirm scan has been commanded; the C1M1-R2 does not use an external motor PWM wire.

## Serial Port Opens But No Data Arrives

- Confirm yellow LiDAR TX goes to receiver input.
- Confirm green LiDAR RX goes to transmitter output.
- Confirm baud rate is 460800.
- Confirm UART format is 8N1.
- Confirm the USB adapter and ESP32 are not both driving LiDAR RX.

## Data Looks Corrupt

- Check ground continuity.
- Shorten UART wires.
- Move motor power wiring away from UART wiring.
- Confirm supply ripple is below 150 mV.
- Confirm the parser is using the official SLAMTEC packet format for the selected scan mode.

## PC-Direct Port Remains Locked

- Close the official SDK probe cleanly.
- Unplug and reconnect the USB adapter if the operating system still holds the port.
- Confirm no terminal program is connected to the same port.

## Current Audit Phase Specific

Current Phase 1 has no live LiDAR communication. Any error involving serial ports is outside the current implementation.
