from __future__ import annotations

import hashlib
from pathlib import Path

from rplidar_c1_tools.stm32_sensor_protocol import iter_stm32_telemetry


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = REPO_ROOT / "evidence" / "phase3.2a" / "bh1750_physical_ba2024b_20260716_234217.jsonl"
REPORT_PATH = REPO_ROOT / "evidence" / "phase3.2a" / "bh1750_physical_evidence.md"
EXPECTED_SHA256 = "6B9A2AE724C6473D6D8F18533CDC7B7081BCC782709862E914CE6B20B1690317"


def test_phase32a_bh1750_physical_evidence_hash_and_shape():
    raw_bytes = EVIDENCE_PATH.read_bytes()

    assert hashlib.sha256(raw_bytes).hexdigest().upper() == EXPECTED_SHA256
    assert raw_bytes.decode("utf-8")
    assert raw_bytes.count(b"\n") == 60


def test_phase32a_bh1750_physical_evidence_records_are_continuous_and_valid():
    messages = list(iter_stm32_telemetry(EVIDENCE_PATH.read_text(encoding="utf-8").splitlines()))

    assert len(messages) == 60
    assert [message.sequence for message in messages] == list(range(769, 829))
    assert [message.timestamp_ms for message in messages] == list(range(384680, 414181, 500))
    assert {message.protocol for message in messages} == {"mars_scout_stm32_sensor_telemetry"}
    assert {message.version for message in messages} == {1}
    assert {message.message_type for message in messages} == {"illuminance"}
    assert {message.sensor_id for message in messages} == {"bh1750_1"}
    assert {message.status for message in messages} == {"ok"}

    lux_values = [float(message.payload["illuminance_lux"]) for message in messages]

    assert min(lux_values) == 0.0
    assert max(lux_values) == 20.83
    assert 0.0 in lux_values
    assert 20.83 in lux_values


def test_phase32a_evidence_report_is_sanitized_and_truthful():
    report = REPORT_PATH.read_text(encoding="utf-8")

    required = [
        "Firmware commit | `ba2024b`",
        "MANUAL_EVIDENCE_VERIFIED",
        "Absolute illuminance calibration",
        "UNVERIFIED",
        EXPECTED_SHA256,
    ]
    forbidden = [
        "C:" + "\\Users",
        "Desk" + "top",
        "COM" + "5",
        "zig" + "xi",
        "unique 96-" + "bit",
    ]

    for snippet in required:
        assert snippet in report
    for snippet in forbidden:
        assert snippet not in report
