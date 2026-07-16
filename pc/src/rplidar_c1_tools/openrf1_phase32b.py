"""Pure Phase 3.2B foundations shared by tests and documentation."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Callable


G_MPS2 = 9.80665
BMP280_EXPECTED_CHIP_ID = 0x58
MPU6050_EXPECTED_WHO_AM_I = 0x68


class Phase32BError(ValueError):
    """Raised for invalid Phase 3.2B pure-logic inputs."""


class RingBuffer:
    """Bounded power-of-two byte ring buffer with overflow accounting."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 1 or capacity & (capacity - 1):
            raise Phase32BError("capacity must be a power of two greater than one")
        self.capacity = capacity
        self._storage = bytearray(capacity)
        self._head = 0
        self._tail = 0
        self.bytes_in = 0
        self.bytes_out = 0
        self.overflow_count = 0

    @property
    def available(self) -> int:
        return (self._head - self._tail) & (self.capacity - 1)

    @property
    def free(self) -> int:
        return self.capacity - 1 - self.available

    def push(self, value: int) -> bool:
        if not 0 <= value <= 0xFF:
            raise Phase32BError("value must be a byte")
        next_head = (self._head + 1) & (self.capacity - 1)
        if next_head == self._tail:
            self.overflow_count += 1
            return False
        self._storage[self._head] = value
        self._head = next_head
        self.bytes_in += 1
        return True

    def pop(self) -> int | None:
        if self._tail == self._head:
            return None
        value = self._storage[self._tail]
        self._tail = (self._tail + 1) & (self.capacity - 1)
        self.bytes_out += 1
        return value

    def read_chunk(self, max_length: int) -> bytes:
        if max_length < 0:
            raise Phase32BError("max_length must be non-negative")
        values = bytearray()
        while len(values) < max_length:
            value = self.pop()
            if value is None:
                break
            values.append(value)
        return bytes(values)


@dataclass(frozen=True, slots=True)
class Bmp280Calibration:
    dig_t1: int
    dig_t2: int
    dig_t3: int
    dig_p1: int
    dig_p2: int
    dig_p3: int
    dig_p4: int
    dig_p5: int
    dig_p6: int
    dig_p7: int
    dig_p8: int
    dig_p9: int


@dataclass(frozen=True, slots=True)
class Bmp280RawSample:
    adc_temperature: int
    adc_pressure: int


@dataclass(frozen=True, slots=True)
class Bmp280CompensatedSample:
    temperature_c: float
    pressure_pa: int
    t_fine: int


def bmp280_compensate(
    calibration: Bmp280Calibration,
    raw: Bmp280RawSample,
) -> Bmp280CompensatedSample:
    """Bosch integer BMP280 compensation, returning pascals and deg C."""
    if calibration.dig_p1 == 0:
        raise Phase32BError("dig_p1 must not be zero")
    var1 = (((raw.adc_temperature >> 3) - (calibration.dig_t1 << 1)) * calibration.dig_t2) >> 11
    var2 = (((((raw.adc_temperature >> 4) - calibration.dig_t1) ** 2) >> 12) * calibration.dig_t3) >> 14
    t_fine = var1 + var2
    temperature_centideg_c = (t_fine * 5 + 128) >> 8

    p_var1 = t_fine - 128000
    p_var2 = p_var1 * p_var1 * calibration.dig_p6
    p_var2 += (p_var1 * calibration.dig_p5) << 17
    p_var2 += calibration.dig_p4 << 35
    p_var1 = ((p_var1 * p_var1 * calibration.dig_p3) >> 8) + ((p_var1 * calibration.dig_p2) << 12)
    p_var1 = (((1 << 47) + p_var1) * calibration.dig_p1) >> 33
    if p_var1 == 0:
        raise Phase32BError("pressure compensation divisor became zero")
    pressure = 1048576 - raw.adc_pressure
    pressure = (((pressure << 31) - p_var2) * 3125) // p_var1
    p_var1 = (calibration.dig_p9 * (pressure >> 13) * (pressure >> 13)) >> 25
    p_var2 = (calibration.dig_p8 * pressure) >> 19
    pressure = ((pressure + p_var1 + p_var2) >> 8) + (calibration.dig_p7 << 4)
    return Bmp280CompensatedSample(
        temperature_c=temperature_centideg_c / 100.0,
        pressure_pa=(pressure + 128) >> 8,
        t_fine=t_fine,
    )


@dataclass(frozen=True, slots=True)
class Mpu6050RawSample:
    accel_x_raw: int
    accel_y_raw: int
    accel_z_raw: int
    gyro_x_raw: int
    gyro_y_raw: int
    gyro_z_raw: int
    temperature_raw: int


