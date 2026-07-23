# Vehicle Assembly And Mounting Evidence

Evidence date: 2026-07-23

This directory archives the user-supplied vehicle photographs, CAD screenshots,
and completed information request. The evidence confirms only what is visible
or explicitly reported. It does not prove continuity, rail voltage, connector
pin order, firmware operation, motor direction, sensor response, or safe motion.

## Archived Files

| File | SHA-256 | Evidence content |
| --- | --- | --- |
| `missing_information_responses.docx` | `FD4954180AE16CD45CA0ED9B50642BEF62AD84B1534065FA8E13EA7A34A5AD0C` | User responses for geometry, wheel positions, ultrasonic CAD poses, and remaining requests |
| `vehicle_top_front_marked.jpg` | `F10157F57A4CE185AA3163A34F64AB51257FDCC95B1D25709218AE52AE57E656` | Top view with vehicle front marked |
| `vehicle_front_ultrasonic.jpg` | `86E6C13F0E53F548249B5374517B8E3732FEF8B68879F0AAB7D9B15E9B422142` | Front view showing three HC-SR04 modules |
| `vehicle_front_right.jpg` | `78F22F3B9DF5121DD38F8A8C0D446E03FD5C86A49DBA3F346EC11254E0E4D3AA` | Front-right exterior view |
| `mpu6050_top_axis.jpg` | `721000FC0523687A08D506EAFAE613A3188F0243FFEDECD9F0534FB865FCDFFA` | Installed GY-521/MPU6050 top view with vehicle-front arrow |
| `mpu6050_underside_axis.jpg` | `C38CBBFD9936B3ECA04E324DF28AEE885A717D8704FE06B5B68BF0B0FA456069` | Underside view of the installed GY-521/MPU6050 with vehicle-front arrow |
| `cad_mount_offsets_view1.jpg` | `7D12E6D0C27D938F3A5DDF250499E9BFEE242D14B1D2BEA32D7B34858612F9FD` | CAD-screen mounting dimensions, first view |
| `cad_mount_offsets_view2.jpg` | `66ECC4CF6906EDBE6620049C7BF69E25A81A3C14AE27B374D54FA4BAB7B5DC73` | CAD-screen mounting dimensions, second view |

## Recorded Facts

The completed response document reports:

- loaded wheel diameter: `79 mm`;
- axle-centre wheelbase: `190 mm`;
- wheel-centre track width: `217 mm`;
- viewed from the rear, the upper-left, upper-right, lower-left, and lower-right
  motors correspond spatially to front-left, front-right, rear-left, and
  rear-right respectively;
- left/centre/right ultrasonic orientation angles: `-45 deg`, `0 deg`,
  `+45 deg`;
- left/centre/right ultrasonic CAD-coordinate tuples in millimetres:
  `(-42.45, 2.67, 132.23)`, `(0, 2.67, 148.33)`, and
  `(41.18, 2.67, 132.23)`.

The user separately reports the C1 scan-plane height above the chassis upper
surface as `56 mm + 29.8 mm = 85.8 mm`.

These values are `MANUAL_EVIDENCE_VERIFIED` as supplied records. Measurement
instrument, tolerance, loaded vehicle mass, coordinate-axis definition, CAD
revision, and as-built agreement remain `UNVERIFIED`. In particular, the
ultrasonic tuples must not be consumed as rover-frame `x/y/z` until the source
CAD axes are mapped to the repository convention (`+x` forward, `+y` left,
`+z` up).

## Visible Assembly Boundary

The photographs support the following limited observations:

- one assembled four-wheel mecanum rover exterior is visible;
- the vehicle front is explicitly marked in the top view;
- three front-face HC-SR04 modules are visible;
- one top-mounted RPLIDAR C1 and one installed GY-521/MPU6050 are visible;
- the GY-521/MPU6050 photographs preserve its orientation relative to vehicle
  front for later axis-transform work.

The photographs do not expose the OpenRF1 wiring bay clearly enough to verify
CN1-CN4 tracing, pin-1 orientation, resistor networks, fuse, wire gauge, power
rails, or common-ground continuity. Wheel roller handedness is not promoted to
a confirmed X-layout solely from these views; a controlled motion test or a
clear wheel-by-wheel record is still required.

## Remaining Manual Gates

- battery barrel polarity and measured battery/VIN/5 V/3.3 V/buck voltages;
- BMS continuous/peak current, installed fuse, and main wire gauge;
- CN1-CN4 to physical FL/FR/RL/RR trace;
- four motor-command signs and four encoder signs;
- one-revolution encoder counts;
- C1 rover-frame `x/y/yaw` and confirmation of the 85.8 mm as-built datum;
- source-CAD to rover-frame transform for all three ultrasonic tuples;
- TCRT5000 and Hall as-built positions, heights, polarities, and thresholds;
- explicit separate authorization before serial access, flashing, or powered
  raised-wheel testing.
