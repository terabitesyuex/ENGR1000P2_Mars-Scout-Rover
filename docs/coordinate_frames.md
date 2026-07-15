# Coordinate Frames

Phase 2.2 freezes the coordinate convention used by PC-side scan processing.

## Project Convention

- `+x` points forward from the rover.
- `+y` points left.
- `+z` points upward.
- Positive yaw is counterclockwise.
- `ScanPoint.angle_deg` is measured in degrees.
- `ScanPoint.angle_deg` is already in the rover-frame convention: `0` degrees forward, positive counterclockwise.
- LiDAR input distance is stored in millimetres.
- Internal Cartesian distances use metres.

## Native C1 Convention

Native RPLIDAR C1 packets may report clockwise-positive angles. Native angles must be converted explicitly before they are stored as `ScanPoint.angle_deg`:

```text
rover_angle_deg = normalize_angle_deg(-native_angle_deg)
```

Do not apply this native conversion to synthetic `ScanPoint` values. Phase 2.1 synthetic scans already use the rover-frame convention.

Phase 2.5 PC-direct C1 capture applies this native-clockwise conversion in the driver boundary before creating `ScanPoint` objects. Recording and replay files store only the project rover-frame convention.

## Polar-To-Cartesian Formula

For a normalized rover-frame point:

```text
angle_rad = radians(angle_deg)
x_m = distance_mm / 1000.0 * cos(angle_rad)
y_m = distance_mm / 1000.0 * sin(angle_rad)
```

Worked example:

- angle: `90` degrees;
- distance: `1000` mm;
- result: `x_m` approximately `0` m, `y_m` approximately `1` m.

Tiny values such as `6.123233995736766e-17` are normal floating-point approximations of zero.

## Cardinal Directions

| Rover angle | Cartesian direction |
| --- | --- |
| 0 degrees | +x forward |
| 90 degrees | +y left |
| 180 degrees | -x rear |
| 270 degrees | -y right |

## Phase 2.3 Display Conventions

Polar scan view:

- zero degrees is shown at the top;
- positive angles proceed counterclockwise;
- `+90` degrees appears on the left;
- radial units are metres.

Rover-centric Cartesian point-cloud view:

- image top represents rover forward;
- image left represents rover left;
- image right represents rover right;
- image bottom represents rover backward;
- units are metres.

The Cartesian display is an image orientation, not a new coordinate frame. It plots rover `y_m` on the horizontal display axis and rover `x_m` on the vertical display axis, then inverts the horizontal axis so positive rover-left appears on the left side of the image. Stored `CartesianPoint` signs are not changed.

## Frame Names

- `lidar_frame`: coordinate frame at the LiDAR optical rotation center.
- `base_link`: future rover body frame.
- `odom`: future short-term local odometry frame.
- `map`: future short-range accumulated mapping frame.

`sensor_id` is an identity label, not a coordinate frame. `c1_1` and `c1_2`
remain neutral IDs until each unit's physical mounting position, height, yaw,
and orientation are verified.

The physical LiDAR mounting translation and yaw from `lidar_frame` to `base_link` remain UNVERIFIED. Phase 2.2 provides only mathematical transform helpers and does not apply any physical mounting offset.

Phase 2.3 visualizations are single-frame synthetic scan views. Phase 2.4 recordings may include optional `rover_pose` records for replay metadata, but these records are not proof of encoder odometry and do not create a verified `odom` frame.

No dual-C1 fusion transform is implemented. Do not combine `c1_1` and `c1_2`
geometry until both unit poses are physically measured and documented.

Do not mix millimetres and metres. Store LiDAR range in millimetres in scan models and convert to metres only when computing Cartesian coordinates.
