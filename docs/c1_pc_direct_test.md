# C1 PC-Direct Test Plan

Phase 2.5 adds the PC-side software boundary for direct RPLIDAR C1 acquisition. Automated tests use mocked byte streams. They do not open serial ports and do not prove the physical unit works.

## Scope

Implemented in Phase 2.5:

- PC-side C1 driver abstraction.
- Transport-injected `connect()`, `disconnect()`, `start_scan()`, and `iter_scan_points()` interface.
- Incremental standard scan-node parser for mocked and future PC-direct byte streams.
- Native C1 clockwise angle conversion before `ScanPoint` creation.
- Bounded capture of one C1 session into the existing Phase 2.4 JSONL recording format.
- CLI command `capture-c1`.
- Replay and visualization compatibility through existing Phase 2.4/2.3 tooling.

Not implemented:

- STM32 integration.
- ESP32 communication.
- WiFi.
- ROS.
- SLAM.
- Navigation.
- Obstacle avoidance.
- Dual-C1 simultaneous operation (NOT CURRENT SCOPE).
- Automated access to real serial ports.

## Hardware Assumptions

CONFIRMED:

- Exactly one RPLIDAR C1M1-R2 is available; its current neutral ID is `c1_1`.
- Verified C1 UART value is 460800 baud, 8N1, 3.3 V TTL.
- Verified C1 supply range is 4.8 V to 5.2 V.
- Verified C1 wire functions are preserved in `HARDWARE_LOCK.md`.

PLANNED:

- Test `c1_1` by PC-direct methods as the sole Phase 2.5 physical acceptance target.
- Use captured `ScanFrame` data with existing recording, replay, and visualization tools.

UNVERIFIED:

- C1 serial ID.
- C1 hardware revision.
- Operational status of the physical C1.
- Final mounting position or orientation.
- Any future second-C1 operation.
- Any COM port name.
- Any ESP32 GPIO or UART assignment.

## Driver Boundary

`C1PcDirectDriver` consumes a byte transport implementing:

- `connect()`
- `disconnect()`
- `write(payload: bytes)`
- `read(size: int) -> bytes`

The driver exposes:

- `connect()`
- `disconnect()`
- `start_scan()`
- `iter_scan_points()`
- `capture_scan_frame()`

Hardware access is isolated in `PySerialByteTransport`, which requires an explicit user-provided port. Automated tests and verification use `BytesBufferTransport`.

## Manual Hardware Procedure

Do not run this until wiring safety checks are complete.

1. Pick one physical C1 and label it temporarily as `c1_1`.
2. Verify supply voltage, polarity, connector orientation, and common ground.
3. Connect through the supplied PC-direct USB adapter.
4. Identify the actual serial port using a separate manual port-listing step.
5. Capture a bounded session:

```powershell
python -m rplidar_c1_tools.cli capture-c1 --sensor-id c1_1 --port <USER_VERIFIED_PORT> --frames 1 --points-per-frame 360 --output data\raw\c1_1_pc_direct.jsonl
```

6. Inspect and replay the recording:

```powershell
python -m rplidar_c1_tools.cli inspect-recording data\raw\c1_1_pc_direct.jsonl
python -m rplidar_c1_tools.cli replay-recording data\raw\c1_1_pc_direct.jsonl --sensor-id c1_1
```

7. Render the final frame:

```powershell
python -m rplidar_c1_tools.cli render-recording data\raw\c1_1_pc_direct.jsonl --sensor-id c1_1 --output-dir data\decoded\c1_1_pc_direct
```

8. Preserve the recording and evidence as the one-device `c1_1` acceptance record. Do not infer physical success from fixture output.

Do not connect a second C1 for Phase 2.5; dual-C1 work is NOT CURRENT SCOPE.

## Acceptance Evidence

Manual Phase 2.5 hardware evidence should include:

- Redacted device identity.
- Health state.
- Capture command used.
- JSONL recording path.
- Inspection summary.
- Replay output.
- Polar and point-cloud PNGs.
- Distance checks against known targets.
- Orientation checks against known geometry.
- Any dropped/corrupt sample observations.

Record hardware evidence in documentation only after the measurements are actually performed.
