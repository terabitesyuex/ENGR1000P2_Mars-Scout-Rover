"""Pure STM32-to-ESP32 frame codec for the Phase 3.2B software contract."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


MAGIC = b"\xA5\x5A"
VERSION = 1
HEADER_LENGTH = 14
CRC_LENGTH = 2
MAX_PAYLOAD_LENGTH = 256

MSG_HEARTBEAT = 1
MSG_COMMAND_ACK = 2
MSG_SUBSYSTEM_STATUS = 3
MSG_LINK_STATUS = 4
MSG_LIDAR_CHUNK = 5


class Esp32LinkCodecError(ValueError):
    """Raised for malformed Phase 3.2B ESP32 link frames."""


@dataclass(frozen=True, slots=True)
class Esp32LinkFrame:
    message_type: int
    sequence: int
    timestamp_ms: int
    payload: bytes = b""
    flags: int = 0
    version: int = VERSION

    def __post_init__(self) -> None:
        _require_u8(self.version, "version")
        _require_u8(self.message_type, "message_type")
        _require_u8(self.flags, "flags")
        _require_u16(self.sequence, "sequence")
        _require_u32(self.timestamp_ms, "timestamp_ms")
        if len(self.payload) > MAX_PAYLOAD_LENGTH:
            raise Esp32LinkCodecError("payload is too long")


@dataclass(frozen=True, slots=True)
class DecodeResult:
    frames: tuple[Esp32LinkFrame, ...]
    malformed_frames: int
    crc_errors: int
    dropped_bytes: int


def crc16_ccitt_false(data: bytes | bytearray | memoryview) -> int:
    """Return CRC-16/CCITT-FALSE, poly 0x1021, init 0xFFFF."""
    crc = 0xFFFF
    for value in bytes(data):
        crc ^= value << 8
        for _bit in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def encode_frame(frame: Esp32LinkFrame) -> bytes:
    """Encode one versioned binary frame with little-endian numeric fields."""
    header = bytearray()
    header.extend(MAGIC)
    header.append(frame.version)
    header.append(frame.message_type)
    header.append(frame.flags)
    header.append(0)
    header.extend(frame.sequence.to_bytes(2, "little"))
    header.extend(frame.timestamp_ms.to_bytes(4, "little"))
    header.extend(len(frame.payload).to_bytes(2, "little"))
    crc_region = bytes(header[2:]) + frame.payload
    crc = crc16_ccitt_false(crc_region)
    return bytes(header) + frame.payload + crc.to_bytes(2, "little")


class Esp32FrameDecoder:
    """Streaming decoder with magic resynchronization and CRC accounting."""

    def __init__(self, *, max_payload_length: int = MAX_PAYLOAD_LENGTH) -> None:
        if max_payload_length <= 0 or max_payload_length > MAX_PAYLOAD_LENGTH:
            raise Esp32LinkCodecError("max_payload_length is invalid")
        self.max_payload_length = max_payload_length
        self._buffer = bytearray()
        self.malformed_frames = 0
        self.crc_errors = 0
        self.dropped_bytes = 0

    def feed(self, data: bytes | bytearray | memoryview | Iterable[int]) -> tuple[Esp32LinkFrame, ...]:
        self._buffer.extend(bytes(data))
        frames: list[Esp32LinkFrame] = []
        while True:
            start = self._buffer.find(MAGIC)
            if start < 0:
                self.dropped_bytes += len(self._buffer)
                self._buffer.clear()
                break
            if start > 0:
                self.dropped_bytes += start
                del self._buffer[:start]
            if len(self._buffer) < HEADER_LENGTH:
                break
            payload_length = int.from_bytes(self._buffer[12:14], "little")
            if payload_length > self.max_payload_length:
                self.malformed_frames += 1
                del self._buffer[0]
                continue
            frame_length = HEADER_LENGTH + payload_length + CRC_LENGTH
            if len(self._buffer) < frame_length:
                break
            raw = bytes(self._buffer[:frame_length])
            expected_crc = int.from_bytes(raw[-CRC_LENGTH:], "little")
            actual_crc = crc16_ccitt_false(raw[2:-CRC_LENGTH])
            if actual_crc != expected_crc:
                self.crc_errors += 1
                del self._buffer[0]
                continue
            version = raw[2]
            if version != VERSION:
                self.malformed_frames += 1
                del self._buffer[:frame_length]
                continue
            frames.append(
                Esp32LinkFrame(
                    version=version,
                    message_type=raw[3],
                    flags=raw[4],
                    sequence=int.from_bytes(raw[6:8], "little"),
                    timestamp_ms=int.from_bytes(raw[8:12], "little"),
                    payload=raw[HEADER_LENGTH:-CRC_LENGTH],
                )
            )
            del self._buffer[:frame_length]
        return tuple(frames)

    def result(self, frames: Iterable[Esp32LinkFrame] = ()) -> DecodeResult:
        return DecodeResult(
            frames=tuple(frames),
            malformed_frames=self.malformed_frames,
            crc_errors=self.crc_errors,
            dropped_bytes=self.dropped_bytes,
        )


def detect_sequence_gaps(frames: Iterable[Esp32LinkFrame]) -> int:
    """Count sequence discontinuities in decode order."""
    previous: int | None = None
    gaps = 0
    for frame in frames:
        if previous is not None and frame.sequence != ((previous + 1) & 0xFFFF):
            gaps += 1
        previous = frame.sequence
    return gaps


def _require_u8(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xFF:
        raise Esp32LinkCodecError(f"{name} must be an unsigned byte")


def _require_u16(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xFFFF:
        raise Esp32LinkCodecError(f"{name} must be an unsigned 16-bit integer")


def _require_u32(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFF:
        raise Esp32LinkCodecError(f"{name} must be an unsigned 32-bit integer")
