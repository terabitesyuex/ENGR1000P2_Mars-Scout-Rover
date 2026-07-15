"""PC-direct RPLIDAR C1 driver boundary.

The driver is transport-injected so automated tests can use fake byte streams
without opening serial ports. Native C1 clockwise angles are converted before
`ScanPoint` creation.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Protocol

from .coordinate_transform import native_c1_angle_to_rover_deg
from .data_models import ScanFrame, ScanPoint
from .recorder import MultiSensorRecorder
from .recording_models import LIDAR_SENSOR_IDS, default_sensor_inventory
from .scan_builder import build_scan_frame, create_scan_point


C1_SCAN_COMMAND = bytes((0xA5, 0x20))
C1_STOP_COMMAND = bytes((0xA5, 0x25))
C1_STANDARD_SCAN_DESCRIPTOR = bytes((0xA5, 0x5A, 0x05, 0x00, 0x00, 0x40, 0x81))
DEFAULT_C1_BAUD_RATE = 460800


class C1DriverError(RuntimeError):
    """Base error for PC-direct C1 acquisition failures."""


class C1ProtocolError(C1DriverError):
    """Raised when decoded C1 sample data is invalid."""


class C1TimeoutError(C1DriverError):
    """Raised when no scan data arrives before the configured empty-read limit."""


class C1HardwareAccessError(C1DriverError):
    """Raised when live hardware access cannot be initialized."""


class C1ByteTransport(Protocol):
    """Minimal byte transport required by the PC-direct driver."""

    def connect(self) -> None:
        """Open the underlying transport."""

    def disconnect(self) -> None:
        """Close the underlying transport."""

    def write(self, payload: bytes) -> None:
        """Write command bytes."""

    def read(self, size: int) -> bytes:
        """Read up to `size` bytes, returning `b""` on timeout."""


@dataclass(frozen=True, slots=True)
class C1DecodedSample:
    """Decoded native C1 scan sample before rover-frame conversion."""

    native_angle_deg: float
    distance_mm: int
    quality: int | None
    timestamp_us: int
    scan_start: bool = False


@dataclass(frozen=True, slots=True)
class C1CaptureConfig:
    """Bounded capture settings for one PC-direct session."""

    sensor_id: str
    frames: int
    points_per_frame: int
    read_chunk_size: int = 64
    max_empty_reads: int = 10

    def validate(self) -> None:
        _validate_sensor_id(self.sensor_id)
        if self.frames <= 0:
            raise ValueError("frames must be positive")
        if self.points_per_frame <= 0:
            raise ValueError("points_per_frame must be positive")
        if self.read_chunk_size <= 0:
            raise ValueError("read_chunk_size must be positive")
        if self.max_empty_reads <= 0:
            raise ValueError("max_empty_reads must be positive")


class C1StandardScanParser:
    """Incremental parser for standard 5-byte RPLIDAR scan nodes."""

    NODE_SIZE = 5

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, chunk: bytes, *, timestamp_us: int) -> Iterator[C1DecodedSample]:
        """Feed arbitrary bytes and yield valid decoded samples."""
        if chunk:
            self._buffer.extend(chunk)
        while len(self._buffer) >= self.NODE_SIZE:
            if (
                len(self._buffer) < len(C1_STANDARD_SCAN_DESCRIPTOR)
                and C1_STANDARD_SCAN_DESCRIPTOR.startswith(self._buffer)
            ):
                break
            if self._buffer.startswith(C1_STANDARD_SCAN_DESCRIPTOR):
                del self._buffer[: len(C1_STANDARD_SCAN_DESCRIPTOR)]
                continue
            node = bytes(self._buffer[: self.NODE_SIZE])
            sample = _parse_standard_node(node, timestamp_us=timestamp_us)
            if sample is None:
                del self._buffer[0]
                continue
            del self._buffer[: self.NODE_SIZE]
            yield sample


class C1PcDirectDriver:
    """Convert C1 byte-stream samples into project `ScanPoint` objects."""

    def __init__(
        self,
        *,
        sensor_id: str,
        transport: C1ByteTransport,
        parser: C1StandardScanParser | None = None,
    ) -> None:
        _validate_sensor_id(sensor_id)
        self.sensor_id = sensor_id
        self._transport = transport
        self._parser = parser or C1StandardScanParser()
        self._connected = False
        self._scanning = False

    def connect(self) -> None:
        self._transport.connect()
        self._connected = True

    def disconnect(self) -> None:
        try:
            if self._connected and self._scanning:
                self.stop_scan()
        finally:
            self._transport.disconnect()
            self._connected = False
            self._scanning = False

    def start_scan(self) -> None:
        if not self._connected:
            raise C1DriverError("driver must be connected before start_scan")
        self._transport.write(C1_SCAN_COMMAND)
        self._scanning = True

    def stop_scan(self) -> None:
        if self._connected:
            self._transport.write(C1_STOP_COMMAND)
        self._scanning = False

    def iter_scan_points(
        self,
        *,
        read_chunk_size: int = 64,
        max_empty_reads: int = 10,
        timestamp_start_us: int = 0,
        timestamp_step_us: int = 1,
    ) -> Iterator[ScanPoint]:
        """Yield validated rover-frame scan points from the active scan stream."""
        if not self._scanning:
            raise C1DriverError("scan must be started before iter_scan_points")
        if read_chunk_size <= 0:
            raise ValueError("read_chunk_size must be positive")
        if max_empty_reads <= 0:
            raise ValueError("max_empty_reads must be positive")

        empty_reads = 0
        read_index = 0
        while True:
            chunk = self._transport.read(read_chunk_size)
            if not chunk:
                empty_reads += 1
                if empty_reads >= max_empty_reads:
                    raise C1TimeoutError("no C1 scan data received before timeout")
                continue
            empty_reads = 0
            timestamp_us = timestamp_start_us + read_index * timestamp_step_us
            read_index += 1
            for sample in self._parser.feed(chunk, timestamp_us=timestamp_us):
                yield decoded_sample_to_scan_point(sample)

    def capture_scan_frame(
        self,
        *,
        points_per_frame: int,
        frame_id: int,
        timestamp_us: int,
        read_chunk_size: int = 64,
        max_empty_reads: int = 10,
    ) -> ScanFrame:
        """Collect a bounded number of points into one `ScanFrame`."""
        if points_per_frame <= 0:
            raise ValueError("points_per_frame must be positive")
        points: list[ScanPoint] = []
        point_iter = self.iter_scan_points(
            read_chunk_size=read_chunk_size,
            max_empty_reads=max_empty_reads,
            timestamp_start_us=timestamp_us,
        )
        while len(points) < points_per_frame:
            points.append(next(point_iter))
        return build_scan_frame(
            points,
            timestamp_us=timestamp_us,
            frame_id=frame_id,
            source="pc_direct_c1",
            metadata={
                "sensor_id": self.sensor_id,
                "hardware_source": "pc_direct",
                "physical_test_required": True,
            },
        )


class BytesBufferTransport:
    """Deterministic byte transport used by tests and verifier smoke workflows."""

    def __init__(self, payload: bytes, *, repeat: bool = False) -> None:
        self._payload = payload
        self._offset = 0
        self._repeat = repeat
        self.connected = False
        self.writes: list[bytes] = []

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def write(self, payload: bytes) -> None:
        if not self.connected:
            raise C1DriverError("transport is not connected")
        self.writes.append(payload)

    def read(self, size: int) -> bytes:
        if not self.connected:
            raise C1DriverError("transport is not connected")
        if size <= 0:
            raise ValueError("size must be positive")
        if self._offset >= len(self._payload):
            if not self._repeat or not self._payload:
                return b""
            self._offset = 0
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


class PySerialByteTransport:
    """PySerial-backed transport for manual Phase 2.5 PC-direct use."""

    def __init__(
        self,
        *,
        port: str,
        baud_rate: int = DEFAULT_C1_BAUD_RATE,
        timeout_s: float = 1.0,
    ) -> None:
        if not port:
            raise ValueError("port must be provided explicitly")
        if baud_rate <= 0:
            raise ValueError("baud_rate must be positive")
        if timeout_s <= 0.0 or not math.isfinite(timeout_s):
            raise ValueError("timeout_s must be positive and finite")
        self.port = port
        self.baud_rate = baud_rate
        self.timeout_s = timeout_s
        self._serial: object | None = None

    def connect(self) -> None:
        try:
            import serial  # type: ignore[import-not-found]
        except ImportError as exc:
            raise C1HardwareAccessError("pyserial is required for live PC-direct capture") from exc
        self._serial = serial.Serial(
            port=self.port,
            baudrate=self.baud_rate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=self.timeout_s,
        )

    def disconnect(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    def write(self, payload: bytes) -> None:
        serial_obj = self._require_serial()
        serial_obj.write(payload)

    def read(self, size: int) -> bytes:
        serial_obj = self._require_serial()
        return bytes(serial_obj.read(size))

    def _require_serial(self):
        if self._serial is None:
            raise C1HardwareAccessError("serial port is not open")
        return self._serial


def decoded_sample_to_scan_point(sample: C1DecodedSample) -> ScanPoint:
    """Validate one decoded native sample and convert it to `ScanPoint`."""
    if not isinstance(sample, C1DecodedSample):
        raise C1ProtocolError("sample must be C1DecodedSample")
    if not math.isfinite(sample.native_angle_deg):
        raise C1ProtocolError("native_angle_deg must be finite")
    if not isinstance(sample.distance_mm, int) or sample.distance_mm <= 0:
        raise C1ProtocolError("distance_mm must be a positive integer")
    if sample.quality is not None and (
        not isinstance(sample.quality, int) or sample.quality < 0
    ):
        raise C1ProtocolError("quality must be a non-negative integer or None")
    rover_angle_deg = native_c1_angle_to_rover_deg(sample.native_angle_deg)
    return create_scan_point(
        angle_deg=rover_angle_deg,
        distance_mm=sample.distance_mm,
        quality=sample.quality,
    )


def capture_c1_session(
    *,
    driver: C1PcDirectDriver,
    output_path: Path | str,
    config: C1CaptureConfig,
    overwrite: bool = False,
) -> Path:
    """Capture bounded C1 frames and record them as Phase 2.4 JSONL."""
    config.validate()
    if config.sensor_id != driver.sensor_id:
        raise ValueError("config sensor_id must match driver sensor_id")
    output = Path(output_path)
    sensor_inventory = default_sensor_inventory(lidar_count=2, include_auxiliary=False)
    with MultiSensorRecorder(
        output,
        sensor_inventory=sensor_inventory,
        metadata={
            "generator": "rplidar_c1_tools.cli capture-c1",
            "source": "pc_direct_c1",
            "captured_sensor_id": config.sensor_id,
            "hardware_validation": "manual_required",
            "dual_c1_simultaneous": "not_attempted",
        },
        overwrite=overwrite,
    ) as recorder:
        try:
            driver.connect()
            driver.start_scan()
            for frame_id in range(config.frames):
                frame = driver.capture_scan_frame(
                    points_per_frame=config.points_per_frame,
                    frame_id=frame_id,
                    timestamp_us=frame_id * 100_000,
                    read_chunk_size=config.read_chunk_size,
                    max_empty_reads=config.max_empty_reads,
                )
                recorder.write_lidar_scan(config.sensor_id, frame)
        finally:
            driver.disconnect()
    return output


def parse_sample_hex(sample_hex: str) -> bytes:
    """Parse whitespace-tolerant hexadecimal fixture bytes."""
    compact = "".join(sample_hex.split())
    if len(compact) % 2 != 0:
        raise ValueError("sample hex must contain an even number of hex digits")
    try:
        return bytes.fromhex(compact)
    except ValueError as exc:
        raise ValueError("sample hex contains non-hexadecimal characters") from exc


def _parse_standard_node(node: bytes, *, timestamp_us: int) -> C1DecodedSample | None:
    if len(node) != C1StandardScanParser.NODE_SIZE:
        raise ValueError("standard node must be exactly 5 bytes")
    start_flag = bool(node[0] & 0x01)
    inverted_start_flag = bool(node[0] & 0x02)
    check_bit = node[1] & 0x01
    if start_flag == inverted_start_flag or check_bit != 1:
        return None

    quality = node[0] >> 2
    angle_q6 = ((node[2] << 7) | (node[1] >> 1))
    native_angle_deg = angle_q6 / 64.0
    distance_q2 = node[3] | (node[4] << 8)
    distance_mm = int(round(distance_q2 / 4.0))
    if distance_mm <= 0:
        return None
    return C1DecodedSample(
        native_angle_deg=native_angle_deg,
        distance_mm=distance_mm,
        quality=quality,
        timestamp_us=timestamp_us,
        scan_start=start_flag,
    )


def _validate_sensor_id(sensor_id: str) -> None:
    if sensor_id not in LIDAR_SENSOR_IDS:
        raise ValueError(f"sensor_id must be one of: {', '.join(LIDAR_SENSOR_IDS)}")
