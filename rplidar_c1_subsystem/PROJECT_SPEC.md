# Project Specification

This document defines the scope and acceptance criteria for the Mars Scout Rover RPLIDAR C1 subsystem. The project uses the SLAMTEC RPLIDAR C1M1-R2 and must remain maintainable, independently testable, and safe for beginner integration work.

## Required Functions

- PC-direct verification through the supplied USB adapter.
- ESP32-C3 communication with the RPLIDAR C1M1-R2.
- Device information query.
- Device health query.
- Scan-mode discovery where supported.
- Start, stop, reset, and bounded recovery.
- Incremental binary protocol parsing.
- Full-scan assembly.
- Range and quality filtering.
- Local obstacle-distance extraction.
- ESP32-to-PC framed binary data transmission.
- Real-time polar and Cartesian visualization.
- Raw and decoded data recording.
- Offline deterministic replay.
- Static occupancy-grid mapping with the LiDAR fixed.
- Diagnostics and fault recovery.
- Synthetic data generation and unit tests.

## Optional Functions

- Scan frequency adjustment when supported by official SLAMTEC commands.
- High-speed or capsule scan decoding after basic scan mode is verified.
- CSV debug mode for low-rate inspection.
- Screenshot export from visualization views.

## Excluded Functions

- STM32 communication.
- Motor commands for the rover.
- Wheel encoders.
- TCRT5000 sensors.
- Hall sensor.
- MPU6050.
- BMP280.
- BH1750.
- Moving-rover mapping.
- Global localization.
- Autonomous navigation.
- Full SLAM.
- ROS as a required dependency.
- External LiDAR motor PWM control.

## Phase Acceptance Criteria

### Phase 0

- Repository skeleton exists.
- `HARDWARE_LOCK.md` contains C1M1-R2.
- Verified electrical values are documented.
- GPIO values remain explicit user-configurable settings.
- No live LiDAR communication is implemented.

### Phase 1

- Official USB adapter works.
- Device information is read.
- Health is valid.
- Scanning starts.
- Points are received.
- One full scan is saved.
- Scanning stops cleanly.

### Phase 2

- Synthetic polar view works.
- Synthetic Cartesian view works.
- Coordinate orientation is correct.
- No hardware is required.

### Phase 3

- ESP32 UART operates at 460800 baud.
- Device information is read.
- Health is read.
- Start and stop commands work.
- No blocking receive loop exists.

### Phase 4

- Valid samples are decoded.
- Scan boundaries are detected.
- Parser recovers from injected corruption.
- No unbounded memory growth occurs.

### Phase 5

- Batched binary frames reach the PC.
- CRC is verified.
- Sequence gaps are detected.
- Live full scans are displayed.

### Phase 6

- Polar and Cartesian views are smooth.
- Display refresh is bounded.
- Scan statistics are visible.

### Phase 7

- Live data can be recorded.
- Recording can be replayed.
- Replay reproduces the same scan geometry.

### Phase 8

- Synthetic room produces four walls.
- Fixed real LiDAR produces a recognizable room outline.
- Free and occupied cells are distinguishable.
- Map can be saved and loaded.

### Phase 9

- Continuous scan runs for at least 30 minutes.
- No crash.
- No unbounded memory growth.
- No persistent parser loss after corrupt data.
- Temporary USB interruption is reported.
- Recovery behavior is documented.

## Final Demonstration Procedure

1. Show the hardware lock and wiring checklist.
2. Run the PC-direct adapter test and capture device information and health.
3. Run the ESP32 firmware, identify the LiDAR, and start scanning.
4. Display live polar and Cartesian scans.
5. Record a session and stop scanning cleanly.
6. Replay the same session deterministically.
7. Generate a static occupancy grid with the LiDAR fixed.
8. Demonstrate fault diagnostics with a controlled interruption.

## Phase 0 Test Method

Phase 0 is verified by checking the file tree, reviewing the unresolved hardware values in `HARDWARE_LOCK.md`, and running the PC-side unit tests:

```powershell
cd rplidar_c1_subsystem
pip install -e .\\pc
pytest .\\pc\\tests
```
