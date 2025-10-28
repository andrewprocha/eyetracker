#!/usr/bin/env python3
"""
Test detection with realistic close-up eye images.
Use this to tune detector parameters before connecting real cameras.
"""

import logging
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from dual_eye_tracker.processing.detector import PupilDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_realistic_eye(
    width: int = 320,
    height: int = 240,
    pupil_center: tuple = (160, 120),
    pupil_radius: int = 30,
    iris_brightness: int = 180,
    pupil_brightness: int = 60,
    add_glint: bool = False,
) -> np.ndarray:
    """
    Generate realistic close-up eye image as seen by IR camera.

    In IR lighting:
    - Pupil appears very dark (absorbs IR)
    - Iris appears bright (reflects IR)
    - Sclera (white) appears very bright
    - Eyelids/skin appears medium gray
    """
    frame = np.zeros((height, width), dtype=np.uint8)

    px, py = pupil_center

    # Background: iris/sclera (bright in IR)
    frame[:] = iris_brightness

    # Add slight radial gradient for iris texture
    y, x = np.ogrid[:height, :width]
    dist = np.sqrt((x - px)**2 + (y - py)**2)

    # Iris region (slightly textured)
    iris_radius = pupil_radius * 2.2
    iris_mask = dist <= iris_radius
    iris_texture = np.random.randint(-8, 8, frame.shape, dtype=np.int16)
    frame[iris_mask] = np.clip(
        iris_brightness + iris_texture[iris_mask],
        iris_brightness - 20,
        iris_brightness + 20
    ).astype(np.uint8)

    # Pupil (very dark in IR)
    pupil_mask = dist <= pupil_radius
    pupil_noise = np.random.randint(-5, 5, frame.shape, dtype=np.int16)
    frame[pupil_mask] = np.clip(
        pupil_brightness + pupil_noise[pupil_mask],
        pupil_brightness - 10,
        pupil_brightness + 10
    ).astype(np.uint8)

    # Smooth the pupil boundary
    frame = cv2.GaussianBlur(frame, (5, 5), 0.5)

    # Add upper eyelid (partial occlusion from top)
    upper_eyelid_y = int(py - pupil_radius * 1.5)
    if upper_eyelid_y > 0:
        # Create curved eyelid
        for y_pos in range(max(0, upper_eyelid_y - 30), upper_eyelid_y):
            curve = int(20 * np.sin((y_pos - upper_eyelid_y + 30) / 30 * np.pi))
            x_start = max(0, px - iris_radius - curve)
            x_end = min(width, px + iris_radius + curve)
            frame[y_pos, int(x_start):int(x_end)] = np.random.randint(100, 130)

    # Add lower eyelid
    lower_eyelid_y = int(py + pupil_radius * 1.5)
    if lower_eyelid_y < height:
        for y_pos in range(lower_eyelid_y, min(height, lower_eyelid_y + 30)):
            curve = int(20 * np.sin((y_pos - lower_eyelid_y) / 30 * np.pi))
            x_start = max(0, px - iris_radius - curve)
            x_end = min(width, px + iris_radius + curve)
            frame[y_pos, int(x_start):int(x_end)] = np.random.randint(100, 130)

    # Add eyelashes (thin dark lines)
    num_lashes = 8
    for i in range(num_lashes):
        # Upper lashes
        lash_x = int(px + (i - num_lashes/2) * 15 + np.random.randint(-5, 5))
        if 0 <= lash_x < width and upper_eyelid_y > 0:
            lash_start_y = max(0, upper_eyelid_y - 5)
            lash_end_y = min(height, upper_eyelid_y + np.random.randint(15, 30))
            cv2.line(frame, (lash_x, lash_start_y), (lash_x, lash_end_y),
                    40, 1 + np.random.randint(0, 2))

        # Lower lashes (fewer and shorter)
        if i % 2 == 0 and lower_eyelid_y < height:
            lash_x = int(px + (i - num_lashes/2) * 15)
            if 0 <= lash_x < width:
                lash_start_y = lower_eyelid_y
                lash_end_y = min(height, lower_eyelid_y + np.random.randint(5, 15))
                cv2.line(frame, (lash_x, lash_start_y), (lash_x, lash_end_y), 40, 1)

    # Optional: add glint (corneal reflection)
    if add_glint:
        glint_x = int(px + pupil_radius * 0.4)
        glint_y = int(py - pupil_radius * 0.3)
        cv2.circle(frame, (glint_x, glint_y), 3, 255, -1)

    return frame


