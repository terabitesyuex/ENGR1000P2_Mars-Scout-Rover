"""Command-line entry points for PC-side tools."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .mecanum_odometry import EncoderConfiguration, MecanumGeometry
from .mecanum_odometry_simulator import (
    MECANUM_ODOMETRY_SCENARIOS,
    generate_mecanum_odometry_telemetry_lines,
)
from .motion_control import (
    FourWheelPIDConfiguration,
    MotionControlConfiguration,
    MotionSafetyPolicy,
    PIDGains,
    PIDLimits,
    WheelAccelerationLimits,
    WheelSpeedLimits,
)
from .motion_control_simulator import (
    MOTION_CONTROL_SCENARIOS,
    SyntheticWheelPlantParameters,
    SyntheticWheelPlantWheelParameters,
    generate_motion_control_telemetry_lines,
)
from .c1_pc_direct import (
    C1CaptureConfig,
    C1DriverError,
    C1PcDirectDriver,
    BytesBufferTransport,
    PySerialByteTransport,
    capture_c1_session,
    parse_sample_hex,
)
from .point_cloud_view import save_point_cloud_view
from .polar_view import save_polar_view
from .recorder import MultiSensorRecorder
from .recording_models import (
    BarometerSample,
    GroundEdgeSample,
    HallLandmarkSample,
    IlluminanceSample,
    ImuSample,
    RoverPose,
    UltrasonicSample,
    default_sensor_inventory,
)
from .replay import RecordingFormatError, inspect_recording, last_lidar_scan_by_sensor, replay_lidar_scans
from .openrf1_bh1750 import generate_bh1750_telemetry_lines
from .stm32_recording_bridge import record_stm32_telemetry_stream
from .stm32_serial_capture import (
    DEFAULT_LINE_LENGTH_LIMIT_BYTES,
    DEFAULT_MAX_CONSECUTIVE_MALFORMED_LINES,
    DEFAULT_STARTUP_GRACE_S,
    DEFAULT_STM32_SERIAL_BAUD,
    FileChunkSerialReader,
    PySerialLineReader,
    Stm32SerialCaptureError,
    capture_stm32_serial_telemetry,
)
from .stm32_sensor_protocol import (
    Stm32TelemetryError,
    iter_stm32_telemetry,
)
from .stm32_sensor_simulator import (
    STM32_SIMULATOR_SCENARIOS,
    generate_synthetic_stm32_lines,
)
from .synthetic_scan import SyntheticRoomConfig, SyntheticScanSource, scan_to_json
from .synthetic_scan import generate_circle_scan, generate_room_scan


def main() -> int:
    parser = argparse.ArgumentParser(prog="rplidar-c1")
    subparsers = parser.add_subparsers(dest="command", required=True)

    synthetic = subparsers.add_parser(
        "synthetic-room",
        help="Generate deterministic synthetic scans without LiDAR hardware.",
    )
    synthetic.add_argument("--scans", type=int, default=1)
    synthetic.add_argument("--angle-step-deg", type=float, default=1.0)
    synthetic.add_argument("--room-length-mm", type=int, default=6000)
    synthetic.add_argument("--room-width-mm", type=int, default=4000)

    render = subparsers.add_parser(
        "render-synthetic",
        help="Render deterministic synthetic scan visualizations as PNG files.",
    )
    render.add_argument(
        "--scene",
        choices=("circle", "room", "both"),
        default="both",
        help="Synthetic scene to render.",
    )
    render.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".verification") / "phase2.3_visuals",
    )
    show_group = render.add_mutually_exclusive_group()
    show_group.add_argument(
        "--show",
        action="store_true",
        help="Display figures interactively after export.",
    )
    show_group.add_argument(
        "--no-show",
        action="store_false",
        dest="show",
        help="Do not display figures after export.",
    )
    render.set_defaults(show=False)

    record = subparsers.add_parser(
        "record-synthetic",
        help="Write a deterministic Phase 2.4 multi-sensor JSONL recording.",
    )
    record.add_argument("--scene", choices=("circle", "room"), default="room")
    record.add_argument("--output", type=Path, required=True)
    record.add_argument("--frames", type=_positive_int, default=3)
    record.add_argument("--lidar-count", type=int, choices=(1, 2), default=1)
    record.add_argument("--point-count", type=_positive_int, default=360)
    record.add_argument("--include-aux", action="store_true")
    record.add_argument("--overwrite", action="store_true")

    inspect = subparsers.add_parser(
        "inspect-recording",
        help="Inspect a Phase 2.4 JSONL recording without loading scan geometry.",
    )
    inspect.add_argument("recording", type=Path)
    inspect.add_argument("--output", type=Path)

    replay = subparsers.add_parser(
        "replay-recording",
        help="Replay recorded LiDAR scans immediately by default.",
    )
    replay.add_argument("recording", type=Path)
    replay.add_argument("--sensor-id")
    replay.add_argument("--limit", type=_positive_int)
    replay.add_argument("--timed", action="store_true")
    replay.add_argument("--speed", type=float, default=1.0)
    replay.add_argument("--output", type=Path)

    render_recording = subparsers.add_parser(
        "render-recording",
        help="Render final replayed LiDAR frames as polar and point-cloud PNGs.",
    )
    render_recording.add_argument("recording", type=Path)
    render_recording.add_argument("--sensor-id", action="append", dest="sensor_ids")
    render_recording.add_argument("--output-dir", type=Path, required=True)

    capture_c1 = subparsers.add_parser(
        "capture-c1",
        help="Capture a bounded PC-direct C1 scan session into JSONL.",
    )
    capture_c1.add_argument("--sensor-id", choices=("c1_1", "c1_2"), required=True)
    capture_c1.add_argument("--output", type=Path, required=True)
    capture_c1.add_argument("--frames", type=_positive_int, default=1)
    capture_c1.add_argument("--points-per-frame", type=_positive_int, default=360)
    capture_c1.add_argument("--read-chunk-size", type=_positive_int, default=64)
    capture_c1.add_argument("--max-empty-reads", type=_positive_int, default=10)
    capture_c1.add_argument("--baud-rate", type=_positive_int, default=460800)
    capture_c1.add_argument("--timeout-s", type=float, default=1.0)
    capture_c1.add_argument("--overwrite", action="store_true")
    source_group = capture_c1.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--port",
        help="Explicit serial port for manual PC-direct hardware capture.",
    )
    source_group.add_argument(
        "--sample-hex",
        help="Hex fixture bytes for automated tests and verifier smoke workflows.",
    )

    simulate_stm32 = subparsers.add_parser(
        "simulate-stm32-sensors",
        help="Generate deterministic Phase 3.1 STM32 sensor telemetry JSONL.",
        description="Generate deterministic Phase 3.1 STM32 sensor telemetry JSONL.",
    )
    simulate_stm32.add_argument("--cycles", type=_positive_int, default=1)
    simulate_stm32.add_argument(
        "--scenario",
        choices=STM32_SIMULATOR_SCENARIOS,
        default="nominal",
    )
    simulate_stm32.add_argument("--start-timestamp-ms", type=_non_negative_int, default=0)
    simulate_stm32.add_argument("--interval-ms", type=_positive_int, default=100)
    simulate_stm32.add_argument("--output", type=Path, required=True)
    simulate_stm32.add_argument("--overwrite", action="store_true")

    simulate_mecanum = subparsers.add_parser(
        "simulate-mecanum-odometry",
        help="Generate deterministic Phase 4A mecanum odometry telemetry JSONL.",
        description=(
            "Generate hardware-free Phase 4A telemetry. Geometry, wheel-side encoder "
            "resolution, and every raw encoder direction sign must be explicit."
        ),
    )
    simulate_mecanum.add_argument("--wheel-radius-m", type=float, required=True)
    simulate_mecanum.add_argument("--half-length-m", type=float, required=True)
    simulate_mecanum.add_argument("--half-width-m", type=float, required=True)
    simulate_mecanum.add_argument(
        "--counts-per-wheel-revolution",
        type=float,
        required=True,
        help="Wheel-side counts per full wheel revolution; no gear ratio is inferred.",
    )
    simulate_mecanum.add_argument(
        "--front-left-direction",
        type=_direction_multiplier,
        required=True,
    )
    simulate_mecanum.add_argument(
        "--front-right-direction",
        type=_direction_multiplier,
        required=True,
    )
    simulate_mecanum.add_argument(
        "--rear-left-direction",
        type=_direction_multiplier,
        required=True,
    )
    simulate_mecanum.add_argument(
        "--rear-right-direction",
        type=_direction_multiplier,
        required=True,
    )
    simulate_mecanum.add_argument("--counter-width-bits", type=_positive_int)
    simulate_mecanum.add_argument(
        "--scenario",
        choices=MECANUM_ODOMETRY_SCENARIOS,
        required=True,
    )
    simulate_mecanum.add_argument("--steps", type=_positive_int, required=True)
    simulate_mecanum.add_argument("--interval-ms", type=_positive_int, required=True)
    simulate_mecanum.add_argument("--start-timestamp-ms", type=_non_negative_int, default=0)
    simulate_mecanum.add_argument("--output", type=Path, required=True)
    simulate_mecanum.add_argument("--overwrite", action="store_true")

    simulate_motion = subparsers.add_parser(
        "simulate-motion-control",
        help="Generate deterministic Phase 4B closed-loop control telemetry JSONL.",
        description=(
            "Run the hardware-free Phase 4B command-shaping, safety, PID, and "
            "SYNTHETIC first-order wheel-plant pipeline. All parameters are test "
            "inputs, not rover measurements or tuning values."
        ),
    )
    simulate_motion.add_argument("--wheel-radius-m", type=float, required=True)
    simulate_motion.add_argument("--half-length-m", type=float, required=True)
    simulate_motion.add_argument("--half-width-m", type=float, required=True)
    simulate_motion.add_argument("--max-wheel-speed-rad-s", type=float, required=True)
    simulate_motion.add_argument(
        "--wheel-acceleration-rad-s2",
        type=float,
        required=True,
    )
    simulate_motion.add_argument("--pid-kp", type=float, required=True)
    simulate_motion.add_argument("--pid-ki", type=float, required=True)
    simulate_motion.add_argument("--pid-kd", type=float, required=True)
    simulate_motion.add_argument("--pid-output-min", type=float, required=True)
    simulate_motion.add_argument("--pid-output-max", type=float, required=True)
    simulate_motion.add_argument("--pid-integral-min", type=float, required=True)
    simulate_motion.add_argument("--pid-integral-max", type=float, required=True)
    simulate_motion.add_argument(
        "--plant-gain-rad-s-per-effort",
        type=float,
        required=True,
        help="Explicit SYNTHETIC steady wheel speed per normalized effort.",
    )
    simulate_motion.add_argument(
        "--plant-time-constant-s",
        type=float,
        required=True,
        help="Explicit SYNTHETIC shared first-order time constant.",
    )
    simulate_motion.add_argument(
        "--slow-front-left-time-constant-s",
        type=float,
        help=(
            "Required only for slow_front_left_wheel; explicit SYNTHETIC mismatch."
        ),
    )
    simulate_motion.add_argument(
        "--command-timeout-ms",
        type=_positive_int,
        required=True,
    )
    simulate_motion.add_argument(
        "--scenario",
        choices=MOTION_CONTROL_SCENARIOS,
        required=True,
    )
    simulate_motion.add_argument("--steps", type=_positive_int, required=True)
    simulate_motion.add_argument("--interval-ms", type=_positive_int, required=True)
    simulate_motion.add_argument(
        "--start-timestamp-ms",
        type=_non_negative_int,
        default=0,
    )
    simulate_motion.add_argument("--output", type=Path, required=True)
    simulate_motion.add_argument("--overwrite", action="store_true")

    inspect_stm32 = subparsers.add_parser(
        "inspect-stm32-telemetry",
        help="Validate and summarize STM32 sensor telemetry JSONL.",
    )
    inspect_stm32.add_argument("--input", type=Path, required=True)
    inspect_stm32.add_argument("--output", type=Path)

    record_stm32 = subparsers.add_parser(
        "record-stm32-telemetry",
        help="Convert STM32 telemetry JSONL into the Phase 2.4 recording format.",
    )
    record_stm32.add_argument("--input", type=Path, required=True)
    record_stm32.add_argument("--output", type=Path, required=True)
    record_stm32.add_argument("--overwrite", action="store_true")

    simulate_bh1750 = subparsers.add_parser(
        "simulate-bh1750-telemetry",
        help="Generate deterministic OpenRF1 BH1750-only telemetry JSONL.",
    )
    simulate_bh1750.add_argument("--samples", type=_positive_int, default=5)
    simulate_bh1750.add_argument("--start-timestamp-ms", type=_non_negative_int, default=0)
    simulate_bh1750.add_argument("--interval-ms", type=_positive_int, default=500)
    simulate_bh1750.add_argument("--output", type=Path, required=True)
    simulate_bh1750.add_argument("--overwrite", action="store_true")

    capture_stm32 = subparsers.add_parser(
        "capture-stm32-serial",
        help="Capture user-selected STM32 BH1750 serial telemetry into JSONL.",
    )
    capture_source = capture_stm32.add_mutually_exclusive_group(required=True)
    capture_source.add_argument("--port", help="Explicit user-verified COM port for manual capture.")
    capture_source.add_argument(
        "--mock-input",
        type=Path,
        help="File-backed mock byte source for tests and verifier smoke runs.",
    )
    capture_stm32.add_argument("--baud", type=_positive_int, default=DEFAULT_STM32_SERIAL_BAUD)
    capture_stm32.add_argument("--duration", type=float, default=30.0)
    capture_stm32.add_argument("--max-messages", type=_positive_int)
    capture_stm32.add_argument("--timeout-s", type=float, default=1.0)
    capture_stm32.add_argument("--read-chunk-size", type=_positive_int, default=64)
    capture_stm32.add_argument("--max-empty-reads", type=_positive_int, default=10)
    capture_stm32.add_argument("--startup-grace-s", type=float, default=DEFAULT_STARTUP_GRACE_S)
    capture_stm32.add_argument(
        "--max-consecutive-malformed-lines",
        type=_positive_int,
        default=DEFAULT_MAX_CONSECUTIVE_MALFORMED_LINES,
    )
    capture_stm32.add_argument(
        "--line-length-limit",
        type=_positive_int,
        default=DEFAULT_LINE_LENGTH_LIMIT_BYTES,
    )
    capture_stm32.add_argument("--telemetry-output", type=Path, required=True)
    capture_stm32.add_argument("--recording-output", type=Path, required=True)
    capture_stm32.add_argument("--overwrite", action="store_true")

    args = parser.parse_args()
    try:
        if args.command == "synthetic-room":
            config = SyntheticRoomConfig(
                scan_count=args.scans,
                angle_step_deg=args.angle_step_deg,
                room_length_mm=args.room_length_mm,
                room_width_mm=args.room_width_mm,
            )
            for scan in SyntheticScanSource(config).scans():
                print(scan_to_json(scan))
            return 0
        if args.command == "render-synthetic":
            paths = render_synthetic(
                scene=args.scene,
                output_dir=args.output_dir,
                show=args.show,
            )
            for path in paths:
                print(path)
            return 0
        if args.command == "record-synthetic":
            path = record_synthetic_session(
                output_path=args.output,
                scene=args.scene,
                frames=args.frames,
                lidar_count=args.lidar_count,
                point_count=args.point_count,
                include_auxiliary=args.include_aux,
                overwrite=args.overwrite,
            )
            print(path)
            return 0
        if args.command == "inspect-recording":
            text = inspect_recording(args.recording).to_text()
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(text, encoding="utf-8")
            print(text, end="")
            return 0
        if args.command == "replay-recording":
            text = replay_recording_text(
                args.recording,
                sensor_id=args.sensor_id,
                limit=args.limit,
                timed=args.timed,
                speed=args.speed,
            )
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(text, encoding="utf-8")
            print(text, end="")
            return 0
        if args.command == "render-recording":
            paths = render_recording_last_frames(
                args.recording,
                output_dir=args.output_dir,
                sensor_ids=tuple(args.sensor_ids or ()),
            )
            for path in paths:
                print(path)
            return 0
        if args.command == "capture-c1":
            path = capture_c1_recording(
                sensor_id=args.sensor_id,
                output_path=args.output,
                frames=args.frames,
                points_per_frame=args.points_per_frame,
                read_chunk_size=args.read_chunk_size,
                max_empty_reads=args.max_empty_reads,
                baud_rate=args.baud_rate,
                timeout_s=args.timeout_s,
                port=args.port,
                sample_hex=args.sample_hex,
                overwrite=args.overwrite,
            )
            print(path)
            return 0
        if args.command == "simulate-stm32-sensors":
            path = simulate_stm32_sensor_telemetry(
                output_path=args.output,
                cycles=args.cycles,
                scenario=args.scenario,
                start_timestamp_ms=args.start_timestamp_ms,
                interval_ms=args.interval_ms,
                overwrite=args.overwrite,
            )
            print(path)
            return 0
        if args.command == "simulate-mecanum-odometry":
            path = simulate_mecanum_odometry(
                output_path=args.output,
                geometry=MecanumGeometry(
                    wheel_radius_m=args.wheel_radius_m,
                    half_length_m=args.half_length_m,
                    half_width_m=args.half_width_m,
                ),
                encoder_configuration=EncoderConfiguration(
                    counts_per_wheel_revolution=args.counts_per_wheel_revolution,
                    front_left_direction=args.front_left_direction,
                    front_right_direction=args.front_right_direction,
                    rear_left_direction=args.rear_left_direction,
                    rear_right_direction=args.rear_right_direction,
                    counter_width_bits=args.counter_width_bits,
                ),
                scenario=args.scenario,
                step_count=args.steps,
                interval_ms=args.interval_ms,
                start_timestamp_ms=args.start_timestamp_ms,
                overwrite=args.overwrite,
            )
            print(path)
            return 0
        if args.command == "simulate-motion-control":
            path = simulate_motion_control(
                output_path=args.output,
                geometry=MecanumGeometry(
                    wheel_radius_m=args.wheel_radius_m,
                    half_length_m=args.half_length_m,
                    half_width_m=args.half_width_m,
                ),
                wheel_speed_limits=WheelSpeedLimits(args.max_wheel_speed_rad_s),
                wheel_acceleration_limits=WheelAccelerationLimits.shared(
                    args.wheel_acceleration_rad_s2
                ),
                gains=PIDGains(args.pid_kp, args.pid_ki, args.pid_kd),
                limits=PIDLimits(
                    output_min=args.pid_output_min,
                    output_max=args.pid_output_max,
                    integral_min=args.pid_integral_min,
                    integral_max=args.pid_integral_max,
                ),
                plant_gain_rad_s_per_effort=args.plant_gain_rad_s_per_effort,
                plant_time_constant_s=args.plant_time_constant_s,
                slow_front_left_time_constant_s=(
                    args.slow_front_left_time_constant_s
                ),
                command_timeout_ms=args.command_timeout_ms,
                scenario=args.scenario,
                step_count=args.steps,
                interval_ms=args.interval_ms,
                start_timestamp_ms=args.start_timestamp_ms,
                overwrite=args.overwrite,
            )
            print(
                f"wrote Phase 4B synthetic motion-control telemetry: {path}"
            )
            return 0
        if args.command == "inspect-stm32-telemetry":
            text = inspect_stm32_telemetry_file(args.input)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(text, encoding="utf-8")
            print(text, end="")
            return 0
        if args.command == "record-stm32-telemetry":
            path = record_stm32_telemetry_file(
                input_path=args.input,
                output_path=args.output,
                overwrite=args.overwrite,
            )
            print(path)
            return 0
        if args.command == "simulate-bh1750-telemetry":
            path = simulate_bh1750_telemetry(
                output_path=args.output,
                samples=args.samples,
                start_timestamp_ms=args.start_timestamp_ms,
                interval_ms=args.interval_ms,
                overwrite=args.overwrite,
            )
            print(path)
            return 0
        if args.command == "capture-stm32-serial":
            text = capture_stm32_serial_file(
                port=args.port,
                mock_input=args.mock_input,
                baud=args.baud,
                duration_s=args.duration,
                max_messages=args.max_messages,
                timeout_s=args.timeout_s,
                read_chunk_size=args.read_chunk_size,
                max_empty_reads=args.max_empty_reads,
                startup_grace_s=args.startup_grace_s,
                max_consecutive_malformed_lines=args.max_consecutive_malformed_lines,
                line_length_limit_bytes=args.line_length_limit,
                telemetry_output=args.telemetry_output,
                recording_output=args.recording_output,
                overwrite=args.overwrite,
            )
            print(text, end="")
            return 0
    except (
        OSError,
        ValueError,
        RecordingFormatError,
        C1DriverError,
        Stm32TelemetryError,
        Stm32SerialCaptureError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    parser.error(f"unsupported command: {args.command}")
    return 2


def render_synthetic(scene: str, output_dir: Path, show: bool = False) -> list[Path]:
    """Render deterministic synthetic visualizations and return output paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    scenes = _selected_scenes(scene)
    paths: list[Path] = []
    for scene_name in scenes:
        scan = _scan_for_scene(scene_name)
        paths.append(
            save_polar_view(
                scan,
                output_dir / f"{scene_name}_polar.png",
                title=f"Synthetic {scene_name} polar scan",
            )
        )
        paths.append(
            save_point_cloud_view(
                scan,
                output_dir / f"{scene_name}_point_cloud.png",
                title=f"Synthetic {scene_name} Cartesian point cloud",
            )
        )
    if show:
        from matplotlib import pyplot as plt

        for scene_name in scenes:
            scan = _scan_for_scene(scene_name)
            from .point_cloud_view import create_point_cloud_figure
            from .polar_view import create_polar_figure

            create_polar_figure(scan, title=f"Synthetic {scene_name} polar scan")
            create_point_cloud_figure(
                scan,
                title=f"Synthetic {scene_name} Cartesian point cloud",
            )
        plt.show()
    return paths


