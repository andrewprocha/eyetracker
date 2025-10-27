"""Main CLI application for DualEyeTracker."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import yaml

from dual_eye_tracker.capture.camera_worker import CameraWorker
from dual_eye_tracker.capture.sync import FrameSynchronizer
from dual_eye_tracker.io.telemetry import TelemetryWriter
from dual_eye_tracker.io.video_writer import DualVideoWriter
from dual_eye_tracker.processing.detector import PupilDetector
from dual_eye_tracker.ui.viewer import DualEyeViewer
from dual_eye_tracker.utils.fps_estimator import FPSEstimator
from dual_eye_tracker.utils.timing import Timer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    """Load YAML configuration file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def run_live_viewer(config: dict, output_dir: Optional[Path] = None) -> int:
    """
    Run live dual-eye viewer.

    Args:
        config: Configuration dictionary.
        output_dir: Optional directory for saving telemetry/video.

    Returns:
        Exit code.
    """
    cam_cfg = config["cameras"]
    proc_cfg = config["processing"]
    sync_cfg = config["sync"]
    ui_cfg = config["ui"]

    # Initialize components
    left_cam = CameraWorker(
        camera_id=cam_cfg["left_id"],
        width=cam_cfg["width"],
        height=cam_cfg["height"],
        fps=cam_cfg["fps"],
        exposure_us=cam_cfg.get("exposure_us"),
        backend=cam_cfg.get("backend", "dshow"),
        pixel_format=cam_cfg.get("pixel_format", "YUY2"),
    )

    right_cam = CameraWorker(
        camera_id=cam_cfg["right_id"],
        width=cam_cfg["width"],
        height=cam_cfg["height"],
        fps=cam_cfg["fps"],
        exposure_us=cam_cfg.get("exposure_us"),
        backend=cam_cfg.get("backend", "dshow"),
        pixel_format=cam_cfg.get("pixel_format", "YUY2"),
    )

    synchronizer = FrameSynchronizer(tolerance_ms=sync_cfg["tolerance_ms"])

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

    viewer = DualEyeViewer(enable_display=ui_cfg["enable_display"])
    fps_estimator = FPSEstimator()

    # Optional writers
    telemetry_writer: Optional[TelemetryWriter] = None
    video_writer: Optional[DualVideoWriter] = None

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

        if ui_cfg.get("save_telemetry", False):
            telemetry_writer = TelemetryWriter(output_dir / "telemetry.csv")
            telemetry_writer.open()

        if ui_cfg.get("save_video", False):
            video_writer = DualVideoWriter(
                output_dir / "left.avi",
                output_dir / "right.avi",
                fps=cam_cfg["fps"],
                codec="FFV1",
                width=cam_cfg["width"],
                height=cam_cfg["height"],
            )
            video_writer.open()

    # Start cameras
    logger.info("Starting cameras...")
    if not left_cam.start():
        logger.error("Failed to start left camera")
        return 1

    if not right_cam.start():
        logger.error("Failed to start right camera")
        left_cam.stop()
        return 1

    logger.info("Cameras started. Press ESC or 'q' to quit.")

    # Main loop
    try:
        while True:
            # Retrieve frames
            left_data = left_cam.get_frame()
            right_data = right_cam.get_frame()

            if left_data is not None:
                synchronizer.add_left(left_data[0], left_data[1])

            if right_data is not None:
                synchronizer.add_right(right_data[0], right_data[1])

            # Try to get synchronized pair
            pair = synchronizer.get_pair()
            if pair is None:
                continue

            timestamp, left_frame, right_frame = pair
            fps_estimator.tick()

            # Detect pupils
            left_result = detector.detect(left_frame)
            right_result = detector.detect(right_frame)

            # Write telemetry
            if telemetry_writer is not None:
                telemetry_writer.write_pair(timestamp, left_result, right_result)

            # Write video
            if video_writer is not None:
                video_writer.write_pair(left_frame, right_frame)

            # Display
            key = viewer.show_pair(
                left_frame, right_frame, left_result, right_result, fps_estimator.get_fps()
            )

            if key == 27 or key == ord("q"):  # ESC or 'q'
                break

    except KeyboardInterrupt:
        logger.info("Interrupted by user")

    finally:
        # Cleanup
        logger.info("Shutting down...")
        left_cam.stop()
        right_cam.stop()
        viewer.close()

        if telemetry_writer is not None:
            telemetry_writer.close()

        if video_writer is not None:
            video_writer.close()

        # Print stats
        logger.info(f"Left camera: {left_cam.get_stats()}")
        logger.info(f"Right camera: {right_cam.get_stats()}")
        logger.info(f"Synchronizer: {synchronizer.get_stats()}")

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DualEyeTracker - Dual camera pupil tracking")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/default.yaml"),
        help="Path to configuration file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory for telemetry and video",
    )
    parser.add_argument(
        "--mode",
        choices=["viewer", "benchmark", "record"],
        default="viewer",
        help="Operation mode",
    )

    args = parser.parse_args()

    if not args.config.exists():
        logger.error(f"Config file not found: {args.config}")
        return 1

    config = load_config(args.config)

    if args.mode == "viewer":
        return run_live_viewer(config, args.output)
    elif args.mode == "benchmark":
        # Import benchmark script
        from scripts.bench_fps import run_benchmark

        return run_benchmark(config)
    elif args.mode == "record":
        if args.output is None:
            logger.error("--output required for record mode")
            return 1
        # Enable saving in config
        config["ui"]["save_telemetry"] = True
        config["ui"]["save_video"] = True
        return run_live_viewer(config, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