def test_detection_with_tuning():
    """Test detector with various parameter sets to find best settings."""

    output_dir = Path("output/detection_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("DETECTION PARAMETER TUNING TEST")
    logger.info("=" * 60)

    # Test different pupil sizes and positions
    test_cases = [
        ("center_large", (160, 120), 35, 180, 60),
        ("center_medium", (160, 120), 25, 180, 60),
        ("center_small", (160, 120), 18, 180, 60),
        ("left_gaze", (130, 110), 28, 180, 60),
        ("right_gaze", (190, 130), 28, 180, 60),
        ("bright_iris", (160, 120), 30, 200, 55),  # Higher contrast
        ("dark_iris", (160, 120), 30, 160, 70),    # Lower contrast
        ("with_glint", (160, 120), 30, 180, 60),   # Corneal reflection
    ]

    # Parameter sets to test (from conservative to aggressive)
    param_sets = [
        ("default", {
            "eyelid_exclusion_pct": 20.0,
            "min_area": 50,
            "max_area": 5000,
            "min_circularity": 0.3,
            "max_eccentricity": 0.95,
            "min_ring_contrast": 15.0,
        }),
        ("lenient", {
            "eyelid_exclusion_pct": 15.0,
            "min_area": 100,
            "max_area": 6000,
            "min_circularity": 0.25,
            "max_eccentricity": 0.97,
            "min_ring_contrast": 10.0,
        }),
        ("very_lenient", {
            "eyelid_exclusion_pct": 10.0,
            "min_area": 80,
            "max_area": 8000,
            "min_circularity": 0.2,
            "max_eccentricity": 0.98,
            "min_ring_contrast": 8.0,
        }),
    ]

    results = []

    for param_name, params in param_sets:
        detector = PupilDetector(**params)
        logger.info(f"\nTesting parameter set: {param_name}")
        logger.info(f"  min_ring_contrast: {params['min_ring_contrast']}")
        logger.info(f"  min_circularity: {params['min_circularity']}")

        success_count = 0

        for test_name, center, radius, iris_bright, pupil_bright in test_cases:
            add_glint = "glint" in test_name

            # Generate test image
            frame = generate_realistic_eye(
                pupil_center=center,
                pupil_radius=radius,
                iris_brightness=iris_bright,
                pupil_brightness=pupil_bright,
                add_glint=add_glint,
            )

            # Detect
            result = detector.detect(frame)

            # Calculate error
            if result.ok:
                error_x = abs(result.center_x - center[0])
                error_y = abs(result.center_y - center[1])
                error_dist = np.sqrt(error_x**2 + error_y**2)
                success_count += 1

                status = "✓ PASS"
                if error_dist > 5:
                    status += f" (error: {error_dist:.1f}px)"
            else:
                error_dist = None
                status = "✗ FAIL"

            results.append({
                "param_set": param_name,
                "test_case": test_name,
                "success": result.ok,
                "error": error_dist,
            })

            # Save visualization for this param set
            if param_name == "default":  # Only save for one param set
                vis = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

                # Draw ground truth
                cv2.circle(vis, center, 3, (255, 0, 0), -1)  # Blue dot
                cv2.circle(vis, center, radius, (255, 0, 0), 1)  # Blue circle

                # Draw detection
                if result.ok:
                    det_center = (int(result.center_x), int(result.center_y))
                    cv2.drawMarker(vis, det_center, (0, 255, 0), cv2.MARKER_CROSS, 20, 2)
                    ellipse = (
                        (result.center_x, result.center_y),
                        (result.axis_major, result.axis_minor),
                        result.angle
                    )
                    cv2.ellipse(vis, ellipse, (0, 255, 255), 2)

                    # Add text
                    cv2.putText(vis, f"Error: {error_dist:.1f}px", (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                else:
                    cv2.putText(vis, "DETECTION FAILED", (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                cv2.putText(vis, test_name, (10, frame.shape[0] - 10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                output_path = output_dir / f"test_{test_name}.png"
                cv2.imwrite(str(output_path), vis)

            logger.info(f"  {test_name:20s}: {status}")

        success_rate = success_count / len(test_cases) * 100
        logger.info(f"\n  Success rate: {success_count}/{len(test_cases)} ({success_rate:.0f}%)")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)

    for param_name, _ in param_sets:
        param_results = [r for r in results if r["param_set"] == param_name]
        success_count = sum(1 for r in param_results if r["success"])
        success_rate = success_count / len(param_results) * 100

        avg_error = np.mean([r["error"] for r in param_results if r["error"] is not None])

        logger.info(f"\n{param_name:15s}: {success_count}/{len(param_results)} success ({success_rate:.0f}%)")
        if success_count > 0:
            logger.info(f"                 Average error: {avg_error:.2f} pixels")

    logger.info(f"\nVisualization images saved to: {output_dir}")
    logger.info("\nRECOMMENDATIONS:")
    logger.info("1. Check test images to see if they match your camera's view")
    logger.info("2. Use parameter set with highest success rate")
    logger.info("3. If all fail, your camera may need different lighting/exposure")
    logger.info("4. Run: python scripts/diagnose_caps.py --camera 0")
    logger.info("   to check your actual camera output")


def main():
    test_detection_with_tuning()
    return 0


if __name__ == "__main__":
    sys.exit(main())
