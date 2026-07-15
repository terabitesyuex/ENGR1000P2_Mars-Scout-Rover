# RPLIDAR C1 PC Tools

PC-side package for synthetic scans, coordinate transforms, visualization, Phase 2.4 multi-sensor recording, deterministic replay, and later mapping work.

Phase 2.4 uses synthetic data only. It does not open serial ports, use WiFi sockets, access hardware, run firmware, implement mapping, implement SLAM, or implement obstacle avoidance.

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

## Data Location

Generated development artifacts belong under `.verification/`, which is ignored by Git. Do not commit generated recordings or figures unless a future task explicitly asks for a curated fixture.

## Tests

```powershell
pc\.venv\Scripts\python.exe -m pytest pc\tests\test_recording.py pc\tests\test_replay.py pc\tests\test_current_plan.py -v
pc\.venv\Scripts\python.exe -m pytest pc\tests -v
```

Phase verifier:

```powershell
.\tools\verify_phase.cmd phase2.4 -AllowDirty
```
