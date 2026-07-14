"""PC tools for the Mars Scout Rover RPLIDAR C1 subsystem."""

from .coordinate_transform import (
    native_clockwise_to_robot_angle_deg,
    normalize_angle_deg,
    polar_to_cartesian_m,
)
from .data_models import LidarSample, LidarScan, RawLidarSample, ScanFrame, ScanPoint
from .data_models import ScanSource
from .scan_builder import ScanValidationError, build_scan_frame, create_scan_point
from .synthetic_scan import (
    SyntheticRoomConfig,
    SyntheticScanSource,
    generate_circle_scan,
    generate_room_scan,
)

__all__ = [
    "LidarSample",
    "LidarScan",
    "RawLidarSample",
    "ScanFrame",
    "ScanPoint",
    "ScanSource",
    "ScanValidationError",
    "SyntheticRoomConfig",
    "SyntheticScanSource",
    "build_scan_frame",
    "create_scan_point",
    "generate_circle_scan",
    "generate_room_scan",
    "native_clockwise_to_robot_angle_deg",
    "normalize_angle_deg",
    "polar_to_cartesian_m",
]
