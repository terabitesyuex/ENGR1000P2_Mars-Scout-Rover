"""Strict offline inspection for VehicleDemo connector encoder telemetry."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
import json
from typing import Any


ENCODER_MAPPING_STATUS = "vendor_connector_mapping_physical_wheels_unverified"
ENCODER_COUNTER_BITS = 16
_TOP_LEVEL_FIELDS = {"sequence", "timestamp_ms", "message_type", "status", "payload"}
_IGNORED_MESSAGE_TYPES = {
    "vehicle_demo_identity",
    "vehicle_demo_status",
    "vehicle_demo_motor_diag",
    "vehicle_demo_hall_event",
}
_CONNECTORS = ("cn1", "cn2", "cn3", "cn4")
_ENCODER_PAYLOAD_FIELDS = {
    "mapping_status",
    "counter_bits",
    "interval_ms",
    "direction_signs_verified",
    *{
        f"{connector}_{suffix}"
        for connector in _CONNECTORS
        for suffix in ("raw_count", "delta_count", "cumulative_count")
    },
}


class VehicleDemoEncoderTelemetryError(ValueError):
    """Raised when connector encoder JSONL is unsafe to consume."""

    def __init__(self, message: str, *, line_number: int | None = None) -> None:
        self.line_number = line_number
        prefix = f"line {line_number}: " if line_number is not None else ""
        super().__init__(f"{prefix}{message}")


@dataclass(frozen=True, slots=True)
class VehicleDemoConnectorEncoderSample:
    sequence: int
    timestamp_ms: int
    interval_ms: int
    raw_counts: tuple[int, int, int, int]
    delta_counts: tuple[int, int, int, int]
    cumulative_counts: tuple[int, int, int, int]
    mapping_status: str = ENCODER_MAPPING_STATUS
    direction_signs_verified: bool = False


@dataclass(frozen=True, slots=True)
class VehicleDemoEncoderSummary:
    sample_count: int
    first_timestamp_ms: int
    last_timestamp_ms: int
    duration_ms: int
    minimum_interval_ms: int
    maximum_interval_ms: int
    final_cumulative_counts: tuple[int, int, int, int]

    def to_text(self) -> str:
        lines = [
            "source: vehicle_demo_jsonl",
            f"mapping_status: {ENCODER_MAPPING_STATUS}",
            "physical_wheel_mapping_verified: false",
            "direction_signs_verified: false",
            f"counter_bits: {ENCODER_COUNTER_BITS}",
            f"sample_count: {self.sample_count}",
            f"first_timestamp_ms: {self.first_timestamp_ms}",
            f"last_timestamp_ms: {self.last_timestamp_ms}",
            f"duration_ms: {self.duration_ms}",
            f"minimum_interval_ms: {self.minimum_interval_ms}",
            f"maximum_interval_ms: {self.maximum_interval_ms}",
        ]
        lines.extend(
            f"cn{index}_final_cumulative_count: {count}"
            for index, count in enumerate(self.final_cumulative_counts, start=1)
        )
        return "\n".join(lines) + "\n"


def parse_vehicle_demo_encoder_line(
    line: str,
    *,
    line_number: int | None = None,
) -> VehicleDemoConnectorEncoderSample | None:
    record = _parse_record(line, line_number)
    message_type = _string(record["message_type"], "message_type", line_number)
    if message_type in _IGNORED_MESSAGE_TYPES:
        return None
    if message_type != "vehicle_demo_encoder":
        raise VehicleDemoEncoderTelemetryError(
            "unsupported message_type",
            line_number=line_number,
        )
    if _string(record["status"], "status", line_number) != "raw_counts":
        raise VehicleDemoEncoderTelemetryError(
            "invalid encoder status",
            line_number=line_number,
        )
    payload = record["payload"]
    if not isinstance(payload, dict):
        raise VehicleDemoEncoderTelemetryError("payload must be an object", line_number=line_number)
    if set(payload) != _ENCODER_PAYLOAD_FIELDS:
        raise VehicleDemoEncoderTelemetryError(
            "unexpected encoder payload fields",
            line_number=line_number,
        )
    mapping_status = _string(payload["mapping_status"], "payload.mapping_status", line_number)
    if mapping_status != ENCODER_MAPPING_STATUS:
        raise VehicleDemoEncoderTelemetryError(
            "unsupported encoder mapping status",
            line_number=line_number,
        )
    if _integer(payload["counter_bits"], "payload.counter_bits", line_number) != 16:
        raise VehicleDemoEncoderTelemetryError("counter_bits must be 16", line_number=line_number)
    if payload["direction_signs_verified"] is not False:
        raise VehicleDemoEncoderTelemetryError(
            "direction signs must remain unverified",
            line_number=line_number,
        )
    interval_ms = _integer(payload["interval_ms"], "payload.interval_ms", line_number)
    if interval_ms <= 0:
        raise VehicleDemoEncoderTelemetryError("interval_ms must be positive", line_number=line_number)
    raw_counts = tuple(
        _bounded_integer(payload[f"{name}_raw_count"], f"payload.{name}_raw_count", 0, 65535, line_number)
        for name in _CONNECTORS
    )
    delta_counts = tuple(
        _bounded_integer(
            payload[f"{name}_delta_count"],
            f"payload.{name}_delta_count",
            -32768,
            32767,
            line_number,
        )
        for name in _CONNECTORS
    )
    cumulative_counts = tuple(
        _bounded_integer(
            payload[f"{name}_cumulative_count"],
            f"payload.{name}_cumulative_count",
            -(2**31),
            2**31 - 1,
            line_number,
        )
        for name in _CONNECTORS
    )
    return VehicleDemoConnectorEncoderSample(
        sequence=_non_negative_integer(record["sequence"], "sequence", line_number),
        timestamp_ms=_non_negative_integer(record["timestamp_ms"], "timestamp_ms", line_number),
        interval_ms=interval_ms,
        raw_counts=raw_counts,  # type: ignore[arg-type]
        delta_counts=delta_counts,  # type: ignore[arg-type]
        cumulative_counts=cumulative_counts,  # type: ignore[arg-type]
        mapping_status=mapping_status,
    )


def iter_vehicle_demo_encoder_samples(
    lines: Iterable[str],
) -> Iterator[VehicleDemoConnectorEncoderSample]:
    previous_sequence = -1
    previous_timestamp_ms = 0
    previous_sample: VehicleDemoConnectorEncoderSample | None = None
    for line_number, line in enumerate(lines, start=1):
        record = _parse_record(line, line_number)
        sequence = _non_negative_integer(record["sequence"], "sequence", line_number)
        timestamp_ms = _non_negative_integer(record["timestamp_ms"], "timestamp_ms", line_number)
        if sequence <= previous_sequence:
            raise VehicleDemoEncoderTelemetryError(
                "sequence must increase",
                line_number=line_number,
            )
        if timestamp_ms < previous_timestamp_ms:
            raise VehicleDemoEncoderTelemetryError(
                "timestamp_ms must be nondecreasing",
                line_number=line_number,
            )
        previous_sequence = sequence
        previous_timestamp_ms = timestamp_ms
        sample = parse_vehicle_demo_encoder_line(line, line_number=line_number)
        if sample is None:
            continue
        if previous_sample is not None:
            elapsed_ms = sample.timestamp_ms - previous_sample.timestamp_ms
            if elapsed_ms != sample.interval_ms:
                raise VehicleDemoEncoderTelemetryError(
                    "encoder interval does not match timestamps",
                    line_number=line_number,
                )
            for index in range(4):
                expected_delta = modular_counter_delta_16(
                    sample.raw_counts[index],
                    previous_sample.raw_counts[index],
                )
                if sample.delta_counts[index] != expected_delta:
                    raise VehicleDemoEncoderTelemetryError(
                        f"cn{index + 1} delta does not match raw counter wrap",
                        line_number=line_number,
                    )
                expected_cumulative = (
                    previous_sample.cumulative_counts[index] + sample.delta_counts[index]
                )
                if sample.cumulative_counts[index] != expected_cumulative:
                    raise VehicleDemoEncoderTelemetryError(
                        f"cn{index + 1} cumulative count mismatch",
                        line_number=line_number,
                    )
        previous_sample = sample
        yield sample


def analyze_vehicle_demo_encoder_stream(lines: Iterable[str]) -> VehicleDemoEncoderSummary:
    samples = list(iter_vehicle_demo_encoder_samples(lines))
    if not samples:
        raise VehicleDemoEncoderTelemetryError("no vehicle_demo_encoder records")
    return VehicleDemoEncoderSummary(
        sample_count=len(samples),
        first_timestamp_ms=samples[0].timestamp_ms,
        last_timestamp_ms=samples[-1].timestamp_ms,
        duration_ms=samples[-1].timestamp_ms - samples[0].timestamp_ms,
        minimum_interval_ms=min(sample.interval_ms for sample in samples),
        maximum_interval_ms=max(sample.interval_ms for sample in samples),
        final_cumulative_counts=samples[-1].cumulative_counts,
    )


def modular_counter_delta_16(current_count: int, previous_count: int) -> int:
    current = _bounded_integer(current_count, "current_count", 0, 65535, None)
    previous = _bounded_integer(previous_count, "previous_count", 0, 65535, None)
    unsigned_delta = (current - previous) & 0xFFFF
    return unsigned_delta if unsigned_delta <= 0x7FFF else unsigned_delta - 0x10000


def _parse_record(line: str, line_number: int | None) -> dict[str, Any]:
    try:
        value = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise VehicleDemoEncoderTelemetryError("invalid JSON", line_number=line_number) from exc
    if not isinstance(value, dict):
        raise VehicleDemoEncoderTelemetryError("record must be an object", line_number=line_number)
    if set(value) != _TOP_LEVEL_FIELDS:
        raise VehicleDemoEncoderTelemetryError(
            "unexpected top-level fields",
            line_number=line_number,
        )
    return value


def _string(value: object, name: str, line_number: int | None) -> str:
    if not isinstance(value, str):
        raise VehicleDemoEncoderTelemetryError(f"{name} must be a string", line_number=line_number)
    return value


def _integer(value: object, name: str, line_number: int | None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise VehicleDemoEncoderTelemetryError(f"{name} must be an integer", line_number=line_number)
    return value


def _non_negative_integer(value: object, name: str, line_number: int | None) -> int:
    result = _integer(value, name, line_number)
    if result < 0:
        raise VehicleDemoEncoderTelemetryError(
            f"{name} must be non-negative",
            line_number=line_number,
        )
    return result


def _bounded_integer(
    value: object,
    name: str,
    minimum: int,
    maximum: int,
    line_number: int | None,
) -> int:
    result = _integer(value, name, line_number)
    if result < minimum or result > maximum:
        raise VehicleDemoEncoderTelemetryError(
            f"{name} must be in [{minimum}, {maximum}]",
            line_number=line_number,
        )
    return result
