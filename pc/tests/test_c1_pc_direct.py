from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import types

import pytest

from rplidar_c1_tools.c1_pc_direct import (
    C1CaptureConfig,
    C1DecodedSample,
    C1DriverError,
    C1PcDirectDriver,
    C1ProtocolError,
    C1StandardScanParser,
    C1TimeoutError,
    BytesBufferTransport,
    PySerialByteTransport,
    capture_c1_session,
    decoded_sample_to_scan_point,
    parse_sample_hex,
)
from rplidar_c1_tools.cli import capture_c1_recording
from rplidar_c1_tools.replay import iter_lidar_scans, read_recording_header


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "pc" / "src"


def test_standard_scan_parser_recovers_from_prefix_and_converts_samples():
    parser = C1StandardScanParser()
    payload = b"\xA5\x5A\x05\x00\x00\x40\x81" + _node(0.0, 1000, quality=15, start=True) + _node(
        90.0,
        1500,
        quality=20,
    )

    samples = list(parser.feed(payload[:6], timestamp_us=10))
    samples += list(parser.feed(payload[6:], timestamp_us=11))

    assert [sample.native_angle_deg for sample in samples] == [0.0, 90.0]
    assert [sample.distance_mm for sample in samples] == [1000, 1500]
    assert samples[0].quality == 15
    assert samples[0].scan_start is True

    first_point = decoded_sample_to_scan_point(samples[0])
    second_point = decoded_sample_to_scan_point(samples[1])
    assert first_point.angle_deg == 0.0
    assert second_point.angle_deg == 270.0
    assert second_point.distance_mm == 1500


def test_decoded_sample_validation_rejects_invalid_values():
    with pytest.raises(C1ProtocolError, match="native_angle_deg"):
        decoded_sample_to_scan_point(
            C1DecodedSample(
                native_angle_deg=float("nan"),
                distance_mm=1000,
                quality=1,
                timestamp_us=0,
            )
        )
    with pytest.raises(C1ProtocolError, match="distance_mm"):
        decoded_sample_to_scan_point(
            C1DecodedSample(
                native_angle_deg=0.0,
                distance_mm=0,
                quality=1,
                timestamp_us=0,
            )
        )
    with pytest.raises(C1ProtocolError, match="quality"):
        decoded_sample_to_scan_point(
            C1DecodedSample(
                native_angle_deg=0.0,
                distance_mm=1000,
                quality=-1,
                timestamp_us=0,
            )
        )


def test_driver_interface_requires_connect_start_and_yields_scan_points():
    transport = BytesBufferTransport(_fixture_bytes())
    driver = C1PcDirectDriver(sensor_id="c1_1", transport=transport)

    with pytest.raises(C1DriverError, match="scan must be started"):
        next(driver.iter_scan_points())

    driver.connect()
    driver.start_scan()
    points = [next(driver.iter_scan_points(read_chunk_size=5)) for _ in range(4)]
    driver.disconnect()

    assert [point.angle_deg for point in points] == [0.0, 270.0, 180.0, 90.0]
    assert [point.distance_mm for point in points] == [1000, 1000, 1000, 1000]
    assert transport.writes[0] == bytes((0xA5, 0x20))
    assert transport.writes[-1] == bytes((0xA5, 0x25))


def test_driver_times_out_when_transport_returns_no_data():
    transport = BytesBufferTransport(b"")
    driver = C1PcDirectDriver(sensor_id="c1_1", transport=transport)
    driver.connect()
    driver.start_scan()

    with pytest.raises(C1TimeoutError, match="no C1 scan data"):
        next(driver.iter_scan_points(read_chunk_size=5, max_empty_reads=2))

    driver.disconnect()


def test_capture_session_writes_phase24_jsonl_and_replays(tmp_path):
    output = tmp_path / "c1_capture.jsonl"
    transport = BytesBufferTransport(_fixture_bytes())
    driver = C1PcDirectDriver(sensor_id="c1_1", transport=transport)

    capture_c1_session(
        driver=driver,
        output_path=output,
        config=C1CaptureConfig(sensor_id="c1_1", frames=1, points_per_frame=4, read_chunk_size=5),
    )

    header = read_recording_header(output)
    assert header["metadata"]["source"] == "pc_direct_c1"
    assert header["metadata"]["captured_sensor_id"] == "c1_1"
    assert header["metadata"]["dual_c1_simultaneous"] == "not_attempted"
    [record] = list(iter_lidar_scans(output))
    assert record.sensor_id == "c1_1"
    assert record.scan_frame.source == "pc_direct_c1"
    assert record.scan_frame.point_count == 4
    assert record.scan_frame.metadata["physical_test_required"] is True


