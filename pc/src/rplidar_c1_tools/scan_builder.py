"""Build and validate unified scan frames.

This module intentionally contains no hardware parsing. Future real RPLIDAR
drivers should decode packets elsewhere, convert angles into the rover-frame
degree convention, then pass `ScanPoint` objects here.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping

from .data_models import MetadataValue, ScanFrame, ScanPoint


class ScanValidationError(ValueError):
    """Raised when scan input cannot form a valid `ScanFrame`."""


def create_scan_point(
    angle_deg: float,
    distance_mm: int,
    quality: int | None = None,
) -> ScanPoint:
    """Create one validated scan point."""
    point = ScanPoint(angle_deg=angle_deg, distance_mm=distance_mm, quality=quality)
    validate_scan_point(point)
    return point


def build_scan_frame(
    points: Iterable[ScanPoint],
    *,
    timestamp_us: int,
    frame_id: int | None = None,
    source: str = "unknown",
    metadata: Mapping[str, MetadataValue] | None = None,
) -> ScanFrame:
    """Validate points and return a `ScanFrame` for downstream consumers."""
    if not isinstance(timestamp_us, int) or timestamp_us < 0:
        raise ScanValidationError("timestamp_us must be a non-negative integer")
    if frame_id is not None and (not isinstance(frame_id, int) or frame_id < 0):
        raise ScanValidationError("frame_id must be a non-negative integer or None")
    if not source:
        raise ScanValidationError("source must be a non-empty string")

    validated_points = [validate_scan_point(point) for point in points]
    if not validated_points:
        raise ScanValidationError("scan frame must contain at least one point")

    return ScanFrame(
        timestamp_us=timestamp_us,
        points=validated_points,
        frame_id=frame_id,
        source=source,
        metadata=dict(metadata or {}),
    )


def validate_scan_point(point: ScanPoint) -> ScanPoint:
    """Return a point when valid, otherwise raise `ScanValidationError`."""
    if not isinstance(point, ScanPoint):
        raise ScanValidationError("point must be a ScanPoint")
    if not math.isfinite(point.angle_deg):
        raise ScanValidationError("angle_deg must be finite")
    if point.angle_deg < 0.0 or point.angle_deg >= 360.0:
        raise ScanValidationError("angle_deg must be in the range [0, 360)")
    if not isinstance(point.distance_mm, int):
        raise ScanValidationError("distance_mm must be an integer")
    if point.distance_mm <= 0:
        raise ScanValidationError("distance_mm must be positive")
    if point.quality is not None:
        if not isinstance(point.quality, int) or point.quality < 0:
            raise ScanValidationError("quality must be a non-negative integer or None")
    return point
