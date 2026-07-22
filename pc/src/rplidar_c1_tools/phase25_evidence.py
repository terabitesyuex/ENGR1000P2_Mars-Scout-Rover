"""Offline validation for the Phase 2.5 physical ``c1_1`` evidence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import struct
from typing import Any, Mapping, Sequence


SOURCE_ARCHIVE_SHA256 = "C28F5B0E9C3E6BC45F39E0C16A2EA90AA1555CB023064A427814F37CC8F109B6"
RVIZ_RELATIVE_PATH = Path("evidence/phase2.5/c1_1_ros2_rviz_laserscan.png")
RVIZ_SHA256 = "A4B56A61B62D43F870F7937488D9D7C85691B54DD0CE3268389618C679FE6A03"
RVIZ_WIDTH_PX = 2560
RVIZ_HEIGHT_PX = 1539

CAPTURE_SPECS: Mapping[str, Mapping[str, object]] = {
    "c1_1_live_1x360": {
        "path": Path("evidence/phase2.5/c1_1_live_1x360.jsonl"),
        "sha256": "4EEB09FE073E694DFA125B475DB2960BB2DD303DCB2C2DD0B05550054FEEE89E",
        "scan_count": 1,
    },
    "c1_1_pc_direct_1x360": {
        "path": Path("evidence/phase2.5/c1_1_pc_direct_1x360.jsonl"),
        "sha256": "18DC13FF5295CA93FA6461AE8FD06681C10D8B458CE8CF18E28AFE5ED7CF921D",
        "scan_count": 1,
    },
    "c1_1_stability_50x360": {
        "path": Path("evidence/phase2.5/c1_1_stability_50x360.jsonl"),
        "sha256": "4108519965A98133023ED53FA17CB97D232E5F18C37720FFFC59F0EAF8963A30",
        "scan_count": 50,
    },
    "c1_1_target_500mm": {
        "path": Path("evidence/phase2.5/c1_1_target_500mm.jsonl"),
        "sha256": "7667E3391429C46836FB467121B5D241FE4FF7EC22EBF48D38E38FBE288FCED8",
        "scan_count": 10,
    },
    "c1_1_target_1000mm": {
        "path": Path("evidence/phase2.5/c1_1_target_1000mm.jsonl"),
        "sha256": "9D0C01BA8886BEC3D31368A2E581A4DE6E7DE40AB6BE47A218E04C31ABADCA5C",
        "scan_count": 10,
    },
    "c1_1_target_2000mm": {
        "path": Path("evidence/phase2.5/c1_1_target_2000mm.jsonl"),
        "sha256": "E857ABEE2B42861D074E19F0767EEE165098538CB660436D4AA02B42A03256B7",
        "scan_count": 10,
    },
    "c1_1_target_left": {
        "path": Path("evidence/phase2.5/c1_1_target_left.jsonl"),
        "sha256": "7FE354A2AD4C205177A30D58CDB74558605FE20521A91BDAD1462B6EE69CF85A",
        "scan_count": 10,
    },
    "c1_1_target_right": {
        "path": Path("evidence/phase2.5/c1_1_target_right.jsonl"),
        "sha256": "7E966AD216796464E3FA18DA97EA10567B518B406E3658D411003AA4D8375675",
        "scan_count": 10,
    },
}

EXPECTED_SCHEMA_NAME = "mars_scout_multisensor_recording"
EXPECTED_SCHEMA_VERSION = 1
EXPECTED_SENSOR_ID = "c1_1"
EXPECTED_SOURCE = "pc_direct_c1"
EXPECTED_POINTS_PER_SCAN = 360
GENERATED_TIMESTAMP_STEP_US = 100_000
PROFILE_WHITE_RANGE_MAX_MM = 12_000

_PRIVATE_MARKERS = (
    "C:" + "\\Users",
    "Desk" + "top",
    "App" + "Data",
    "Documents" + "\\GitHub",
    "zig" + "xi",
)
_COM_PORT_PATTERN = re.compile(r"\bCOM[0-9]+\b", re.IGNORECASE)


class Phase25EvidenceError(ValueError):
    """Raised when committed Phase 2.5 evidence differs from its lock."""


@dataclass(frozen=True, slots=True)
class Phase25CaptureSummary:
    name: str
    sha256: str
    scan_count: int
    point_count: int
    sequence_start: int
    sequence_end: int
    timestamp_start_us: int
    timestamp_end_us: int
    generated_timestamp_step_us: int | None
    distance_min_mm: int
    distance_max_mm: int
    quality_min: int
    quality_max: int
    zero_quality_count: int
    over_profile_range_count: int


@dataclass(frozen=True, slots=True)
class Phase25RvizSummary:
    sha256: str
    width_px: int
    height_px: int
    bit_depth: int
    color_type: int


def validate_phase25_capture(
    repo_root: Path,
    name: str,
    *,
    evidence_path: Path | None = None,
) -> Phase25CaptureSummary:
    try:
        spec = CAPTURE_SPECS[name]
    except KeyError as exc:
        raise Phase25EvidenceError(f"unknown capture {name!r}") from exc

    path = evidence_path if evidence_path is not None else repo_root / Path(spec["path"])
    raw_bytes = path.read_bytes()
    actual_sha256 = hashlib.sha256(raw_bytes).hexdigest().upper()
    if actual_sha256 != spec["sha256"]:
        raise Phase25EvidenceError(
            f"expected evidence sha256 {spec['sha256']}, got {actual_sha256}"
        )

    raw_text = raw_bytes.decode("utf-8")
    _validate_no_private_local_information(raw_text)
    records = _parse_jsonl(raw_text)
    return _validate_capture_records(name, records, int(spec["scan_count"]), actual_sha256)


def validate_all_phase25_captures(repo_root: Path) -> list[Phase25CaptureSummary]:
    return [validate_phase25_capture(repo_root, name) for name in CAPTURE_SPECS]


def validate_phase25_rviz_evidence(repo_root: Path) -> Phase25RvizSummary:
    raw_bytes = (repo_root / RVIZ_RELATIVE_PATH).read_bytes()
    actual_sha256 = hashlib.sha256(raw_bytes).hexdigest().upper()
    if actual_sha256 != RVIZ_SHA256:
        raise Phase25EvidenceError(
            f"expected RViz sha256 {RVIZ_SHA256}, got {actual_sha256}"
        )
    if len(raw_bytes) < 29 or raw_bytes[:8] != b"\x89PNG\r\n\x1a\n":
        raise Phase25EvidenceError("RViz evidence is not a PNG")
    if raw_bytes[12:16] != b"IHDR":
        raise Phase25EvidenceError("RViz PNG is missing IHDR")

    width_px, height_px = struct.unpack(">II", raw_bytes[16:24])
    bit_depth = raw_bytes[24]
    color_type = raw_bytes[25]
    if (width_px, height_px) != (RVIZ_WIDTH_PX, RVIZ_HEIGHT_PX):
        raise Phase25EvidenceError("RViz PNG dimensions do not match the locked evidence")
    if bit_depth != 8 or color_type != 2:
        raise Phase25EvidenceError("RViz PNG pixel format does not match the locked evidence")
    return Phase25RvizSummary(
        sha256=actual_sha256,
        width_px=width_px,
        height_px=height_px,
        bit_depth=bit_depth,
        color_type=color_type,
    )


def _validate_no_private_local_information(raw_text: str) -> None:
    if any(marker in raw_text for marker in _PRIVATE_MARKERS):
        raise Phase25EvidenceError("evidence contains private local information")
    if _COM_PORT_PATTERN.search(raw_text):
        raise Phase25EvidenceError("evidence contains a concrete COM port")


def _parse_jsonl(raw_text: str) -> list[Mapping[str, Any]]:
    records: list[Mapping[str, Any]] = []
    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        if not line:
            raise Phase25EvidenceError(f"blank JSONL line at {line_number}")
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Phase25EvidenceError(f"invalid JSON on line {line_number}: {exc}") from exc
        if not isinstance(record, dict):
            raise Phase25EvidenceError(f"record {line_number} is not a JSON object")
        records.append(record)
    return records


def _validate_capture_records(
    name: str,
    records: Sequence[Mapping[str, Any]],
    expected_scan_count: int,
    sha256: str,
) -> Phase25CaptureSummary:
    if len(records) != expected_scan_count + 1:
        raise Phase25EvidenceError(f"{name} has an unexpected record count")
    _validate_header(records[0])

    scans = records[1:]
    distances: list[int] = []
    qualities: list[int] = []
    for index, scan in enumerate(scans):
        _validate_scan(scan, index)
        points = scan["points"]
        assert isinstance(points, list)
        for point in points:
            assert isinstance(point, dict)
            distances.append(point["distance_mm"])
            qualities.append(point["quality"])

    timestamps = [int(scan["timestamp_us"]) for scan in scans]
    timestamp_steps = [next_value - value for value, next_value in zip(timestamps, timestamps[1:])]
    if timestamp_steps and timestamp_steps != [GENERATED_TIMESTAMP_STEP_US] * (len(scans) - 1):
        raise Phase25EvidenceError(f"{name} timestamps do not use the generated 100 ms step")

    return Phase25CaptureSummary(
        name=name,
        sha256=sha256,
        scan_count=len(scans),
        point_count=len(distances),
        sequence_start=int(scans[0]["sequence"]),
        sequence_end=int(scans[-1]["sequence"]),
        timestamp_start_us=timestamps[0],
        timestamp_end_us=timestamps[-1],
        generated_timestamp_step_us=GENERATED_TIMESTAMP_STEP_US if timestamp_steps else None,
        distance_min_mm=min(distances),
        distance_max_mm=max(distances),
        quality_min=min(qualities),
        quality_max=max(qualities),
        zero_quality_count=sum(value == 0 for value in qualities),
        over_profile_range_count=sum(value > PROFILE_WHITE_RANGE_MAX_MM for value in distances),
    )


def _validate_header(header: Mapping[str, Any]) -> None:
    expected = {
        "record_type": "header",
        "schema_name": EXPECTED_SCHEMA_NAME,
        "schema_version": EXPECTED_SCHEMA_VERSION,
    }
    for key, value in expected.items():
        if header.get(key) != value:
            raise Phase25EvidenceError(f"header {key} must be {value!r}")

    metadata = header.get("metadata")
    if not isinstance(metadata, dict):
        raise Phase25EvidenceError("header metadata must be an object")
    metadata_expected = {
        "captured_sensor_id": EXPECTED_SENSOR_ID,
        "source": EXPECTED_SOURCE,
        "hardware_validation": "manual_required",
        "dual_c1_simultaneous": "not_current_scope",
    }
    for key, value in metadata_expected.items():
        if metadata.get(key) != value:
            raise Phase25EvidenceError(f"header metadata {key} must be {value!r}")

    inventory = header.get("sensor_inventory")
    if not isinstance(inventory, list) or len(inventory) != 1:
        raise Phase25EvidenceError("header must declare exactly one sensor")
    if inventory[0].get("sensor_id") != EXPECTED_SENSOR_ID:
        raise Phase25EvidenceError("header sensor inventory must contain c1_1")

    convention = header.get("coordinate_convention")
    if not isinstance(convention, dict):
        raise Phase25EvidenceError("header coordinate_convention must be an object")
    convention_expected = {
        "frame": "rover",
        "angle_zero": "forward",
        "positive_angle": "counterclockwise",
        "angle_unit": "deg",
        "distance_unit": "mm",
    }
    for key, value in convention_expected.items():
        if convention.get(key) != value:
            raise Phase25EvidenceError(f"coordinate convention {key} must be {value!r}")


def _validate_scan(scan: Mapping[str, Any], index: int) -> None:
    expected = {
        "record_type": "lidar_scan",
        "schema_name": EXPECTED_SCHEMA_NAME,
        "schema_version": EXPECTED_SCHEMA_VERSION,
        "sensor_id": EXPECTED_SENSOR_ID,
        "source": EXPECTED_SOURCE,
        "sequence": index + 1,
        "frame_id": index,
        "timestamp_us": index * GENERATED_TIMESTAMP_STEP_US,
        "rover_pose": None,
    }
    for key, value in expected.items():
        if scan.get(key) != value:
            raise Phase25EvidenceError(f"scan {index} {key} must be {value!r}")

    metadata = scan.get("metadata")
    if not isinstance(metadata, dict):
        raise Phase25EvidenceError(f"scan {index} metadata must be an object")
    if metadata.get("sensor_id") != EXPECTED_SENSOR_ID:
        raise Phase25EvidenceError(f"scan {index} metadata sensor_id must be c1_1")
    if metadata.get("hardware_source") != "pc_direct":
        raise Phase25EvidenceError(f"scan {index} hardware_source must be pc_direct")
    if metadata.get("physical_test_required") is not True:
        raise Phase25EvidenceError(f"scan {index} physical_test_required must be true")

    points = scan.get("points")
    if not isinstance(points, list) or len(points) != EXPECTED_POINTS_PER_SCAN:
        raise Phase25EvidenceError(f"scan {index} must contain 360 points")
    for point_index, point in enumerate(points):
        if not isinstance(point, dict) or set(point) != {"angle_deg", "distance_mm", "quality"}:
            raise Phase25EvidenceError(f"scan {index} point {point_index} has an invalid shape")
        angle_deg = point["angle_deg"]
        distance_mm = point["distance_mm"]
        quality = point["quality"]
        if isinstance(angle_deg, bool) or not isinstance(angle_deg, (int, float)):
            raise Phase25EvidenceError(f"scan {index} point {point_index} angle is not numeric")
        if not math.isfinite(float(angle_deg)) or not 0.0 <= float(angle_deg) <= 360.0:
            raise Phase25EvidenceError(f"scan {index} point {point_index} angle is out of range")
        if isinstance(distance_mm, bool) or not isinstance(distance_mm, int) or distance_mm <= 0:
            raise Phase25EvidenceError(f"scan {index} point {point_index} distance is invalid")
        if isinstance(quality, bool) or not isinstance(quality, int) or not 0 <= quality <= 63:
            raise Phase25EvidenceError(f"scan {index} point {point_index} quality is invalid")
