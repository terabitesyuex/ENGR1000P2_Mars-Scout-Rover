"""Deterministic Phase 3.1 STM32 sensor telemetry simulator."""

from __future__ import annotations

from collections.abc import Iterable

from .stm32_sensor_models import Stm32TelemetryMessage
from .stm32_sensor_protocol import encode_stm32_telemetry_message


STM32_SIMULATOR_SCENARIOS = (
    "nominal",
    "ultrasonic_timeout",
    "ground_polarity_unverified",
    "hall_polarity_unverified",
    "environment_change",
    "mixed_faults",
)


def generate_synthetic_stm32_session(
    *,
    cycles: int = 1,
    start_timestamp_ms: int = 0,
    interval_ms: int = 100,
    scenario: str = "nominal",
) -> tuple[Stm32TelemetryMessage, ...]:
    """Return deterministic low-rate STM32 telemetry messages."""
    if cycles <= 0:
        raise ValueError("cycles must be positive")
    if start_timestamp_ms < 0:
        raise ValueError("start_timestamp_ms must be non-negative")
    if interval_ms <= 0:
        raise ValueError("interval_ms must be positive")
    if scenario not in STM32_SIMULATOR_SCENARIOS:
        raise ValueError(f"scenario must be one of: {', '.join(STM32_SIMULATOR_SCENARIOS)}")

    messages: list[Stm32TelemetryMessage] = []
    sequence = 0
    for cycle in range(cycles):
        timestamp_ms = start_timestamp_ms + cycle * interval_ms
        for message_type, sensor_id, payload, status in _cycle_samples(cycle, scenario):
            messages.append(
                Stm32TelemetryMessage(
                    sequence=sequence,
                    timestamp_ms=timestamp_ms,
                    message_type=message_type,
                    sensor_id=sensor_id,
                    payload=payload,
                    status=status,
                )
            )
            sequence += 1
    return tuple(messages)


def generate_synthetic_stm32_lines(
    *,
    cycles: int = 1,
    start_timestamp_ms: int = 0,
    interval_ms: int = 100,
    scenario: str = "nominal",
) -> tuple[str, ...]:
    """Return deterministic JSON lines for the synthetic session."""
    return tuple(
        encode_stm32_telemetry_message(message)
        for message in generate_synthetic_stm32_session(
            cycles=cycles,
            start_timestamp_ms=start_timestamp_ms,
            interval_ms=interval_ms,
            scenario=scenario,
        )
    )


def _cycle_samples(
    cycle: int,
    scenario: str,
) -> Iterable[tuple[str, str, dict[str, object], str]]:
    ultrasonic_distances = (450 + cycle * 5, 650 + cycle * 5, 850 + cycle * 5)
    for index, distance_mm in enumerate(ultrasonic_distances, start=1):
        status = "simulated"
        payload: dict[str, object] = {
            "distance_mm": distance_mm,
            "raw_echo_us": 1200 + index * 100 + cycle,
            "valid": True,
        }
        if scenario in {"ultrasonic_timeout", "mixed_faults"} and index == 2 and cycle == 0:
            status = "timeout"
            payload = {"raw_echo_us": None, "valid": False}
        yield ("ultrasonic", f"ultrasonic_{index}", payload, status)

    for index, raw_state in enumerate((cycle % 2, (cycle + 1) % 2), start=1):
        polarity_verified = scenario not in {"ground_polarity_unverified", "mixed_faults"}
        yield (
            "ground_edge",
            f"tcrt5000_{index}",
            {
                "raw_state": raw_state,
                "polarity_verified": polarity_verified,
                "interpreted_edge_detected": bool(raw_state) if polarity_verified else None,
            },
            "simulated",
        )

    hall_polarity_verified = scenario not in {"hall_polarity_unverified", "mixed_faults"}
    hall_raw_state = 1 if cycle % 3 == 0 else 0
    yield (
        "hall_landmark",
        "hall_1",
        {
            "raw_state": hall_raw_state,
            "polarity_verified": hall_polarity_verified,
            "interpreted_landmark_detected": (
                bool(hall_raw_state) if hall_polarity_verified else None
            ),
        },
        "simulated",
    )

    lux = 320.0 + cycle * (15.0 if scenario == "environment_change" else 1.0)
    if scenario == "mixed_faults" and cycle == 0:
        yield ("illuminance", "bh1750_1", {"illuminance_lux": None}, "not_initialized")
    else:
        yield ("illuminance", "bh1750_1", {"illuminance_lux": lux}, "simulated")

    pressure_delta = cycle * (25.0 if scenario == "environment_change" else 1.0)
    yield (
        "barometer",
        "bmp280_1",
        {
            "temperature_c": 24.0 + cycle * 0.1,
            "pressure_pa": 101_325.0 - pressure_delta,
        },
        "simulated",
    )