def record_synthetic_session(
    *,
    output_path: Path,
    scene: str,
    frames: int,
    lidar_count: int,
    point_count: int,
    include_auxiliary: bool,
    overwrite: bool,
) -> Path:
    """Create a deterministic software-only multi-sensor recording."""
    if frames <= 0:
        raise ValueError("frames must be positive")
    if lidar_count not in (1, 2):
        raise ValueError("lidar_count must be 1 or 2")
    sensor_inventory = default_sensor_inventory(
        lidar_count=lidar_count,
        include_auxiliary=include_auxiliary,
    )
    lidar_ids = ("c1_1", "c1_2")[:lidar_count]
    with MultiSensorRecorder(
        output_path,
        sensor_inventory=sensor_inventory,
        metadata={
            "generator": "rplidar_c1_tools.cli record-synthetic",
            "scene": scene,
            "hardware_access": "none",
        },
        overwrite=overwrite,
    ) as recorder:
        for frame_id in range(frames):
            timestamp_us = frame_id * 100_000
            pose = _synthetic_pose(timestamp_us, frame_id) if include_auxiliary else None
            for sensor_id in lidar_ids:
                scan = _scan_for_scene(
                    scene,
                    point_count=point_count,
                    timestamp_us=timestamp_us,
                    frame_id=frame_id,
                )
                recorder.write_lidar_scan(sensor_id, scan, pose=pose)
            if include_auxiliary and pose is not None:
                _write_synthetic_auxiliary(recorder, timestamp_us, frame_id, pose)
    return output_path


