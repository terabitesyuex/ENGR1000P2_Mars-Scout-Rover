# PC-Direct Verification

PC-direct verification will verify the RPLIDAR C1M1-R2 directly from the PC through the supplied USB-to-UART adapter before ESP32 live communication work. Current Phase 1 is audit and validation tooling only, so it does not open serial ports.

Hardware path:

```text
RPLIDAR C1M1-R2 -> original XH2.54 cable -> supplied USB adapter -> PC
```

Phase 1 probe requirements:

- list serial ports;
- open the selected port at 460800 baud;
- connect through the official SLAMTEC SDK or compatible software;
- read device information;
- read firmware and hardware information;
- read health state;
- list supported scan modes if available;
- start scanning;
- count samples and completed rotations;
- print scan frequency;
- save one full scan;
- stop scanning;
- disconnect cleanly.

No live PC-direct communication is implemented in current Phase 1.
