from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from rplidar_c1_tools.vehicle_demo_encoder import (
    ENCODER_MAPPING_STATUS,
    VehicleDemoConnectorEncoderSample,
    VehicleDemoEncoderTelemetryError,
    analyze_vehicle_demo_encoder_stream,
    iter_vehicle_demo_encoder_samples,
    modular_counter_delta_16,
    parse_vehicle_demo_encoder_line,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "pc" / "src"


def _encoder_line(
    sequence: int,
    timestamp_ms: int,
    *,
    interval_ms: int = 50,
    raw: tuple[int, int, int, int] = (10, 20, 30, 40),
    delta: tuple[int, int, int, int] = (1, 2, 3, 4),
    cumulative: tuple[int, int, int, int] = (1, 2, 3, 4),
    mapping_status: str = ENCODER_MAPPING_STATUS,
    signs_verified: object = False,
) -> str:
    payload: dict[str, object] = {
        "mapping_status": mapping_status,
        "counter_bits": 16,
        "interval_ms": interval_ms,
        "direction_signs_verified": signs_verified,
    }
    for index, connector in enumerate(("cn1", "cn2", "cn3", "cn4")):
        payload[f"{connector}_raw_count"] = raw[index]
        payload[f"{connector}_delta_count"] = delta[index]
        payload[f"{connector}_cumulative_count"] = cumulative[index]
    return json.dumps(
        {
            "sequence": sequence,
            "timestamp_ms": timestamp_ms,
            "message_type": "vehicle_demo_encoder",
            "status": "raw_counts",
            "payload": payload,
        },
        separators=(",", ":"),
    ) + "\n"


def _identity_line(sequence: int, timestamp_ms: int) -> str:
    return json.dumps(
        {
            "sequence": sequence,
            "timestamp_ms": timestamp_ms,
            "message_type": "vehicle_demo_identity",
            "status": "software_ready",
            "payload": {},
        },
        separators=(",", ":"),
    ) + "\n"


def test_parser_preserves_connector_counts_without_wheel_or_sign_claims() -> None:
    sample = parse_vehicle_demo_encoder_line(_encoder_line(3, 150))

    assert sample == VehicleDemoConnectorEncoderSample(
        sequence=3,
        timestamp_ms=150,
        interval_ms=50,
        raw_counts=(10, 20, 30, 40),
        delta_counts=(1, 2, 3, 4),
        cumulative_counts=(1, 2, 3, 4),
    )
    assert sample.direction_signs_verified is False
    assert "front_left" not in repr(sample)


@pytest.mark.parametrize(
    ("current", "previous", "expected"),
    [
        (101, 100, 1),
        (100, 101, -1),
        (1, 65534, 3),
        (65534, 1, -3),
        (32768, 0, -32768),
    ],
)
def test_modular_counter_delta_16(current: int, previous: int, expected: int) -> None:
    assert modular_counter_delta_16(current, previous) == expected


def test_stream_validates_wrap_interval_and_cumulative_counts() -> None:
    lines = [
        _identity_line(0, 0),
        _encoder_line(
            1,
            50,
            raw=(65534, 1, 100, 200),
            delta=(0, 0, 0, 0),
            cumulative=(0, 0, 0, 0),
        ),
        _encoder_line(
            2,
            100,
            raw=(1, 65534, 105, 198),
            delta=(3, -3, 5, -2),
            cumulative=(3, -3, 5, -2),
        ),
    ]

    samples = list(iter_vehicle_demo_encoder_samples(lines))

    assert len(samples) == 2
    assert samples[-1].delta_counts == (3, -3, 5, -2)


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("not-json\n", "invalid JSON"),
        (_encoder_line(1, 50, mapping_status="guessed"), "mapping status"),
        (_encoder_line(1, 50, signs_verified=True), "must remain unverified"),
        (_encoder_line(1, 50, raw=(65536, 0, 0, 0)), "cn1_raw_count"),
        (_encoder_line(1, 50, delta=(32768, 0, 0, 0)), "cn1_delta_count"),
        (_encoder_line(1, 50, interval_ms=0), "interval_ms must be positive"),
    ],
)
def test_invalid_encoder_records_are_rejected(line: str, message: str) -> None:
    with pytest.raises(VehicleDemoEncoderTelemetryError, match=message):
        parse_vehicle_demo_encoder_line(line)


def test_stream_rejects_inconsistent_delta_interval_and_cumulative() -> None:
    first = _encoder_line(1, 50, raw=(10, 20, 30, 40), cumulative=(1, 2, 3, 4))
    with pytest.raises(VehicleDemoEncoderTelemetryError, match="interval"):
        list(
            iter_vehicle_demo_encoder_samples(
                [first, _encoder_line(2, 101, interval_ms=50, raw=(11, 22, 33, 44), cumulative=(2, 4, 6, 8))]
            )
        )
    with pytest.raises(VehicleDemoEncoderTelemetryError, match="delta"):
        list(
            iter_vehicle_demo_encoder_samples(
                [first, _encoder_line(2, 100, raw=(12, 22, 33, 44), cumulative=(2, 4, 6, 8))]
            )
        )
    with pytest.raises(VehicleDemoEncoderTelemetryError, match="cumulative"):
        list(
            iter_vehicle_demo_encoder_samples(
                [first, _encoder_line(2, 100, raw=(11, 22, 33, 44), cumulative=(99, 4, 6, 8))]
            )
        )


def test_summary_reports_connector_counts_only() -> None:
    summary = analyze_vehicle_demo_encoder_stream(
        [
            _encoder_line(1, 50, cumulative=(1, 2, 3, 4)),
            _encoder_line(
                2,
                100,
                raw=(11, 22, 33, 44),
                cumulative=(2, 4, 6, 8),
            ),
        ]
    )

    assert summary.sample_count == 2
    assert summary.duration_ms == 50
    assert summary.final_cumulative_counts == (2, 4, 6, 8)
    text = summary.to_text()
    assert "physical_wheel_mapping_verified: false" in text
    assert "direction_signs_verified: false" in text
    assert "cn4_final_cumulative_count: 8" in text


def test_offline_cli_inspects_encoder_file_from_other_cwd(tmp_path: Path) -> None:
    source = tmp_path / "vehicle.jsonl"
    report = tmp_path / "report.txt"
    source.write_text(_encoder_line(1, 50), encoding="utf-8", newline="")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SRC_ROOT)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "rplidar_c1_tools",
            "inspect-vehicle-demo-encoder",
            "--input",
            str(source),
            "--output",
            str(report),
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert report.read_text(encoding="utf-8") == result.stdout
    assert "sample_count: 1" in result.stdout
