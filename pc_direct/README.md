# PC-Direct Verification

Phase 2.5 adds a PC-side software capture boundary for a single RPLIDAR C1 stream. Automated verification uses fixture bytes only; real hardware must be tested manually with an explicit user-verified serial port.

Both physical RPLIDAR C1 units must be tested independently:

- `c1_1`
- `c1_2`

Planned hardware path:

```text
RPLIDAR C1 -> original XH2.54 cable -> supplied USB adapter -> PC
```

Manual Phase 2.5 steps for each unit:

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

Manual capture command template:

```powershell
python -m rplidar_c1_tools.cli capture-c1 --sensor-id c1_1 --port <USER_VERIFIED_PORT> --frames 1 --points-per-frame 360 --output .verification\phase2.5\c1_1_pc_direct.jsonl
```

Fixture-only smoke command:

```powershell
python -m rplidar_c1_tools.cli capture-c1 --sensor-id c1_1 --sample-hex 3d0100a00f3e012da00f3e015aa00f3e0187a00f --frames 1 --points-per-frame 4 --read-chunk-size 5 --output .verification\phase2.5\c1_1_fixture.jsonl --overwrite
```

One stable C1 is the baseline integration target. Simultaneous dual-C1 operation remains optional and UNVERIFIED until later feasibility tests.