def mpu6050_accel_raw_to_mps2(raw: int, *, accel_range_g: int = 2) -> float:
    lsb_per_g = {2: 16384, 4: 8192, 8: 4096, 16: 2048}
    if accel_range_g not in lsb_per_g:
        raise Phase32BError("accel_range_g must be 2, 4, 8, or 16")
    return raw / lsb_per_g[accel_range_g] * G_MPS2


def mpu6050_gyro_raw_to_radps(raw: int, *, gyro_range_dps: int = 250) -> float:
    lsb_per_dps = {250: 131.0, 500: 65.5, 1000: 32.8, 2000: 16.4}
    if gyro_range_dps not in lsb_per_dps:
        raise Phase32BError("gyro_range_dps must be 250, 500, 1000, or 2000")
    return raw / lsb_per_dps[gyro_range_dps] * (pi / 180.0)


def mpu6050_temperature_raw_to_c(raw: int) -> float:
    return raw / 340.0 + 36.53


@dataclass(slots=True)
class DigitalDebounceFilter:
    stable_samples_required: int = 3
    raw_state: int = 0
    filtered_state: int = 0
    candidate_state: int = 0
    candidate_count: int = 0
    last_transition_ms: int = 0
    transition_count: int = 0

    def update(self, raw_state: int, now_ms: int) -> bool:
        raw = 1 if raw_state else 0
        self.raw_state = raw
        if raw == self.filtered_state:
            self.candidate_state = raw
            self.candidate_count = 0
            return False
        if raw != self.candidate_state:
            self.candidate_state = raw
            self.candidate_count = 1
            return False
        self.candidate_count += 1
        if self.candidate_count >= self.stable_samples_required:
            self.filtered_state = raw
            self.last_transition_ms = now_ms
            self.transition_count += 1
            self.candidate_count = 0
            return True
        return False


@dataclass(slots=True)
class Hcsr04StateMachine:
    sensor_id: str
    state: str = "idle"
    state_started_us: int = 0
    echo_rise_us: int | None = None
    raw_echo_us: int | None = None
    distance_mm: int | None = None
    valid: bool = False
    timeout_count: int = 0
    trigger_us: int = 10
    timeout_us: int = 30000
    quiet_time_us: int = 5000

    def start(self, now_us: int) -> bool:
        if self.state != "idle":
            return False
        self.state = "trigger_high"
        self.state_started_us = now_us
        self.echo_rise_us = None
        self.raw_echo_us = None
        self.distance_mm = None
        self.valid = False
        return True

    def poll(self, now_us: int) -> str | None:
        elapsed = now_us - self.state_started_us
        if self.state == "trigger_high" and elapsed >= self.trigger_us:
            self.state = "wait_rising"
            self.state_started_us = now_us
            return "wait_rising"
        if self.state in {"wait_rising", "wait_falling"} and elapsed >= self.timeout_us:
            self.state = "quiet"
            self.state_started_us = now_us
            self.timeout_count += 1
            self.valid = False
            self.raw_echo_us = None
            self.distance_mm = None
            return "timeout"
        if self.state == "quiet" and elapsed >= self.quiet_time_us:
            self.state = "idle"
            return "idle"
        return None

    def echo_edge(self, *, high: bool, now_us: int) -> bool:
        if self.state == "wait_rising" and high:
            self.echo_rise_us = now_us
            self.state = "wait_falling"
            self.state_started_us = now_us
            return True
        if self.state == "wait_falling" and not high and self.echo_rise_us is not None:
            self.raw_echo_us = now_us - self.echo_rise_us
            self.distance_mm = hcsr04_echo_us_to_distance_mm(self.raw_echo_us)
            self.valid = True
            self.state = "quiet"
            self.state_started_us = now_us
            return True
        return False


def hcsr04_echo_us_to_distance_mm(echo_us: int) -> int:
    if echo_us < 0:
        raise Phase32BError("echo_us must be non-negative")
    return (echo_us * 343 + 1000) // 2000


@dataclass(slots=True)
class ScheduledTask:
    name: str
    period_ms: int
    callback: Callable[[int], None]
    next_run_ms: int = 0
    enabled: bool = True
    run_count: int = 0


class CooperativeScheduler:
    def __init__(self, tasks: tuple[ScheduledTask, ...]) -> None:
        self.tasks = tasks

    def service(self, now_ms: int) -> tuple[str, ...]:
        ran: list[str] = []
        for task in self.tasks:
            if task.enabled and _u32_due(now_ms, task.next_run_ms):
                task.callback(now_ms)
                task.next_run_ms = (now_ms + task.period_ms) & 0xFFFFFFFF
                task.run_count += 1
                ran.append(task.name)
        return tuple(ran)


def _u32_due(now: int, deadline: int) -> bool:
    return ((now - deadline) & 0xFFFFFFFF) < 0x80000000
