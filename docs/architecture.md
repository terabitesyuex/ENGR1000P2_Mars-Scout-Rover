# Architecture

The rover architecture separates hardware access, transport, data models, algorithms, visualization, recording, and replay. Phase 2.4 is PC-side recording and replay only.

## Sensor Layer

Ranging:

- RPLIDAR C1 x2, neutral IDs `c1_1` and `c1_2`.
- HC-SR04 x3, neutral IDs `ultrasonic_1`, `ultrasonic_2`, `ultrasonic_3`.

Motion and pose:

- Four wheel encoders.
- MPU6050 x1.

Ground and landmark:

- TCRT5000 x2 for edge/drop detection.
- Hall sensor module x1 for magnetic landmark/checkpoint detection.

Environment:

- BH1750 x1 for illuminance in lux.
- BMP280 x1 for temperature and atmospheric pressure.

## Planned Data Paths

```text
RPLIDAR C1
    -> ESP32 -> WiFi -> PC visualization/recording

STM32 sensors and rover state
    -> ESP32 -> WiFi -> PC

HC-SR04 / TCRT5000 / relevant local state
    -> STM32 safety decision -> motor control -> rover motion

rover motion
    -> encoders / MPU6050 / sensors -> STM32 -> ESP32 -> PC
```

The ESP32 -> WiFi -> PC path is the current communication plan. Bluetooth is only a superseded early concept if it appears in historical material.

## Responsibility Split

STM32 planned responsibilities:

- Existing four-mecanum-wheel motor control.
- Wheel encoder acquisition.
- Low-level motor safety.
- Command-timeout stop.
- MPU6050 acquisition.
- HC-SR04 acquisition.
- TCRT5000 edge/drop detection.
- Hall landmark detection.
- BH1750 and BMP280 acquisition unless interface tests require a different assignment.
- Low-rate sensor preprocessing.
- Basic odometry support.
- Local stop/turn obstacle-avoidance state machine.

ESP32 planned responsibilities:

- WiFi communication with the PC.
- Receive STM32 rover and sensor information.
- Package and transmit data.
- Receive limited configuration/control messages.
- Interface with at least one RPLIDAR C1 in a later phase.

PC responsibilities:

- Real-time polar visualization.
- Real-time Cartesian visualization.
- Recording.
- Replay.
- Experiment inspection.
- Data and figure export.
- Later short-range encoder/IMU-assisted accumulated 2D mapping.

## Current Software Layers

```text
Synthetic LiDAR source
    -> ScanFrame data model
    -> scan builder / coordinate transforms
    -> visualization
    -> Phase 2.4 JSONL recorder
    -> lazy replay
    -> replay visualization
```

The Phase 2.4 JSONL recording format is a PC-side reproducibility format. It is not the future on-wire ESP32 protocol.

## Two-C1 Policy

- Two C1 units are available.
- Phase 2.5 must test both independently.
- One stable C1 is the baseline integration target.
- Simultaneous dual-C1 operation is optional and remains UNVERIFIED until UART, GPIO, bandwidth, buffering, timing, and power feasibility are measured.
- Final exact LiDAR-derived avoidance ownership is not yet locked.

## Current Phase Scope

Phase 2.4 implements deterministic multi-sensor recording and replay using synthetic data. It does not open serial ports, command a C1, parse C1 packets, use WiFi sockets, run firmware, implement mapping, implement SLAM, implement odometry, or implement obstacle avoidance.

Emergency stopping remains a local STM32 safety responsibility in the plan. PC mapping occurs later and is short-range accumulated mapping, not a required reusable global SLAM map. ROS is not required.
