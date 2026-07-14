# LiDAR Protocol Notes

Official SLAMTEC RPLIDAR protocol documentation is the source of truth for all C1 packet layouts, command bytes, checksums, response descriptors, and scan data formats.

## Phase 0 Rule

The final C1 binary protocol parser is not implemented in Phase 0. This file records constraints only.

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

Later phases must begin with the minimum reliable subset:

- stop;
- reset;
- device information;
- health information;
- start scan;
- stop scan;
- one verified scan mode.

## Parser Requirements

The ESP32 parser must be incremental and non-blocking. It must accept arbitrary byte chunks, recover from random prefix bytes, validate every length field, and never assume that a serial read returns a complete packet.
