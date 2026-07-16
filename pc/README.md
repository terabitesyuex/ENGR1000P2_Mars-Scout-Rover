# RPLIDAR C1 PC Tools

PC-side package for synthetic scans, coordinate transforms, visualization, Phase 2.4 multi-sensor recording, deterministic replay, Phase 2.5 PC-direct C1 capture, Phase 3.1 STM32 telemetry simulation/parsing/recording bridge, Phase 3.2A OpenRF1 BH1750 mocked serial capture, Phase 3.2B multisensor/link fixtures, and later mapping work.

Phase 2.5 automated tests use mocked C1 byte streams only. Manual PC-direct capture can use an explicit user-verified port, but this package does not invent ports, access STM32/ESP32 firmware, use WiFi sockets, implement mapping, implement SLAM, or implement obstacle avoidance.

Phase 3.1 STM32 telemetry tools use deterministic files and in-memory streams only. They do not open serial ports, GPIO, I2C, USB devices, timers, or network sockets.

Phase 3.2A capture tools use file-backed mock input in automated tests. Manual live capture requires an explicit user-selected CH340 COM port; no COM port is guessed.

Phase 3.2B tools use deterministic fixtures and pure codecs only. They do not open USART2, USART3, real COM ports, USB devices, WiFi sockets, GPIO, I2C, flashing tools, or sensors.

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

## STM32 Sensor Telemetry

```powershell
python -m rplidar_c1_tools.cli simulate-stm32-sensors --cycles 5 --scenario nominal --output .verification\phase3.1\synthetic_stm32_telemetry.jsonl --overwrite
python -m rplidar_c1_tools.cli inspect-stm32-telemetry --input .verification\phase3.1\synthetic_stm32_telemetry.jsonl --output .verification\phase3.1\telemetry_inspection.txt
python -m rplidar_c1_tools.cli record-stm32-telemetry --input .verification\phase3.1\synthetic_stm32_telemetry.jsonl --output .verification\phase3.1\converted_multisensor_recording.jsonl --overwrite
```

Protocol: `mars_scout_stm32_sensor_telemetry` version `1`.

Supported scenarios: `nominal`, `ultrasonic_timeout`, `ground_polarity_unverified`, `hall_polarity_unverified`, `environment_change`, and `mixed_faults`.

## OpenRF1 BH1750 Serial Capture

Generate BH1750-only mock telemetry:

```powershell
python -m rplidar_c1_tools simulate-bh1750-telemetry --samples 5 --output .verification\phase3.2a\mocked_bh1750_source.jsonl --overwrite
```

Capture through the mocked serial path and convert to a Phase 2.4 recording:

```powershell
python -m rplidar_c1_tools capture-stm32-serial --mock-input .verification\phase3.2a\mocked_bh1750_source.jsonl --max-messages 5 --telemetry-output .verification\phase3.2a\mocked_bh1750_telemetry.jsonl --recording-output .verification\phase3.2a\mocked_bh1750_recording.jsonl --overwrite
```

Manual live capture requires a user-verified port:

```powershell
python -m rplidar_c1_tools capture-stm32-serial --port <USER_VERIFIED_COM_PORT> --baud 115200 --duration 30 --telemetry-output bh1750_telemetry.jsonl --recording-output bh1750_recording.jsonl --overwrite
```

If pyserial is unavailable for manual live capture, install it only in the repository virtual environment:

```powershell
pc\.venv\Scripts\python.exe -m pip install pyserial
```

## Phase 3.2B Full-Hardware Fixtures

```powershell
python -m rplidar_c1_tools.cli simulate-stm32-sensors --cycles 2 --scenario phase32b_full_foundation --output .verification\phase3.2b\phase32b_full_telemetry.jsonl --overwrite
python -m rplidar_c1_tools.cli record-stm32-telemetry --input .verification\phase3.2b\phase32b_full_telemetry.jsonl --output .verification\phase3.2b\phase32b_full_recording.jsonl --overwrite
python -m rplidar_c1_tools.cli inspect-recording .verification\phase3.2b\phase32b_full_recording.jsonl --output .verification\phase3.2b\phase32b_recording_inspection.txt
```

The fixture includes `imu_raw`, `subsystem_status`, `link_status`, and `lidar_transport_stats`. These records are software diagnostics, not physical sensor evidence.

## Data Location

Generated development artifacts belong under `.verification/`, which is ignored by Git. Do not commit generated recordings or figures unless a future task explicitly asks for a curated fixture.

## Tests

```powershell
pc\.venv\Scripts\python.exe -m pytest pc\tests\test_recording.py pc\tests\test_replay.py pc\tests\test_current_plan.py -v
pc\.venv\Scripts\python.exe -m pytest pc\tests\test_stm32_sensor_models.py pc\tests\test_stm32_sensor_protocol.py pc\tests\test_stm32_sensor_simulator.py pc\tests\test_stm32_recording_bridge.py pc\tests\test_stm32_sensor_cli.py pc\tests\test_phase3_current_plan.py -v
pc\.venv\Scripts\python.exe -m pytest pc\tests\test_openrf1_bh1750.py pc\tests\test_openrf1_firmware_foundation.py pc\tests\test_stm32_serial_capture.py -v
pc\.venv\Scripts\python.exe -m pytest pc\tests -v
```

Phase verifier:

```powershell
.\tools\verify_phase.cmd phase2.5 -AllowDirty
.\tools\verify_phase.cmd phase3.1 -AllowDirty
.\tools\verify_phase.cmd phase3.2a -AllowDirty
```
