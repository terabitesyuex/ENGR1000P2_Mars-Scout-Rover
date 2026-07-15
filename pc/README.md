# RPLIDAR C1 PC Tools

PC-side package for synthetic scans, coordinate transforms, visualization, Phase 2.4 multi-sensor recording, deterministic replay, Phase 2.5 PC-direct C1 capture, and later mapping work.

Phase 2.5 automated tests use mocked C1 byte streams only. Manual PC-direct capture can use an explicit user-verified port, but this package does not invent ports, access STM32/ESP32 firmware, use WiFi sockets, implement mapping, implement SLAM, or implement obstacle avoidance.

## Install For Development

```powershell
python -m pip install -e .\pc
```

## Synthetic Scan Output

```powershell
python -m rplidar_c1_tools.cli synthetic-room --scans 1
```

## Synthetic Visualization

```powershell
python -m rplidar_c1_tools.cli render-synthetic --scene both --output-dir .verification\phase2.3_visuals --no-show
```

## Multi-Sensor Recording

One-LiDAR synthetic session:

```powershell
python -m rplidar_c1_tools.cli record-synthetic --scene room --frames 2 --lidar-count 1 --output .verification\phase2.4\one_c1_room.jsonl
```

Two-LiDAR synthetic session with auxiliary streams:

```powershell
python -m rplidar_c1_tools.cli record-synthetic --scene room --frames 3 --lidar-count 2 --include-aux --output .verification\phase2.4\synthetic_multisensor_room.jsonl
```

Auxiliary synthetic streams include optional rover pose, MPU6050-style IMU samples, HC-SR04-style ultrasonic samples, TCRT5000 edge samples, Hall landmark samples, BH1750 illuminance samples, and BMP280 temperature/pressure samples. These are deterministic software fixtures, not hardware measurements.

## Inspection

```powershell
python -m rplidar_c1_tools.cli inspect-recording .verification\phase2.4\synthetic_multisensor_room.jsonl --output .verification\phase2.4\inspection.txt
```

## Replay

Immediate replay:

```powershell
python -m rplidar_c1_tools.cli replay-recording .verification\phase2.4\synthetic_multisensor_room.jsonl
```

Filter one C1:

```powershell
python -m rplidar_c1_tools.cli replay-recording .verification\phase2.4\synthetic_multisensor_room.jsonl --sensor-id c1_1
```

## Render From Replay

```powershell
python -m rplidar_c1_tools.cli render-recording .verification\phase2.4\synthetic_multisensor_room.jsonl --output-dir .verification\phase2.4
```

Expected output names include:

- `c1_1_last_polar.png`
- `c1_1_last_point_cloud.png`
- `c1_2_last_polar.png`
- `c1_2_last_point_cloud.png`

## PC-Direct C1 Capture

Manual capture requires a user-verified port:

```powershell
python -m rplidar_c1_tools.cli capture-c1 --sensor-id c1_1 --port <USER_VERIFIED_PORT> --frames 1 --points-per-frame 360 --output .verification\phase2.5\c1_1_pc_direct.jsonl
```

Automated smoke capture uses fixture bytes and opens no serial port:

```powershell
python -m rplidar_c1_tools.cli capture-c1 --sensor-id c1_1 --sample-hex 3d0100a00f3e012da00f3e015aa00f3e0187a00f --frames 1 --points-per-frame 4 --read-chunk-size 5 --output .verification\phase2.5\c1_1_fixture.jsonl --overwrite
```

The output is the same Phase 2.4 JSONL schema used by `inspect-recording`, `replay-recording`, and `render-recording`.

## Data Location

Generated development artifacts belong under `.verification/`, which is ignored by Git. Do not commit generated recordings or figures unless a future task explicitly asks for a curated fixture.

## Tests

```powershell
pc\.venv\Scripts\python.exe -m pytest pc\tests\test_recording.py pc\tests\test_replay.py pc\tests\test_current_plan.py -v
pc\.venv\Scripts\python.exe -m pytest pc\tests -v
```

Phase verifier:

```powershell
.\tools\verify_phase.cmd phase2.5 -AllowDirty
```
