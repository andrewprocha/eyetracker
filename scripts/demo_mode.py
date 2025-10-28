#!/usr/bin/env python3
"""Demo mode with synthetic eye images to visualize tracking."""

import logging
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from dual_eye_tracker.processing.detector import PupilDetector
from dual_eye_tracker.ui.viewer import DualEyeViewer
from dual_eye_tracker.utils.fps_estimator import FPSEstimator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_eye_frame(
    width: int = 320,
    height: int = 240,
    pupil_x: float = 160,
    pupil_y: float = 120,
    pupil_radius: float = 20,
    add_eyelashes: bool = True,
    add_eyelid: bool = True,
) -> np.ndarray:
    """
    Generate synthetic eye image with pupil, iris, and eyelashes.

    Args:
        width: Frame width.
        height: Frame height.
        pupil_x: Pupil center X.
        pupil_y: Pupil center Y.
        pupil_radius: Pupil radius.
        add_eyelashes: Whether to add eyelash artifacts.
        add_eyelid: Whether to add eyelid occlusion.

    Returns:
        Grayscale synthetic eye frame.
    """
    # Create bright background (sclera/iris)
    frame = np.ones((height, width), dtype=np.uint8) * 180

    # Add some texture/noise
    noise = np.random.randint(-10, 10, (height, width), dtype=np.int16)
    frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Draw iris (slightly darker ring)
    iris_radius = pupil_radius * 2.5
    y, x = np.ogrid[:height, :width]
    iris_mask = (x - pupil_x) ** 2 + (y - pupil_y) ** 2 <= iris_radius**2
    frame[iris_mask] = np.clip(frame[iris_mask] * 0.85, 0, 255).astype(np.uint8)

    # Draw dark pupil
    pupil_mask = (x - pupil_x) ** 2 + (y - pupil_y) ** 2 <= pupil_radius**2
    frame[pupil_mask] = np.random.randint(40, 70)

    # Add eyelid occlusion (top and bottom dark bands)
    if add_eyelid:
        eyelid_top = int(height * 0.15)
        eyelid_bottom = int(height * 0.85)
        frame[:eyelid_top, :] = np.random.randint(100, 140, (eyelid_top, width))
        frame[eyelid_bottom:, :] = np.random.randint(100, 140, (height - eyelid_bottom, width))

    # Add thin dark lines (eyelashes)
    if add_eyelashes:
        for i in range(8):
            x_pos = int(pupil_x + np.random.randint(-40, 40))
            y_start = max(0, int(pupil_y - pupil_radius - 5))
            y_end = min(height, int(pupil_y + pupil_radius + 30))
            thickness = 1 if i % 2 == 0 else 2
            cv2.line(frame, (x_pos, y_start), (x_pos, y_end), 30, thickness)

    return frame


def run_demo(duration: float = 60.0) -> int:
    """
    Run demo with synthetic eye tracking.

    Args:
        duration: Demo duration in seconds (0 = infinite).

    Returns:
        Exit code.
    """
    logger.info("Starting DualEyeTracker DEMO mode")
    logger.info("Generating synthetic eye images with tracking")
    logger.info("Press ESC or 'q' to quit")

    # Initialize detector with demo-friendly settings
    detector = PupilDetector(
        eyelid_exclusion_pct=15.0,
        lash_kernel_length=15,
        lash_kernel_thickness=2,
        min_area=50,
        max_area=3000,
        min_circularity=0.3,
        max_eccentricity=0.95,
        min_ring_contrast=15.0,
    )

    viewer = DualEyeViewer(
        window_name_left="Left Eye (DEMO)",
        window_name_right="Right Eye (DEMO)",
        enable_display=True,
    )
    viewer.initialize()

    fps_estimator = FPSEstimator()

    # Animation parameters
    start_time = time.time()
    frame_count = 0

    try:
        while True:
            # Check duration
            if duration > 0 and time.time() - start_time > duration:
                break

            # Animate pupil position (circular motion for left, figure-8 for right)
            t = time.time() - start_time

            # Left eye: circular motion
            left_cx = 160 + 30 * np.cos(t * 0.5)
            left_cy = 120 + 30 * np.sin(t * 0.5)

            # Right eye: figure-8 motion
            right_cx = 160 + 35 * np.sin(t * 0.7)
            right_cy = 120 + 25 * np.sin(t * 1.4)

            # Vary pupil size slightly
            pupil_radius = 18 + 4 * np.sin(t * 0.3)

            # Generate frames
            left_frame = generate_eye_frame(
                pupil_x=left_cx,
                pupil_y=left_cy,
                pupil_radius=pupil_radius,
                add_eyelashes=True,
                add_eyelid=True,
            )

            right_frame = generate_eye_frame(
                pupil_x=right_cx,
                pupil_y=right_cy,
                pupil_radius=pupil_radius * 1.1,
                add_eyelashes=True,
                add_eyelid=True,
            )

            # Detect pupils
            left_result = detector.detect(left_frame)
            right_result = detector.detect(right_frame)

            # Update FPS
            fps_estimator.tick()

            # Display
            key = viewer.show_pair(
                left_frame,
                right_frame,
                left_result,
                right_result,
                fps_estimator.get_fps(),
            )

            frame_count += 1

            # Print detection info every 30 frames
            if frame_count % 30 == 0:
                logger.info(
                    f"Frame {frame_count}: "
                    f"Left={'OK' if left_result.ok else 'FAIL'} "
                    f"({left_result.center_x:.1f}, {left_result.center_y:.1f}), "
                    f"Right={'OK' if right_result.ok else 'FAIL'} "
                    f"({right_result.center_x:.1f}, {right_result.center_y:.1f}), "
                    f"FPS={fps_estimator.get_fps():.1f}"
                )

            # Check for quit
            if key == 27 or key == ord("q"):  # ESC or 'q'
                break

            # Simulate realistic frame rate
            time.sleep(1.0 / 60.0)  # 60 fps demo

    except KeyboardInterrupt:
        logger.info("Interrupted by user")

    finally:
        viewer.close()
        logger.info(f"Demo completed. Processed {frame_count} frames")

    return 0


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="DualEyeTracker Demo Mode")
    parser.add_argument(
        "--duration", type=float, default=0, help="Demo duration in seconds (0 = infinite)"
    )

    args = parser.parse_args()

    return run_demo(args.duration)


if __name__ == "__main__":
    sys.exit(main())