def replay_recording_text(
    recording_path: Path,
    *,
    sensor_id: str | None = None,
    limit: int | None = None,
    timed: bool = False,
    speed: float = 1.0,
) -> str:
    """Return compact text for replayed LiDAR scans."""
    lines: list[str] = []
    count = 0
    for record in replay_lidar_scans(
        recording_path,
        sensor_id=sensor_id,
        timed=timed,
        speed=speed,
    ):
        lines.append(
            "sensor_id={0} sequence={1} timestamp_us={2} points={3}".format(
                record.sensor_id,
                record.sequence,
                record.scan_frame.timestamp_us,
                record.scan_frame.point_count,
            )
        )
        count += 1
        if limit is not None and count >= limit:
            break
    lines.append(f"replayed_lidar_scans={count}")
    return "\n".join(lines) + "\n"


def render_recording_last_frames(
    recording_path: Path,
    *,
    output_dir: Path,
    sensor_ids: tuple[str, ...] = (),
) -> list[Path]:
    """Render final recorded LiDAR frame for each selected sensor."""
    output_dir.mkdir(parents=True, exist_ok=True)
    records = last_lidar_scan_by_sensor(recording_path, sensor_ids=sensor_ids or None)
    if not records:
        raise ValueError("recording contains no matching LiDAR scans")
    paths: list[Path] = []
    for sensor_id in sorted(records):
        frame = records[sensor_id].scan_frame
        paths.append(
            save_polar_view(
                frame,
                output_dir / f"{sensor_id}_last_polar.png",
                title=f"{sensor_id} replayed polar scan",
            )
        )
        paths.append(
            save_point_cloud_view(
                frame,
                output_dir / f"{sensor_id}_last_point_cloud.png",
                title=f"{sensor_id} replayed point cloud",
            )
        )
    return paths


