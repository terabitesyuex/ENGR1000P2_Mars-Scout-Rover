# LiDAR Protocol Notes

Official SLAMTEC RPLIDAR protocol documentation is the source of truth for all C1 packet layouts, command bytes, checksums, response descriptors, and scan data formats.

## Current Phase 2.5 Rule

Phase 2.5 implements a bounded PC-direct software parser for standard 5-byte scan nodes and a driver boundary that converts native C1 angles before `ScanPoint` creation. Automated driver tests use fixture bytes only. Separately committed evidence marks physical PC-direct acquisition for the one `c1_1` MANUAL_EVIDENCE_VERIFIED, while electrical, vendor-health, clean-packet-rate, timing, and accuracy acceptance remain UNVERIFIED.

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
- standard scan-node parsing path, physically exercised with raw quality-zero and above-profile-range points retained for follow-up filtering analysis.

Device information, health information, reset behavior, and additional scan modes remain future manual hardware validation items until documented.

## Parser Requirements

The PC-side parser must be incremental. It must accept arbitrary byte chunks, recover from response-descriptor prefixes, validate sample invariants, and never assume that a read returns a complete packet. Embedded ESP32 parsing remains a future phase.
