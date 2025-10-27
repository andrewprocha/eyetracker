"""Pupil detector with IR-oriented preprocessing and eyelash suppression."""

import logging
from typing import Optional, Tuple

import cv2
import numpy as np

from dual_eye_tracker.processing.result import DetectionResult

logger = logging.getLogger(__name__)


class PupilDetector:
    """Detects pupil ellipse in IR eye imagery with robustness to eyelashes and eyelids."""

    def __init__(
        self,
        eyelid_exclusion_pct: float = 20.0,
        lash_kernel_length: int = 15,
        lash_kernel_thickness: int = 2,
        min_area: int = 50,
        max_area: int = 5000,
        min_circularity: float = 0.3,
        max_eccentricity: float = 0.95,
        min_ring_contrast: float = 15.0,
        morph_open_size: int = 3,
        morph_close_size: int = 5,
        border_margin: int = 5,
    ):
        """
        Initialize detector.

        Args:
            eyelid_exclusion_pct: Percentage of top/bottom rows to exclude for eyelids.
            lash_kernel_length: Length of line kernel for eyelash morphology.
            lash_kernel_thickness: Thickness of line kernel.
            min_area: Minimum contour area.
            max_area: Maximum contour area.
            min_circularity: Minimum circularity (1.0 = perfect circle).
            max_eccentricity: Maximum eccentricity (0 = circle, 1 = line).
            min_ring_contrast: Minimum average contrast around ellipse boundary.
            morph_open_size: Kernel size for morphological opening.
            morph_close_size: Kernel size for morphological closing.
            border_margin: Pixels from edge to reject detections.
        """
        self.eyelid_exclusion_pct = eyelid_exclusion_pct
        self.lash_kernel_length = lash_kernel_length
        self.lash_kernel_thickness = lash_kernel_thickness
        self.min_area = min_area
        self.max_area = max_area
        self.min_circularity = min_circularity
        self.max_eccentricity = max_eccentricity
        self.min_ring_contrast = min_ring_contrast
        self.morph_open_size = morph_open_size
        self.morph_close_size = morph_close_size
        self.border_margin = border_margin

        # Pre-build kernels
        self._lash_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (lash_kernel_length, lash_kernel_thickness)
        )
        self._open_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (morph_open_size, morph_open_size)
        )
        self._close_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (morph_close_size, morph_close_size)
        )

    def detect(self, frame: np.ndarray) -> DetectionResult:
        """
        Detect pupil in frame.

        Args:
            frame: Grayscale image (uint8).

        Returns:
            DetectionResult with pupil parameters.
        """
        if frame is None or frame.size == 0:
            return DetectionResult.failed()

        h, w = frame.shape[:2]

        # Step 1: Exclude eyelid bands
        masked = self._exclude_eyelids(frame)

        # Step 2: Suppress eyelashes with line-shaped morphology
        suppressed = self._suppress_eyelashes(masked)

        # Step 3: Otsu thresholding (dark pupil on bright iris)
        binary = self._threshold(suppressed)

        # Step 4: Morphological cleanup
        cleaned = self._morphology_cleanup(binary)

        # Step 5: Find contours and filter
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best_result = DetectionResult.failed()
        best_score = -1.0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.min_area or area > self.max_area:
                continue

            # Circularity check
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity < self.min_circularity:
                continue

            # Fit ellipse (requires at least 5 points)
            if len(cnt) < 5:
                continue

            ellipse = cv2.fitEllipse(cnt)
            (cx, cy), (MA, ma), angle = ellipse

            # Border touch rejection
            if (
                cx < self.border_margin
                or cy < self.border_margin
                or cx > w - self.border_margin
                or cy > h - self.border_margin
            ):
                continue

            # Eccentricity check
            major = max(MA, ma)
            minor = min(MA, ma)
            if minor == 0:
                continue
            eccentricity = np.sqrt(1 - (minor / major) ** 2)
            if eccentricity > self.max_eccentricity:
                continue

            # Ring contrast check
            contrast = self._compute_ring_contrast(frame, ellipse)
            if contrast < self.min_ring_contrast:
                continue

            # Score by area (prefer larger pupils) and quality
            score = area * contrast

            if score > best_score:
                best_score = score
                best_result = DetectionResult(
                    ok=True,
                    center_x=cx,
                    center_y=cy,
                    axis_major=major,
                    axis_minor=minor,
                    angle=angle,
                    quality=min(contrast / 50.0, 1.0),  # Normalize to 0-1
                    eccentricity=eccentricity,
                    area=area,
                )

        return best_result

    def _exclude_eyelids(self, frame: np.ndarray) -> np.ndarray:
        """Mask out top and bottom bands to exclude eyelids."""
        h, w = frame.shape[:2]
        band_h = int(h * self.eyelid_exclusion_pct / 100.0)

        masked = frame.copy()
        if band_h > 0:
            masked[:band_h, :] = 255  # Set to white (bright)
            masked[h - band_h :, :] = 255

        return masked

    def _suppress_eyelashes(self, frame: np.ndarray) -> np.ndarray:
        """Apply morphological opening with line kernel to suppress thin dark eyelashes."""
        # Invert: lashes are dark, we want to erode them in inverted space
        inverted = cv2.bitwise_not(frame)
        opened = cv2.morphologyEx(inverted, cv2.MORPH_OPEN, self._lash_kernel)
        # Also apply rotated kernel
        rotated_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (self.lash_kernel_thickness, self.lash_kernel_length)
        )
        opened = cv2.morphologyEx(opened, cv2.MORPH_OPEN, rotated_kernel)
        return cv2.bitwise_not(opened)

    def _threshold(self, frame: np.ndarray) -> np.ndarray:
        """Apply Otsu's method to segment dark pupil."""
        _, binary = cv2.threshold(frame, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return binary

    def _morphology_cleanup(self, binary: np.ndarray) -> np.ndarray:
        """Remove noise with opening, then fill holes with closing."""
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, self._open_kernel)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, self._close_kernel)
        return closed

    def _compute_ring_contrast(self, frame: np.ndarray, ellipse: Tuple) -> float:
        """Compute average intensity difference between inner and outer ring around ellipse."""
        (cx, cy), (MA, ma), angle = ellipse

        # Sample points on ellipse boundary
        inner_samples = []
        outer_samples = []

        for theta in np.linspace(0, 2 * np.pi, 32, endpoint=False):
            # Parametric ellipse equation
            a = MA / 2.0
            b = ma / 2.0
            cos_angle = np.cos(np.radians(angle))
            sin_angle = np.sin(np.radians(angle))
            cos_theta = np.cos(theta)
            sin_theta = np.sin(theta)

            # Ellipse point
            x = a * cos_theta
            y = b * sin_theta

            # Rotate
            xr = x * cos_angle - y * sin_angle + cx
            yr = x * sin_angle + y * cos_angle + cy

            # Inner point (90% of radius)
            xi = int(cx + 0.9 * (xr - cx))
            yi = int(cy + 0.9 * (yr - cy))

            # Outer point (110% of radius)
            xo = int(cx + 1.1 * (xr - cx))
            yo = int(cy + 1.1 * (yr - cy))

            # Sample if in bounds
            h, w = frame.shape[:2]
            if 0 <= xi < w and 0 <= yi < h:
                inner_samples.append(frame[yi, xi])
            if 0 <= xo < w and 0 <= yo < h:
                outer_samples.append(frame[yo, xo])

        if not inner_samples or not outer_samples:
            return 0.0

        # Contrast = outer - inner (pupil is dark, iris is bright)
        avg_inner = np.mean(inner_samples)
        avg_outer = np.mean(outer_samples)
        contrast = avg_outer - avg_inner

        return float(contrast)

    def visualize_mask(self, frame: np.ndarray) -> np.ndarray:
        """
        Generate debug visualization with preprocessing masks.

        Args:
            frame: Input frame.

        Returns:
            Color image with masks overlaid.
        """
        masked = self._exclude_eyelids(frame)
        suppressed = self._suppress_eyelashes(masked)
        binary = self._threshold(suppressed)
        cleaned = self._morphology_cleanup(binary)

        # Create RGB visualization
        vis = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        # Overlay cleaned binary mask in red
        vis[cleaned > 0] = [0, 0, 255]

        return vis