def capture_c1_recording(
    *,
    sensor_id: str,
    output_path: Path,
    frames: int,
    points_per_frame: int,
    read_chunk_size: int,
    max_empty_reads: int,
    baud_rate: int,
    timeout_s: float,
    port: str | None,
    sample_hex: str | None,
    overwrite: bool,
) -> Path:
    """Capture C1 data using either live serial or a deterministic fixture."""
    if sample_hex is not None:
        transport = BytesBufferTransport(parse_sample_hex(sample_hex))
    elif port is not None:
        transport = PySerialByteTransport(
            port=port,
            baud_rate=baud_rate,
            timeout_s=timeout_s,
        )
    else:
        raise ValueError("provide either --port or --sample-hex")
    driver = C1PcDirectDriver(sensor_id=sensor_id, transport=transport)
    return capture_c1_session(
        driver=driver,
        output_path=output_path,
        config=C1CaptureConfig(
            sensor_id=sensor_id,
            frames=frames,
            points_per_frame=points_per_frame,
            read_chunk_size=read_chunk_size,
            max_empty_reads=max_empty_reads,
        ),
        overwrite=overwrite,
    )


def simulate_stm32_sensor_telemetry(
    *,
    output_path: Path,
    cycles: int,
    scenario: str,
    start_timestamp_ms: int,
    interval_ms: int,
    overwrite: bool,
) -> Path:
    """Write deterministic STM32 telemetry fixture lines."""
    if output_path.exists() and not overwrite:
        raise ValueError(f"telemetry output already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = generate_synthetic_stm32_lines(
        cycles=cycles,
        scenario=scenario,
        start_timestamp_ms=start_timestamp_ms,
        interval_ms=interval_ms,
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return output_path


def simulate_mecanum_odometry(
    *,
    output_path: Path,
    geometry: MecanumGeometry,
    encoder_configuration: EncoderConfiguration,
    scenario: str,
    step_count: int,
    interval_ms: int,
    start_timestamp_ms: int,
    overwrite: bool,
) -> Path:
    """Write deterministic software-only Phase 4A telemetry fixture lines."""
    if output_path.exists() and not overwrite:
        raise ValueError(f"telemetry output already exists: {output_path}")
    lines = generate_mecanum_odometry_telemetry_lines(
        geometry=geometry,
        encoder_configuration=encoder_configuration,
        scenario=scenario,
        step_count=step_count,
        interval_ms=interval_ms,
        start_timestamp_ms=start_timestamp_ms,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return output_path


def simulate_motion_control(
    *,
    output_path: Path,
    geometry: MecanumGeometry,
    wheel_speed_limits: WheelSpeedLimits,
    wheel_acceleration_limits: WheelAccelerationLimits,
    gains: PIDGains,
    limits: PIDLimits,
    plant_gain_rad_s_per_effort: float,
    plant_time_constant_s: float,
    slow_front_left_time_constant_s: float | None,
    command_timeout_ms: int,
    scenario: str,
    step_count: int,
    interval_ms: int,
    start_timestamp_ms: int,
    overwrite: bool,
) -> Path:
    """Write deterministic software-only Phase 4B telemetry fixture lines."""
    if output_path.exists() and not overwrite:
        raise ValueError(f"telemetry output already exists: {output_path}")
    if scenario == "slow_front_left_wheel" and slow_front_left_time_constant_s is None:
        raise ValueError(
            "slow_front_left_wheel requires --slow-front-left-time-constant-s"
        )
    shared_plant = SyntheticWheelPlantWheelParameters(
        gain_rad_s_per_normalized_effort=plant_gain_rad_s_per_effort,
        time_constant_s=plant_time_constant_s,
    )
    front_left_plant = (
        SyntheticWheelPlantWheelParameters(
            gain_rad_s_per_normalized_effort=plant_gain_rad_s_per_effort,
            time_constant_s=slow_front_left_time_constant_s,
        )
        if scenario == "slow_front_left_wheel"
        else shared_plant
    )
    plant = SyntheticWheelPlantParameters(
        front_left=front_left_plant,
        front_right=shared_plant,
        rear_left=shared_plant,
        rear_right=shared_plant,
    )
    configuration = MotionControlConfiguration(
        geometry=geometry,
        wheel_speed_limits=wheel_speed_limits,
        wheel_acceleration_limits=wheel_acceleration_limits,
        wheel_pid=FourWheelPIDConfiguration.shared(gains, limits),
        safety_policy=MotionSafetyPolicy(command_timeout_ms=command_timeout_ms),
    )
    lines = generate_motion_control_telemetry_lines(
        configuration=configuration,
        plant_parameters=plant,
        scenario=scenario,
        step_count=step_count,
        interval_ms=interval_ms,
        start_timestamp_ms=start_timestamp_ms,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return output_path


def inspect_stm32_telemetry_file(input_path: Path) -> str:
    """Return a compact validation summary for STM32 telemetry JSONL."""
    counts: dict[str, int] = {}
    sensors: set[str] = set()
    first_timestamp_ms: int | None = None
    last_timestamp_ms: int | None = None
    total = 0
    with input_path.open("r", encoding="utf-8") as stream:
        for message in iter_stm32_telemetry(stream):
            total += 1
            counts[message.message_type] = counts.get(message.message_type, 0) + 1
            sensors.add(message.sensor_id)
            if first_timestamp_ms is None:
                first_timestamp_ms = message.timestamp_ms
            last_timestamp_ms = message.timestamp_ms
    lines = [
        f"path: {input_path}",
        "protocol: mars_scout_stm32_sensor_telemetry v1",
        f"messages: {total}",
        f"sensors: {', '.join(sorted(sensors))}",
        "message_counts:",
    ]
    for message_type, count in sorted(counts.items()):
        lines.append(f"  {message_type}: {count}")
    lines.append(f"first_timestamp_ms: {first_timestamp_ms}")
    lines.append(f"last_timestamp_ms: {last_timestamp_ms}")
    return "\n".join(lines) + "\n"


def record_stm32_telemetry_file(
    *,
    input_path: Path,
    output_path: Path,
    overwrite: bool,
) -> Path:
    """Convert STM32 telemetry JSONL to the existing multi-sensor recording format."""
    with input_path.open("r", encoding="utf-8") as stream:
        return record_stm32_telemetry_stream(
            stream,
            output_path=output_path,
            overwrite=overwrite,
        )


def simulate_bh1750_telemetry(
    *,
    output_path: Path,
    samples: int,
    start_timestamp_ms: int,
    interval_ms: int,
    overwrite: bool,
) -> Path:
    """Write deterministic OpenRF1 BH1750-only telemetry fixture lines."""
    if output_path.exists() and not overwrite:
        raise ValueError(f"telemetry output already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = generate_bh1750_telemetry_lines(
        samples=samples,
        start_timestamp_ms=start_timestamp_ms,
        interval_ms=interval_ms,
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return output_path


def capture_stm32_serial_file(
    *,
    port: str | None,
    mock_input: Path | None,
    baud: int,
    duration_s: float,
    max_messages: int | None,
    timeout_s: float,
    read_chunk_size: int,
    max_empty_reads: int,
    startup_grace_s: float,
    max_consecutive_malformed_lines: int,
    line_length_limit_bytes: int,
    telemetry_output: Path,
    recording_output: Path,
    overwrite: bool,
) -> str:
    """Capture OpenRF1 BH1750 serial telemetry from a live or mocked source."""
    if mock_input is not None:
        reader = FileChunkSerialReader(mock_input, chunk_size=max(1, read_chunk_size // 2))
    elif port is not None:
        reader = PySerialLineReader(port=port, baud=baud, timeout_s=timeout_s)
    else:
        raise ValueError("provide either --port or --mock-input")
    summary = capture_stm32_serial_telemetry(
        reader=reader,
        telemetry_output=telemetry_output,
        recording_output=recording_output,
        duration_s=duration_s,
        max_messages=max_messages,
        read_chunk_size=read_chunk_size,
        max_empty_reads=max_empty_reads,
        startup_grace_s=startup_grace_s,
        max_consecutive_malformed_lines=max_consecutive_malformed_lines,
        line_length_limit_bytes=line_length_limit_bytes,
        overwrite=overwrite,
    )
    return summary.to_text()


def _selected_scenes(scene: str) -> tuple[str, ...]:
    if scene == "both":
        return ("circle", "room")
    if scene in {"circle", "room"}:
        return (scene,)
    raise ValueError("scene must be one of: circle, room, both")


def _scan_for_scene(
    scene: str,
    *,
    point_count: int = 360,
    timestamp_us: int = 0,
    frame_id: int | None = 0,
):
    if scene == "circle":
        return generate_circle_scan(
            point_count=point_count,
            radius_mm=2000,
            timestamp_us=timestamp_us,
            frame_id=frame_id,
        )
    if scene == "room":
        return generate_room_scan(
            point_count=point_count,
            room_length_mm=6000,
            room_width_mm=4000,
            timestamp_us=timestamp_us,
            frame_id=frame_id,
        )
    raise ValueError("scene must be one of: circle, room, both")


def _synthetic_pose(timestamp_us: int, frame_id: int) -> RoverPose:
    return RoverPose(
        timestamp_us=timestamp_us,
        x_m=frame_id * 0.05,
        y_m=0.0,
        yaw_rad=frame_id * 0.01,
    )


def _write_synthetic_auxiliary(
    recorder: MultiSensorRecorder,
    timestamp_us: int,
    frame_id: int,
    pose: RoverPose,
) -> None:
    recorder.write_rover_pose(pose)
    recorder.write_imu_sample(
        ImuSample(
            timestamp_us=timestamp_us,
            accel_x_mps2=0.0,
            accel_y_mps2=0.0,
            accel_z_mps2=9.80665,
            gyro_x_radps=0.0,
            gyro_y_radps=0.0,
            gyro_z_radps=0.01 * frame_id,
            temperature_c=24.0,
        )
    )
    for index, distance_mm in enumerate((600, 700, 800), start=1):
        recorder.write_ultrasonic_sample(
            UltrasonicSample(
                timestamp_us=timestamp_us,
                sensor_id=f"ultrasonic_{index}",
                distance_mm=distance_mm + frame_id,
            )
        )
    for index in (1, 2):
        recorder.write_ground_edge_sample(
            GroundEdgeSample(
                timestamp_us=timestamp_us,
                sensor_id=f"tcrt5000_{index}",
                edge_detected=False,
                reflectance_raw=700 + index,
            )
        )
    recorder.write_hall_landmark_sample(
        HallLandmarkSample(
            timestamp_us=timestamp_us,
            detected=(frame_id % 3 == 0),
            raw_value=1 if frame_id % 3 == 0 else 0,
        )
    )
    recorder.write_illuminance_sample(
        IlluminanceSample(
            timestamp_us=timestamp_us,
            illuminance_lux=320.0 + frame_id,
        )
    )
    recorder.write_barometer_sample(
        BarometerSample(
            timestamp_us=timestamp_us,
            temperature_c=24.0 + frame_id * 0.1,
            pressure_pa=101_325.0 - frame_id,
        )
    )


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be a non-negative integer")
    return parsed


def _direction_multiplier(value: str) -> int:
    parsed = int(value)
    if parsed not in (-1, 1):
        raise argparse.ArgumentTypeError("value must be +1 or -1")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
