"""Host-testable OpenRF1 BH1750 logic for Phase 3.2A."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .stm32_sensor_models import Stm32TelemetryMessage
from .stm32_sensor_protocol import encode_stm32_telemetry_message


OPENRF1_BOARD_NAME = "OpenRF1"
OPENRF1_MCU = "STM32F103RCT6"
OPENRF1_BH1750_SENSOR_ID = "bh1750_1"
OPENRF1_BH1750_ADDRESS_7BIT = 0x23
OPENRF1_BH1750_MEASUREMENT_TIME_MS = 180
OPENRF1_BH1750_PERIOD_MS = 500
OPENRF1_BH1750_RETRY_BACKOFF_MS = 1000
BH1750_ONE_TIME_HIGH_RESOLUTION_MODE = 0x20


class OpenRf1Bh1750Error(ValueError):
    """Raised for invalid OpenRF1/BH1750 software inputs."""


@dataclass(frozen=True, slots=True)
class OpenRf1BoardConfig:
    """OpenRF1 constants used by firmware and PC-side tests."""

    board_name: str = OPENRF1_BOARD_NAME
    mcu: str = OPENRF1_MCU
    sensor_id: str = OPENRF1_BH1750_SENSOR_ID
    scl_port: str = "GPIOB"
    scl_pin: str = "GPIO_Pin_1"
    sda_port: str = "GPIOC"
    sda_pin: str = "GPIO_Pin_3"
    bh1750_address_7bit: int = OPENRF1_BH1750_ADDRESS_7BIT
    uart: str = "USART1"
    uart_tx_pin: str = "PA9"
    uart_rx_pin: str = "PA10"
    uart_baud: int = 115200
    uart_data_bits: int = 8
    uart_parity: str = "none"
    uart_stop_bits: int = 1


@dataclass(frozen=True, slots=True)
class Bh1750Sample:
    """One host-testable BH1750 state-machine output sample."""

    timestamp_ms: int
    status: str
    illuminance_centilux: int | None

    @property
    def illuminance_lux(self) -> float | None:
        if self.illuminance_centilux is None:
            return None
        return self.illuminance_centilux / 100.0


class Bh1750Controller:
    """Small nonblocking BH1750 measurement state machine.

    The callbacks are intentionally dependency-injected so tests do not touch
    I2C, GPIO, USB, or serial devices.
    """

    def __init__(
        self,
        *,
        measurement_time_ms: int = OPENRF1_BH1750_MEASUREMENT_TIME_MS,
        period_ms: int = OPENRF1_BH1750_PERIOD_MS,
        retry_backoff_ms: int = OPENRF1_BH1750_RETRY_BACKOFF_MS,
    ) -> None:
        if measurement_time_ms <= 0:
            raise OpenRf1Bh1750Error("measurement_time_ms must be positive")
        if period_ms < measurement_time_ms:
            raise OpenRf1Bh1750Error("period_ms must be at least measurement_time_ms")
        if retry_backoff_ms <= 0:
            raise OpenRf1Bh1750Error("retry_backoff_ms must be positive")
        self.measurement_time_ms = measurement_time_ms
        self.period_ms = period_ms
        self.retry_backoff_ms = retry_backoff_ms
        self.state = "START_MEASUREMENT"
        self.next_action_ms = 0

    def step(
        self,
        now_ms: int,
        *,
        start_measurement: Callable[[], str],
        read_raw_count: Callable[[], tuple[str, int | None]],
    ) -> Bh1750Sample | None:
        """Advance the state machine without long measurement busy-waiting."""
        _require_non_negative_int(now_ms, "now_ms")
        if now_ms < self.next_action_ms:
            return None

        if self.state == "START_MEASUREMENT":
            status = start_measurement()
            if status == "ok":
                self.state = "WAIT_MEASUREMENT"
                self.next_action_ms = now_ms + self.measurement_time_ms
                return None
            self.state = "RETRY_BACKOFF"
            self.next_action_ms = now_ms + self.retry_backoff_ms
            return Bh1750Sample(now_ms, _normal_error_status(status), None)

        if self.state == "WAIT_MEASUREMENT":
            self.state = "READ_MEASUREMENT"

        if self.state == "READ_MEASUREMENT":
            status, raw_count = read_raw_count()
            if status == "ok":
                if raw_count is None:
                    raise OpenRf1Bh1750Error("raw_count is required when status is ok")
                centilux = bh1750_raw_count_to_centilux(raw_count)
                self.state = "START_MEASUREMENT"
                self.next_action_ms = now_ms + max(0, self.period_ms - self.measurement_time_ms)
                return Bh1750Sample(now_ms, "ok", centilux)
            self.state = "RETRY_BACKOFF"
            self.next_action_ms = now_ms + self.retry_backoff_ms
            return Bh1750Sample(now_ms, _normal_error_status(status), None)

        if self.state == "RETRY_BACKOFF":
            self.state = "START_MEASUREMENT"
            return None

        raise OpenRf1Bh1750Error(f"unknown controller state: {self.state}")


def bh1750_write_address_byte(address_7bit: int = OPENRF1_BH1750_ADDRESS_7BIT) -> int:
    """Return the internal write byte derived from the public 7-bit address."""
    return _address_byte(address_7bit, read=False)


def bh1750_read_address_byte(address_7bit: int = OPENRF1_BH1750_ADDRESS_7BIT) -> int:
    """Return the internal read byte derived from the public 7-bit address."""
    return _address_byte(address_7bit, read=True)


def bh1750_raw_count_from_bytes(msb: int, lsb: int) -> int:
    """Combine BH1750 MSB/LSB result bytes into a 16-bit raw count."""
    _require_byte(msb, "msb")
    _require_byte(lsb, "lsb")
    return (msb << 8) | lsb


def bh1750_raw_count_to_centilux(raw_count: int) -> int:
    """Convert raw BH1750 counts to centi-lux using lux = raw / 1.2."""
    _require_raw_count(raw_count)
    return (raw_count * 250 + 1) // 3


def bh1750_raw_count_to_lux(raw_count: int) -> float:
    """Convert raw BH1750 counts to lux without using sentinel error values."""
    return bh1750_raw_count_to_centilux(raw_count) / 100.0


def format_bh1750_telemetry_line(
    *,
    sequence: int,
    timestamp_ms: int,
    status: str,
    illuminance_centilux: int | None,
) -> str:
    """Return one Phase 3.1-compatible BH1750 telemetry JSON line."""
    _require_non_negative_int(sequence, "sequence")
    _require_non_negative_int(timestamp_ms, "timestamp_ms")
    if illuminance_centilux is not None:
        _require_non_negative_int(illuminance_centilux, "illuminance_centilux")
    payload: dict[str, object] = {
        "illuminance_lux": None if illuminance_centilux is None else illuminance_centilux / 100.0
    }
    message = Stm32TelemetryMessage(
        sequence=sequence,
        timestamp_ms=timestamp_ms,
        message_type="illuminance",
        sensor_id=OPENRF1_BH1750_SENSOR_ID,
        payload=payload,
        status=status,
    )
    return encode_stm32_telemetry_message(message)


def generate_bh1750_telemetry_lines(
    *,
    samples: int = 5,
    start_timestamp_ms: int = 0,
    interval_ms: int = OPENRF1_BH1750_PERIOD_MS,
) -> tuple[str, ...]:
    """Generate deterministic BH1750-only telemetry for verifier smoke tests."""
    if samples <= 0:
        raise OpenRf1Bh1750Error("samples must be positive")
    if interval_ms <= 0:
        raise OpenRf1Bh1750Error("interval_ms must be positive")
    _require_non_negative_int(start_timestamp_ms, "start_timestamp_ms")
    lines: list[str] = []
    for index in range(samples):
        centilux = 12_000 + index * 725
        lines.append(
            format_bh1750_telemetry_line(
                sequence=index,
                timestamp_ms=start_timestamp_ms + index * interval_ms,
                status="simulated",
                illuminance_centilux=centilux,
            )
        )
    return tuple(lines)


def _address_byte(address_7bit: int, *, read: bool) -> int:
    if isinstance(address_7bit, bool) or not isinstance(address_7bit, int):
        raise OpenRf1Bh1750Error("address_7bit must be an integer")
    if not 0 <= address_7bit <= 0x7F:
        raise OpenRf1Bh1750Error("address_7bit must fit in 7 bits")
    return (address_7bit << 1) | (1 if read else 0)


def _require_byte(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xFF:
        raise OpenRf1Bh1750Error(f"{name} must be a byte")


def _require_raw_count(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xFFFF:
        raise OpenRf1Bh1750Error("raw_count must be a 16-bit unsigned integer")


def _require_non_negative_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise OpenRf1Bh1750Error(f"{name} must be a non-negative integer")


def _normal_error_status(status: str) -> str:
    if status in {"timeout", "not_initialized", "hardware_fault", "stale"}:
        return status
    if status == "ok":
        raise OpenRf1Bh1750Error("ok is not an error status")
    return "hardware_fault"
