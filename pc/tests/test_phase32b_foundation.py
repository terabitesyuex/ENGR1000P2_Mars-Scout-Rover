from __future__ import annotations

import math

from rplidar_c1_tools.openrf1_phase32b import (
    Bmp280Calibration,
    Bmp280RawSample,
    CooperativeScheduler,
    DigitalDebounceFilter,
    Hcsr04StateMachine,
    RingBuffer,
    ScheduledTask,
    bmp280_compensate,
    hcsr04_echo_us_to_distance_mm,
    mpu6050_accel_raw_to_mps2,
    mpu6050_gyro_raw_to_radps,
    mpu6050_temperature_raw_to_c,
)


def test_ring_buffer_wraparound_and_overflow_accounting():
    ring = RingBuffer(4)

    assert ring.push(1)
    assert ring.push(2)
    assert ring.push(3)
    assert not ring.push(4)
    assert ring.overflow_count == 1
    assert ring.read_chunk(2) == b"\x01\x02"
    assert ring.push(4)
    assert ring.push(5)
    assert ring.read_chunk(4) == b"\x03\x04\x05"
    assert ring.bytes_in == 5
    assert ring.bytes_out == 5


def test_bmp280_bosch_compensation_vector():
    calibration = Bmp280Calibration(
        dig_t1=27504,
        dig_t2=26435,
        dig_t3=-1000,
        dig_p1=36477,
        dig_p2=-10685,
        dig_p3=3024,
        dig_p4=2855,
        dig_p5=140,
        dig_p6=-7,
        dig_p7=15500,
        dig_p8=-14600,
        dig_p9=6000,
    )
    compensated = bmp280_compensate(
        calibration,
        Bmp280RawSample(adc_temperature=519888, adc_pressure=415148),
    )

    assert compensated.temperature_c == 25.08
    assert 100650 <= compensated.pressure_pa <= 100656


def test_mpu6050_raw_conversion_helpers_are_deterministic():
    assert math.isclose(mpu6050_accel_raw_to_mps2(16384, accel_range_g=2), 9.80665)
    assert math.isclose(mpu6050_gyro_raw_to_radps(131, gyro_range_dps=250), math.radians(1.0))
    assert math.isclose(mpu6050_temperature_raw_to_c(0), 36.53)


def test_debounce_retains_raw_and_counts_only_stable_transitions():
    debounce = DigitalDebounceFilter(stable_samples_required=3)

    assert not debounce.update(1, 10)
    assert not debounce.update(1, 20)
    assert debounce.raw_state == 1
    assert debounce.filtered_state == 0
    assert debounce.update(1, 30)
    assert debounce.filtered_state == 1
    assert debounce.transition_count == 1
    assert debounce.last_transition_ms == 30


def test_hcsr04_valid_pulse_timeout_and_quiet_period():
    channel = Hcsr04StateMachine("ultrasonic_1")

    assert channel.start(0)
    assert channel.poll(10) == "wait_rising"
    assert channel.echo_edge(high=True, now_us=20)
    assert channel.echo_edge(high=False, now_us=1020)
    assert channel.valid is True
    assert channel.raw_echo_us == 1000
    assert channel.distance_mm == hcsr04_echo_us_to_distance_mm(1000)
    assert channel.poll(6020) == "idle"

    assert channel.start(7000)
    assert channel.poll(7010) == "wait_rising"
    assert channel.poll(37010) == "timeout"
    assert channel.valid is False
    assert channel.distance_mm is None
    assert channel.timeout_count == 1


def test_scheduler_handles_u32_rollover_and_missing_sensor_tasks_keep_running():
    ran: list[tuple[str, int]] = []
    scheduler = CooperativeScheduler(
        (
            ScheduledTask("fast", 10, lambda now: ran.append(("fast", now)), next_run_ms=0xFFFFFFFE),
            ScheduledTask("disabled", 10, lambda now: ran.append(("disabled", now)), enabled=False),
        )
    )

    assert scheduler.service(0xFFFFFFFE) == ("fast",)
    assert scheduler.service(3) == ()
    assert scheduler.service(8) == ("fast",)
    assert [name for name, _now in ran] == ["fast", "fast"]
