#!/usr/bin/env python3
"""Benchmark script for FPS and latency testing."""

import logging
import sys
import time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dual_eye_tracker.capture.camera_worker import CameraWorker
from dual_eye_tracker.processing.detector import PupilDetector
from dual_eye_tracker.utils.fps_estimator import FPSEstimator
from dual_eye_tracker.utils.profiler import SimpleProfiler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_benchmark(config: dict, duration_sec: float = 5.0, warmup_sec: float = 2.0) -> int:
    """
    Run headless FPS benchmark.

    Args:
        config: Configuration dictionary.
        duration_sec: Benchmark duration after warmup.
        warmup_sec: Warmup period.

    Returns:
        Exit code (0 = success, non-zero if performance insufficient).
    """
    cam_cfg = config["cameras"]
    proc_cfg = config["processing"]

    logger.info(f"Benchmark: {cam_cfg['fps']} FPS target, {duration_sec}s duration")

    # Create components
    left_cam = CameraWorker(
        camera_id=cam_cfg["left_id"],
        width=cam_cfg["width"],
        height=cam_cfg["height"],
        fps=cam_cfg["fps"],
        exposure_us=cam_cfg.get("exposure_us"),
        backend=cam_cfg.get("backend", "dshow"),
        pixel_format=cam_cfg.get("pixel_format", "YUY2"),
    )

    detector = PupilDetector(
        eyelid_exclusion_pct=proc_cfg["eyelid_exclusion_pct"],
        lash_kernel_length=proc_cfg["lash_kernel_length"],
        lash_kernel_thickness=proc_cfg["lash_kernel_thickness"],
        min_area=proc_cfg["min_area"],
        max_area=proc_cfg["max_area"],
        min_circularity=proc_cfg["min_circularity"],
        max_eccentricity=proc_cfg["max_eccentricity"],
        min_ring_contrast=proc_cfg["min_ring_contrast"],
    )

    fps_est = FPSEstimator()
    profiler = SimpleProfiler()

    # Start camera
    if not left_cam.start():
        logger.error("Failed to start camera")
        return 1

    logger.info(f"Warming up for {warmup_sec}s...")
    warmup_end = time.perf_counter() + warmup_sec

    # Warmup phase
    while time.perf_counter() < warmup_end:
        frame_data = left_cam.get_frame()
        if frame_data is not None:
            _, frame = frame_data
            detector.detect(frame)

    # Reset counters
    fps_est.reset()
    profiler.reset()

    logger.info(f"Benchmarking for {duration_sec}s...")
    bench_start = time.perf_counter()
    bench_end = bench_start + duration_sec
    frame_count = 0
    detect_ok_count = 0

    # Benchmark phase
    while time.perf_counter() < bench_end:
        frame_data = left_cam.get_frame()
        if frame_data is None:
            continue

        _, frame = frame_data
        fps_est.tick()

        profiler.start("detect")
        result = detector.detect(frame)
        profiler.stop("detect")

        frame_count += 1
        if result.ok:
            detect_ok_count += 1

    actual_duration = time.perf_counter() - bench_start
    left_cam.stop()

    # Calculate metrics
    measured_fps = frame_count / actual_duration
    target_fps = cam_cfg["fps"]
    fps_ratio = measured_fps / target_fps
    detect_rate = detect_ok_count / frame_count if frame_count > 0 else 0

    # Report
    logger.info("=" * 60)
    logger.info("BENCHMARK RESULTS")
    logger.info("=" * 60)
    logger.info(f"Target FPS:      {target_fps:.1f}")
    logger.info(f"Measured FPS:    {measured_fps:.1f}")
    logger.info(f"FPS Ratio:       {fps_ratio:.1%}")
    logger.info(f"Frames:          {frame_count}")
    logger.info(f"Detection Rate:  {detect_rate:.1%}")
    logger.info("")
    logger.info(profiler.report())
    logger.info("=" * 60)

    # Camera stats
    stats = left_cam.get_stats()
    logger.info(f"Camera stats: {stats}")

    # Pass/fail criteria
    min_fps_ratio = 0.90  # Must achieve at least 90% of target FPS
    if fps_ratio < min_fps_ratio:
        logger.warning(
            f"Performance insufficient: {fps_ratio:.1%} < {min_fps_ratio:.1%} required"
        )
        return 1

    logger.info("Benchmark PASSED")
    return 0


def main() -> int:
    """Main entry for standalone benchmark."""
    import argparse

    import yaml

    parser = argparse.ArgumentParser(description="FPS Benchmark")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/preset_120fps.yaml"),
        help="Config file",
    )
    parser.add_argument("--duration", type=float, default=5.0, help="Benchmark duration (s)")
    parser.add_argument("--warmup", type=float, default=2.0, help="Warmup duration (s)")

    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    return run_benchmark(config, args.duration, args.warmup)


if __name__ == "__main__":
    sys.exit(main())
