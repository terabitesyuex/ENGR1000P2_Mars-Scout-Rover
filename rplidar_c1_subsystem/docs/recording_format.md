# SUPERSEDED HISTORICAL COPY

Use repository-root `docs/recording_format.md` for the current JSONL schema. Current hardware uses one physical C1 (`c1_1`); any `c1_2` stream below is historical or synthetic compatibility data.

# Recording Format

Recording is implemented in a later phase. This file defines the intended session layout.

## Session Directory

```text
data/raw/YYYY-MM-DD_HHMMSS/
    metadata.json
    wire_stream.bin
    samples.csv
    scans.jsonl
    events.jsonl
```

## Metadata

`metadata.json` must contain:

- recording version;
- date and time;
- LiDAR model;
- firmware version;
- hardware revision;
- redacted serial identifier;
- ESP32 firmware version;
- transport configuration;
- filter configuration;
- coordinate convention;
- map configuration.

## Files

- `wire_stream.bin`: exact ESP32-to-PC binary frames.
- `samples.csv`: decoded samples for inspection.
- `scans.jsonl`: completed scans.
- `events.jsonl`: connection, disconnection, scan start, scan stop, health changes, parser errors, timeouts, recovery attempts, and configuration changes.

The recorder must create directories safely, preserve partial recordings, flush periodically, close cleanly on Ctrl+C, and never overwrite an existing session accidentally.
