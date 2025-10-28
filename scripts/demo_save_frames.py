#!/usr/bin/env python3
"""Demo mode that saves tracking visualization frames to files."""

import logging
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from dual_eye_tracker.processing.detector import PupilDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_eye_frame(
    width: int = 320,
    height: int = 240,
    pupil_x: float = 160,
    pupil_y: float = 120,
    pupil_radius: float = 25,
) -> np.ndarray:
    """Generate synthetic eye image with high contrast (IR-like)."""
    # Create very bright background (bright iris in IR)
    frame = np.full((height, width), 220, dtype=np.uint8)

    # Draw dark pupil using OpenCV filled circle for perfect shape
    cv2.circle(frame, (int(pupil_x), int(pupil_y)), int(pupil_radius), 50, -1)

    # Smooth the boundary to look more natural
    frame = cv2.GaussianBlur(frame, (7, 7), 1.0)

    # Add eyelid bands (darker regions at top/bottom)
    eyelid_height = int(height * 0.18)
    frame[:eyelid_height, :] = 140
    frame[height - eyelid_height:, :] = 140

    # Add a few thin eyelash lines
    for i in range(4):
        x_offset = int((i - 2) * 15)  # Spread evenly
        x_pos = int(pupil_x + x_offset)
        if 0 <= x_pos < width:
            y_start = eyelid_height
            y_end = int(pupil_y + pupil_radius + 20)
            if y_end < height - eyelid_height:
                cv2.line(frame, (x_pos, y_start), (x_pos, y_end), 60, 2)

    return frame


def draw_overlay(frame: np.ndarray, result, label: str) -> np.ndarray:
    """Draw detection overlay on frame."""
    # Convert to color
    vis = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    # Add label
    cv2.putText(vis, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    if result.ok:
        cx, cy = int(result.center_x), int(result.center_y)

        # Draw crosshair
        cv2.drawMarker(vis, (cx, cy), (0, 255, 0), cv2.MARKER_CROSS, 20, 2)

        # Draw ellipse
        ellipse = (
            (result.center_x, result.center_y),
            (result.axis_major, result.axis_minor),
            result.angle,
        )
        cv2.ellipse(vis, ellipse, (0, 255, 255), 2)

        # Add info text
        info_text = f"Center: ({cx}, {cy})"
        cv2.putText(vis, info_text, (10, frame.shape[0] - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        quality_text = f"Quality: {result.quality:.2f}"
        cv2.putText(vis, quality_text, (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    else:
        cv2.putText(vis, "NO DETECTION", (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    return vis


def main() -> int:
    """Generate demo frames and save to output directory."""
    output_dir = Path("output/demo_frames")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating demo tracking frames...")
    logger.info(f"Output directory: {output_dir}")

    # Use very lenient detection settings for synthetic demo images
    detector = PupilDetector(
        eyelid_exclusion_pct=18.0,
        min_area=300,
        max_area=5000,
        min_circularity=0.2,
        max_eccentricity=0.99,
        min_ring_contrast=5.0,  # Very low threshold
        border_margin=3,
    )

    # Generate several example frames with different pupil positions
    # Use positions well within the visible area (away from eyelids)
    positions = [
        (140, 100, "left_top", 22),
        (160, 120, "center", 25),
        (180, 140, "right_bottom", 23),
        (130, 130, "left_bottom", 24),
        (190, 110, "right_top", 22),
    ]

    for idx, (px, py, desc, radius) in enumerate(positions):
        # Generate left and right eye frames with good-sized pupils
        left_frame = generate_eye_frame(pupil_x=px, pupil_y=py, pupil_radius=radius)
        right_frame = generate_eye_frame(pupil_x=px + 10, pupil_y=py - 5, pupil_radius=radius + 1)

        # Save raw frames for inspection
        cv2.imwrite(str(output_dir / f"raw_{idx:02d}_left.png"), left_frame)
        cv2.imwrite(str(output_dir / f"raw_{idx:02d}_right.png"), right_frame)

        # Detect pupils
        left_result = detector.detect(left_frame)
        right_result = detector.detect(right_frame)

        # Also get debug visualization showing the processing pipeline
        left_debug = detector.visualize_mask(left_frame)
        right_debug = detector.visualize_mask(right_frame)
        cv2.imwrite(str(output_dir / f"debug_{idx:02d}_left.png"), left_debug)
        cv2.imwrite(str(output_dir / f"debug_{idx:02d}_right.png"), right_debug)

        # Draw overlays
        left_vis = draw_overlay(left_frame, left_result, f"Left Eye - {desc}")
        right_vis = draw_overlay(right_frame, right_result, f"Right Eye - {desc}")

        # Combine side by side
        combined = np.hstack([left_vis, right_vis])

        # Save
        output_path = output_dir / f"tracking_{idx:02d}_{desc}.png"
        cv2.imwrite(str(output_path), combined)

        logger.info(
            f"Frame {idx+1}: Left={left_result.ok} "
            f"({left_result.center_x:.1f}, {left_result.center_y:.1f}), "
            f"Right={right_result.ok} "
            f"({right_result.center_x:.1f}, {right_result.center_y:.1f})"
        )

    logger.info(f"\n✓ Generated {len(positions)} demo frames in {output_dir}")
    logger.info("\nExample features visible in frames:")
    logger.info("  • Green crosshair marks pupil center")
    logger.info("  • Yellow ellipse shows fitted pupil shape")
    logger.info("  • Quality score indicates detection confidence")
    logger.info("  • Eyelash suppression keeps detection stable")

    return 0


if __name__ == "__main__":
    sys.exit(main())
