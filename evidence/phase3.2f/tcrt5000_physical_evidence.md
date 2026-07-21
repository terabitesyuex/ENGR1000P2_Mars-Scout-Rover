# Phase 3.2F Isolated TCRT5000 Physical Evidence

## Scope

This evidence records A's isolated bench bring-up of the two available TCRT5000 modules with the OpenRF1 ground-sensor-only firmware. It is not full-rover validation and does not validate the Hall sensor, other sensors, motors, ESP32/WiFi, or LiDAR integration.

The current inventory contains exactly one physical RPLIDAR C1M1-R2. Its neutral ID is `c1_1`; its physical acceptance remains UNVERIFIED. No second physical C1 or dual-C1 result is claimed here.

## Build And Flash Evidence

| Item | Recorded result | Status |
| --- | --- | --- |
| Keil target | `OpenRF1_GroundSensors_Bringup` | MANUAL_EVIDENCE_VERIFIED |
| Build diagnostics | 0 errors, 0 warnings | MANUAL_EVIDENCE_VERIFIED |
| Program size | Code 12000, RO-data 2776, RW-data 4, ZI-data 3176 bytes | MANUAL_EVIDENCE_VERIFIED |
| HEX SHA-256 | `999B678986655A2F913EEA643CA1A21EEC0C5CE0C883E4E9A55F5BF9C605FCB5` | MANUAL_EVIDENCE_VERIFIED |
| Flash result | Full erase, approximately 14 KB written, then execution from `0x08000000` | MANUAL_EVIDENCE_VERIFIED |

The programming log's MCU unique identifier and the operator's local port/path details are intentionally not tracked.

## Wiring And Telemetry Evidence

| Item | Recorded result | Status |
| --- | --- | --- |
| `tcrt5000_1` signal | OUT connected to signal 1 / X1 / PC4 | MANUAL_EVIDENCE_VERIFIED |
| `tcrt5000_2` signal | OUT connected to signal 2 / X2 / PC5 | MANUAL_EVIDENCE_VERIFIED |
| Module supply connection | Both modules connected to the labelled STM32 3.3 V supply and common GND | MANUAL_EVIDENCE_VERIFIED connection only; voltage not measured |
| Identity telemetry | Protocol version 1, `sensor_id=ground_sensors`, X1/PC4, X2/PC5, X3/PB0, X4 unused, 5 ms sample, 4 samples / 20 ms debounce, 50 ms telemetry | MANUAL_EVIDENCE_VERIFIED |
| Serial framing | JSONL telemetry was received; an initial partial line can occur when capture begins in the middle of a frame | MANUAL_EVIDENCE_VERIFIED |

The firmware intentionally preserves numeric `raw_level` and `debounced_level`. It does not assign semantic meaning to 0 or 1.

## Sanitized Captures

The four 100-frame captures contain no sequence gaps. Each steady-state capture spans 4950 ms with exact 50 ms timestamp increments.

| Capture | Observed channel state | SHA-256 |
| --- | --- | --- |
| `tcrt5000_1_open_space.jsonl` | left raw/debounced = 0/0 | `3A51BE6E0D66F5089C7A05BF77E188706484967462552D814B2C0F4C04E3D23E` |
| `tcrt5000_1_white_surface.jsonl` | left raw/debounced = 1/1 | `8EEBC9DA5ACC887F496DEE6C279B31A5B3309422AFF303E53AF74CE3CF12255C` |
| `tcrt5000_2_open_space.jsonl` | right raw/debounced = 0/0 | `402AD39E824B9CBC5FD97D770FD72E81C8577CB27278EC22F628832C336F6D87` |
| `tcrt5000_2_white_surface.jsonl` | right raw/debounced = 1/1 | `DBB584BB886EBF647182D419D8C931E87363EC58CE8EF2DF0B920D13FC5710AA` |

These captures verify repeatable digital response only for the tested open-space and reflective-surface geometry. During informal observation, both black and white targets could light the module indicator at a suitable distance, while too near or too far could extinguish it. Therefore colour classification and a reliable physical detection window are not established.

## Verified Boundary

The following items are MANUAL_EVIDENCE_VERIFIED for isolated bring-up only:

- successful build, flash, and execution of the ground-sensor-only firmware;
- installed PC4 and PC5 TCRT signal connections and labelled 3.3 V/common-GND connections;
- both TCRT channels producing live raw and debounced state changes;
- the four sanitized 100-frame captures with no sequence gaps;
- exact 50 ms steady-state telemetry timing in those captures.

## Still Unverified

The following items remain UNVERIFIED:

- Actual 3.3 V rail voltage and each TCRT output high/low voltage.
- TCRT output topology and electrical margins.
- Active polarity and semantic meaning of raw level 0 or 1.
- Black/white classification, calibrated reflectance threshold, reliable distance window, and drop/edge safety performance.
- Startup-frame timing, long-duration timing, real-world debounce suitability, final mounting, ambient-light robustness, and motor-vibration performance.
- Hall sensor wiring, divider values, voltages, polarity, magnetic response, and landmark behavior.
- Shared-I2C, complete multisensor firmware, complete rover operation, ESP32/WiFi, the single C1's physical acceptance, encoder/IMU fusion, odometry accuracy, mapping, and autonomous behavior.

No additional TCRT5000 hardware test is required for this evidence-only PR. The voltage and Hall checks remain separate future manual actions.
