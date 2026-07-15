# PC-Direct Verification

PC-direct verification is planned for Phase 2.5. Phase 2.4 does not open serial ports or communicate with live LiDAR hardware.

Both physical RPLIDAR C1 units must be tested independently:

- `c1_1`
- `c1_2`

Future hardware path:

```text
RPLIDAR C1 -> original XH2.54 cable -> supplied USB adapter -> PC
```

Future Phase 2.5 steps for each unit:

1. Confirm supply voltage, polarity, connector orientation, and common ground.
2. List serial ports.
3. Open the selected port at 460800 baud.
4. Use the official SLAMTEC SDK or compatible software.
5. Read device information.
6. Read firmware and hardware information.
7. Record only a redacted serial identifier.
8. Read health state.
9. List supported scan modes if available.
10. Start scanning.
11. Count samples and completed rotations.
12. Print scan frequency.
13. Save one full scan.
14. Check distance and orientation against known references.
15. Stop scanning.
16. Disconnect cleanly.

One stable C1 is the baseline integration target. Simultaneous dual-C1 operation remains optional and UNVERIFIED until later feasibility tests.