def test_capture_rejects_sensor_mismatch_and_invalid_ids(tmp_path):
    with pytest.raises(ValueError, match="sensor_id"):
        C1PcDirectDriver(sensor_id="front_lidar", transport=BytesBufferTransport(b""))

    driver = C1PcDirectDriver(sensor_id="c1_1", transport=BytesBufferTransport(_fixture_bytes()))
    with pytest.raises(ValueError, match="must match"):
        capture_c1_session(
            driver=driver,
            output_path=tmp_path / "capture.jsonl",
            config=C1CaptureConfig(sensor_id="c1_2", frames=1, points_per_frame=4),
        )


def test_cli_capture_c1_uses_hex_fixture_without_serial(tmp_path):
    output = tmp_path / "capture.jsonl"

    path = capture_c1_recording(
        sensor_id="c1_2",
        output_path=output,
        frames=1,
        points_per_frame=4,
        read_chunk_size=5,
        max_empty_reads=2,
        baud_rate=460800,
        timeout_s=1.0,
        port=None,
        sample_hex=_fixture_bytes().hex(),
        overwrite=False,
    )

    assert path == output
    [record] = list(iter_lidar_scans(output))
    assert record.sensor_id == "c1_2"


def test_cli_capture_c1_subprocess_writes_recording_from_any_cwd(tmp_path):
    output = tmp_path / "capture.jsonl"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "rplidar_c1_tools.cli",
            "capture-c1",
            "--sensor-id",
            "c1_1",
            "--frames",
            "1",
            "--points-per-frame",
            "4",
            "--read-chunk-size",
            "5",
            "--sample-hex",
            _fixture_bytes().hex(),
            "--output",
            str(output),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    [record] = list(iter_lidar_scans(output))
    assert record.sensor_id == "c1_1"
    assert record.scan_frame.point_count == 4


def test_parse_sample_hex_accepts_whitespace_and_rejects_bad_input():
    assert parse_sample_hex("3d 01 00 a0 0f") == _node(0.0, 1000, quality=15, start=True)
    with pytest.raises(ValueError, match="even number"):
        parse_sample_hex("abc")
    with pytest.raises(ValueError, match="non-hexadecimal"):
        parse_sample_hex("zz")


def test_pyserial_transport_uses_explicit_port_and_can_be_faked(monkeypatch):
    writes: list[bytes] = []

    class FakeSerial:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.closed = False

        def write(self, payload: bytes) -> None:
            writes.append(payload)

        def read(self, size: int) -> bytes:
            return b"\x01"[:size]

        def close(self) -> None:
            self.closed = True

    fake_serial_module = types.SimpleNamespace(Serial=FakeSerial)
    monkeypatch.setitem(sys.modules, "serial", fake_serial_module)

    transport = PySerialByteTransport(port="COM_TEST_ONLY", baud_rate=460800, timeout_s=0.25)
    transport.connect()
    transport.write(b"abc")
    assert transport.read(1) == b"\x01"
    transport.disconnect()

    assert writes == [b"abc"]


def _fixture_bytes() -> bytes:
    return b"".join(
        [
            _node(0.0, 1000, quality=15, start=True),
            _node(90.0, 1000, quality=15),
            _node(180.0, 1000, quality=15),
            _node(270.0, 1000, quality=15),
        ]
    )


def _node(
    native_angle_deg: float,
    distance_mm: int,
    *,
    quality: int,
    start: bool = False,
) -> bytes:
    angle_q6 = int(round(native_angle_deg * 64.0))
    distance_q2 = distance_mm * 4
    sync_quality = (quality << 2) | (0x01 if start else 0x02)
    angle_low = ((angle_q6 & 0x7F) << 1) | 0x01
    angle_high = (angle_q6 >> 7) & 0xFF
    return bytes(
        [
            sync_quality,
            angle_low,
            angle_high,
            distance_q2 & 0xFF,
            (distance_q2 >> 8) & 0xFF,
        ]
    )
