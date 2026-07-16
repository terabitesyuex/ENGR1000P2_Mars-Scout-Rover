from __future__ import annotations

from rplidar_c1_tools.esp32_link_codec import (
    MSG_HEARTBEAT,
    MSG_LIDAR_CHUNK,
    Esp32FrameDecoder,
    Esp32LinkFrame,
    crc16_ccitt_false,
    detect_sequence_gaps,
    encode_frame,
)


def test_crc16_ccitt_false_known_check_value():
    assert crc16_ccitt_false(b"123456789") == 0x29B1


def test_encode_frame_matches_phase32b_golden_vector():
    frame = Esp32LinkFrame(
        message_type=MSG_HEARTBEAT,
        sequence=0x1234,
        timestamp_ms=0x01020304,
        payload=b"OK",
    )

    assert encode_frame(frame).hex() == "a55a0101000034120403020102004f4b94fd"


def test_decoder_recovers_from_noise_malformed_length_and_crc_failure():
    good = encode_frame(Esp32LinkFrame(message_type=MSG_LIDAR_CHUNK, sequence=1, timestamp_ms=10, payload=b"abc"))
    bad_crc = bytearray(good)
    bad_crc[-1] ^= 0x55
    malformed = b"\xa5\x5a\x01\x01\x00\x00\x02\x00\x00\x00\x00\x00\xff\x7f"
    decoder = Esp32FrameDecoder()

    frames = decoder.feed(b"noise" + malformed + bytes(bad_crc) + good)

    assert frames == (Esp32LinkFrame(message_type=MSG_LIDAR_CHUNK, sequence=1, timestamp_ms=10, payload=b"abc"),)
    assert decoder.dropped_bytes >= len("noise")
    assert decoder.malformed_frames >= 1
    assert decoder.crc_errors >= 1


def test_sequence_gap_detection_allows_u16_rollover():
    frames = (
        Esp32LinkFrame(message_type=MSG_HEARTBEAT, sequence=0xFFFE, timestamp_ms=0),
        Esp32LinkFrame(message_type=MSG_HEARTBEAT, sequence=0xFFFF, timestamp_ms=1),
        Esp32LinkFrame(message_type=MSG_HEARTBEAT, sequence=0, timestamp_ms=2),
        Esp32LinkFrame(message_type=MSG_HEARTBEAT, sequence=2, timestamp_ms=3),
    )

    assert detect_sequence_gaps(frames) == 1
