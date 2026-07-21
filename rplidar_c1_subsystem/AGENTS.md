# Historical Mirror Agent Guide

This directory is a tracked historical mirror of the LiDAR subsystem. It is not the authoritative working tree. Use the repository-root `AGENTS.md`, `README.md`, `HARDWARE_LOCK.md`, `PROJECT_SPEC.md`, and `docs/` for current implementation and hardware decisions.

Current inventory has exactly one physical SLAMTEC RPLIDAR C1M1-R2. Its only active physical ID is `c1_1`; any `c1_2` references in this mirror are historical or synthetic compatibility data and must not be treated as a second device. Do not claim physical C1 acceptance, dual-C1 operation, WiFi, rover integration, or sensor validation from this mirror.

Current Phase 3.2F status is recorded at repository root: A's isolated TCRT5000 evidence verifies only the isolated build/flash, PC4/PC5 signal connections, labelled 3.3 V/common-GND connections, live raw/debounced response, four sanitized 100-frame captures, and exact 50 ms steady-state timestamps. Voltage measurements, polarity semantics, black/white/drop classification, Hall behavior, shared buses, and full-rover operation remain UNVERIFIED.

Do not edit this mirror to create a competing implementation. Changes to current code, evidence, tests, or hardware guidance belong in the repository root.
