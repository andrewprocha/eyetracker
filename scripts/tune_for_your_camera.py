#!/usr/bin/env python3
"""
Interactive tool to help tune detector parameters for your specific camera setup.
Shows you what the detector sees at each processing stage.
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


def generate_realistic_eye_closeup(
    width: int = 320,
    height: int = 240,
    pupil_offset_x: int = 0,
    pupil_offset_y: int = 0,
) -> np.ndarray:
    """
    Generate realistic close-up eye as seen by IR camera.
    This matches a camera pointed directly at the eye from ~10-20cm distance.
    """
    frame = np.zeros((height, width), dtype=np.uint8)

    # Center of pupil
    px = width // 2 + pupil_offset_x
    py = height // 2 + pupil_offset_y

    # In close-up IR view:
    # - Most of frame is iris (bright, ~180-200)
    # - Pupil is centered, dark (~50-70)
    # - Eyelids only partially visible at edges
    # - Eyelashes cross over the iris

    # Start with bright iris filling most of frame
    frame[:] = 185

    # Add natural iris texture (radial pattern)
    y, x = np.ogrid[:height, :width]
    dist = np.sqrt((x - px)**2 + (y - py)**2)
    angle = np.arctan2(y - py, x - px)

    # Radial texture in iris
    iris_texture = (np.sin(angle * 40) * 3).astype(np.int16)
    frame = np.clip(frame.astype(np.int16) + iris_texture, 0, 255).astype(np.uint8)

    # Pupil (dark circle, typically 50-80 pixels diameter in close-up)
    pupil_radius = 28
    pupil_mask = dist <= pupil_radius
    frame[pupil_mask] = np.random.randint(55, 65, frame.shape)[pupil_mask]

    # Smooth pupil boundary (natural blur)
    frame = cv2.GaussianBlur(frame, (5, 5), 1.0)

    # Add eyelid shadows at top/bottom (NOT full occlusion, just darkening)
    # Upper eyelid shadow (gradient from top)
    for y_pos in range(min(40, height // 4)):
        shadow_strength = 1.0 - (y_pos / 40)
        frame[y_pos, :] = (frame[y_pos, :] * (1 - shadow_strength * 0.3)).astype(np.uint8)

    # Lower eyelid shadow
    for y_pos in range(max(height - 40, height * 3 // 4), height):
        shadow_strength = (y_pos - (height - 40)) / 40
        frame[y_pos, :] = (frame[y_pos, :] * (1 - shadow_strength * 0.3)).astype(np.uint8)

    # Add realistic eyelashes (crossing over iris, not just from edges)
    num_upper_lashes = 12
    for i in range(num_upper_lashes):
        lash_x = int(width * (i + 1) / (num_upper_lashes + 1))
        lash_x += np.random.randint(-5, 5)

        # Upper lashes drop down from top
        lash_y_start = np.random.randint(0, 10)
        lash_y_end = np.random.randint(60, 100)
        lash_curve = int((lash_x - width/2) * 0.1)  # Slight curve

        cv2.line(frame,
                (lash_x, lash_y_start),
                (lash_x + lash_curve, lash_y_end),
                45,  # Dark gray
                np.random.randint(1, 3))

    # Fewer lower lashes
    num_lower_lashes = 6
    for i in range(num_lower_lashes):
        lash_x = int(width * (i + 1) / (num_lower_lashes + 1))
        lash_x += np.random.randint(-5, 5)

        lash_y_start = height - np.random.randint(0, 10)
        lash_y_end = height - np.random.randint(40, 80)
        lash_curve = int((lash_x - width/2) * 0.1)

        cv2.line(frame,
                (lash_x, lash_y_start),
                (lash_x + lash_curve, lash_y_end),
                45,
                np.random.randint(1, 2))

    return frame


def show_processing_pipeline(frame: np.ndarray, detector: PupilDetector):
    """Show each stage of the detection pipeline."""
    h, w = frame.shape[:2]

    # Stage 1: Original
    stage1 = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    cv2.putText(stage1, "1. Original", (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Stage 2: After eyelid exclusion
    masked = detector._exclude_eyelids(frame)
    stage2 = cv2.cvtColor(masked, cv2.COLOR_GRAY2BGR)
    cv2.putText(stage2, "2. Eyelid exclusion", (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    band_h = int(h * detector.eyelid_exclusion_pct / 100.0)
    cv2.rectangle(stage2, (0, 0), (w, band_h), (0, 0, 255), 1)
    cv2.rectangle(stage2, (0, h-band_h), (w, h), (0, 0, 255), 1)

    # Stage 3: After eyelash suppression
    suppressed = detector._suppress_eyelashes(masked)
    stage3 = cv2.cvtColor(suppressed, cv2.COLOR_GRAY2BGR)
    cv2.putText(stage3, "3. Eyelash suppression", (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Stage 4: After thresholding
    binary = detector._threshold(suppressed)
    stage4 = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    cv2.putText(stage4, "4. Otsu threshold", (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Stage 5: After morphology
    cleaned = detector._morphology_cleanup(binary)
    stage5 = cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)
    cv2.putText(stage5, "5. Morphology cleanup", (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Stage 6: Final detection
    result = detector.detect(frame)
    stage6 = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    if result.ok:
        cv2.drawMarker(stage6, (int(result.center_x), int(result.center_y)),
                      (0, 255, 0), cv2.MARKER_CROSS, 20, 2)
        ellipse = ((result.center_x, result.center_y),
                  (result.axis_major, result.axis_minor),
                  result.angle)
        cv2.ellipse(stage6, ellipse, (0, 255, 255), 2)
        cv2.putText(stage6, f"6. DETECTED Q={result.quality:.2f}", (5, 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    else:
        cv2.putText(stage6, "6. NOT DETECTED", (5, 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    # Combine stages
    row1 = np.hstack([stage1, stage2, stage3])
    row2 = np.hstack([stage4, stage5, stage6])
    combined = np.vstack([row1, row2])

    return combined, result


def main():
    """Run interactive tuning tool."""
    output_dir = Path("output/tuning")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 70)
    logger.info("DETECTOR TUNING FOR YOUR CAMERA")
    logger.info("=" * 70)
    logger.info("\nThis tool shows you what the detector sees at each processing stage.")
    logger.info("Use this to understand why detection fails and tune parameters.\n")

    # Test multiple parameter configurations
    configs = [
        ("default_params", {
            "eyelid_exclusion_pct": 20.0,
            "min_area": 50,
            "min_ring_contrast": 15.0,
        }),
        ("reduced_eyelid_mask", {
            "eyelid_exclusion_pct": 5.0,  # Much less masking for close-up
            "min_area": 200,  # Larger pupils in close-up
            "min_ring_contrast": 12.0,
        }),
        ("optimized_closeup", {
            "eyelid_exclusion_pct": 0.0,  # No eyelid masking needed
            "min_area": 300,  # Close-up pupils are big
            "max_area": 8000,
            "min_ring_contrast": 10.0,
            "min_circularity": 0.2,  # Allow more variation
        }),
    ]

    # Generate test eye at center
    test_frame = generate_realistic_eye_closeup()

    cv2.imwrite(str(output_dir / "input_eye_closeup.png"), test_frame)
    logger.info(f"Saved input image: {output_dir / 'input_eye_closeup.png'}")

    best_config = None
    best_quality = 0

    for config_name, params in configs:
        logger.info(f"\n{'='*70}")
        logger.info(f"Testing: {config_name}")
        logger.info(f"{'='*70}")
        for key, val in params.items():
            logger.info(f"  {key}: {val}")

        detector = PupilDetector(**params)
        pipeline_vis, result = show_processing_pipeline(test_frame, detector)

        # Save visualization
        output_path = output_dir / f"pipeline_{config_name}.png"
        cv2.imwrite(str(output_path), pipeline_vis)

        if result.ok:
            logger.info(f"\n✓ SUCCESS!")
            logger.info(f"  Center: ({result.center_x:.1f}, {result.center_y:.1f})")
            logger.info(f"  Quality: {result.quality:.2f}")
            logger.info(f"  Axes: ({result.axis_major:.1f}, {result.axis_minor:.1f})")
            logger.info(f"  Saved: {output_path}")

            if result.quality > best_quality:
                best_quality = result.quality
                best_config = (config_name, params)
        else:
            logger.info(f"\n✗ FAILED - detection unsuccessful")
            logger.info(f"  Check pipeline visualization: {output_path}")
            logger.info(f"  Look for issues in stages 2-5")

    # Summary
    logger.info(f"\n{'='*70}")
    logger.info("SUMMARY")
    logger.info(f"{'='*70}")

    if best_config:
        logger.info(f"\n✓ Best configuration: {best_config[0]} (quality: {best_quality:.2f})")
        logger.info(f"\nRecommended config for your camera:\n")
        logger.info("processing:")
        for key, val in best_config[1].items():
            logger.info(f"  {key}: {val}")

        # Save recommended config
        config_path = output_dir / "recommended_config.txt"
        with open(config_path, "w") as f:
            f.write("# Recommended detector parameters for your camera setup\n")
            f.write("# Add these to your configs/default.yaml under 'processing:'\n\n")
            for key, val in best_config[1].items():
                f.write(f"{key}: {val}\n")

        logger.info(f"\nSaved recommended config to: {config_path}")
    else:
        logger.info("\n✗ None of the tested configurations worked.")
        logger.info("\nTroubleshooting steps:")
        logger.info("1. Check pipeline images in output/tuning/")
        logger.info("2. Look at stage 4 (threshold) - is the pupil visible?")
        logger.info("3. If pupil is too faint, you need more IR lighting")
        logger.info("4. If pupil is fragmented by eyelashes, increase lash_kernel_length")
        logger.info("5. If eyelid exclusion removes pupil, set eyelid_exclusion_pct to 0")

    logger.info(f"\nAll visualizations saved to: {output_dir}/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
