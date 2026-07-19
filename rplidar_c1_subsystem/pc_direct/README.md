# SUPERSEDED HISTORICAL COPY

This nested document is a superseded historical copy, not current PC-direct guidance. Use repository-root `pc_direct/README.md`; the current physical acceptance target is one `c1_1`. Any `c1_2` references here are HISTORICAL.

# PC-Direct Verification

Phase 1 verifies the RPLIDAR C1M1-R2 directly from the PC through the supplied USB-to-UART adapter before any ESP32 development.

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

No live PC-direct communication is implemented in Phase 0.
