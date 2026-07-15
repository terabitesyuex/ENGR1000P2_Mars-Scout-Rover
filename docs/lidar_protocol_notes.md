# LiDAR Protocol Notes

Official SLAMTEC RPLIDAR protocol documentation is the source of truth for all C1 packet layouts, command bytes, checksums, response descriptors, and scan data formats.

## Current Phase 2.5 Rule

Phase 2.5 implements a bounded PC-direct software parser for standard 5-byte scan nodes and a driver boundary that converts native C1 angles before `ScanPoint` creation. Automated tests use fixture bytes only and do not prove either physical C1 unit operates.

The parser is intentionally separated from serial hardware access and recording. Future protocol extensions such as high-speed or capsule scan modes must be added as separate parser paths with tests.

## Required Distinctions

The implementation must distinguish:

- command packets sent to the LiDAR;
- command-response descriptors;
- device information responses;
- health responses;
- scan responses;
- scan data packets;
- standard scan mode;
- high-speed or capsule scan modes;
- scan-boundary indicators;
- error responses.

## Initial Minimum Command Set

Phase 2.5 begins with the minimum reliable PC-direct subset:

- stop;
- start scan;
- standard scan-node parsing path, pending physical validation.

Device information, health information, reset behavior, and additional scan modes remain future manual hardware validation items until documented.

## Parser Requirements

The PC-side parser must be incremental. It must accept arbitrary byte chunks, recover from response-descriptor prefixes, validate sample invariants, and never assume that a read returns a complete packet. Embedded ESP32 parsing remains a future phase.
