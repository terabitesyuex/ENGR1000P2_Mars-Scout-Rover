# SUPERSEDED HISTORICAL COPY

Use repository-root `docs/architecture.md` for the current Phase 2.4 architecture. Historical statements below may be stale.

# Architecture

The subsystem is split into independently testable layers. Live hardware is only one possible scan source.

## Layer Diagram

```text
RPLIDAR C1M1-R2
    |
    | 3.3 V TTL UART, 460800 baud
    v
ESP32-C3 firmware
    - command encoder
    - response parser
    - scan parser
    - scan assembler
    - filtering
    - obstacle sectors
    - framed PC transport
    |
    | framed binary packets
    v
PC tools
    - packet decoder
    - scan builder
    - visualization
    - recorder
    - replay
    - stationary occupancy grid

Synthetic and replay sources feed the same PC scan interfaces.
```

## Module Responsibilities

- `firmware/src/lidar`: LiDAR commands, parser state machines, scan assembly, and device statistics.
- `firmware/src/processing`: filtering, coordinate conversion, and local obstacle sectors.
- `firmware/src/transport`: ESP32-to-PC binary frame encoding and CRC.
- `firmware/src/diagnostics`: health monitoring, runtime counters, and rate-limited status.
- `pc/src/rplidar_c1_tools`: PC configuration, data models, synthetic data, replay, visualization, recording, and mapping.
- `pc_direct`: Phase 1 official-SDK probe used only for direct PC verification.

## Boundaries

- Firmware must not depend on desktop SDK classes.
- PC visualization must not know whether scans came from live ESP32 frames, replay, CSV, or synthetic generation.
- Raw measurements must be preserved in recordings.
- Filtered validity must be stored separately from protocol validity.
- Debug text must not be mixed with normal binary frame transport.

## Phase 0 Scope

Phase 0 creates structure and documentation plus a deterministic Python synthetic scan interface. No live serial ports are opened, no C1 command bytes are emitted, and no binary C1 parser is implemented.
