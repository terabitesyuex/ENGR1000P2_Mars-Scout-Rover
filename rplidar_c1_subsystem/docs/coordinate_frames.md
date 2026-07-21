# SUPERSEDED HISTORICAL COPY

Use repository-root `docs/coordinate_frames.md` for current coordinate-frame rules. The current physical inventory has one C1 (`c1_1`); no dual-C1 transform is active.

# Coordinate Frames

The project uses two coordinate systems: the native C1 scan convention and the internal rover convention.

## Native C1 Convention

- Origin at the LiDAR rotation center.
- Positive x points forward.
- Angle increases clockwise.
- Native system is left-handed.

## Rover Convention

- Positive x points forward.
- Positive y points left.
- Positive angle is counterclockwise.
- Right-handed 2D robotics convention.

## Conversion

Convert native clockwise angle to rover angle:

```text
robot_angle_deg = normalize_angle(-native_clockwise_angle_deg)
```

Then convert polar range to Cartesian position:

```text
angle_rad = robot_angle_deg * pi / 180
x_m = distance_mm / 1000.0 * cos(angle_rad)
y_m = distance_mm / 1000.0 * sin(angle_rad)
```

## Expected Cardinal Directions

| Native clockwise angle | Rover angle | Cartesian direction |
| --- | --- | --- |
| 0 degrees | 0 degrees | +x forward |
| 90 degrees | 270 degrees | -y right |
| 180 degrees | 180 degrees | -x rear |
| 270 degrees | 90 degrees | +y left |

Do not mix millimetres and metres. Store distances in millimetres in scan samples and convert to metres only when computing Cartesian coordinates.
