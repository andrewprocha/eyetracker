"""Real-time dual-eye viewer with overlay visualization."""

import logging
from typing import Optional

import cv2
import numpy as np

from dual_eye_tracker.processing.result import DetectionResult

logger = logging.getLogger(__name__)


class DualEyeViewer:
    """OpenCV-based viewer for dual eye tracking with overlays."""

    def __init__(
        self,
        window_name_left: str = "Left Eye",
        window_name_right: str = "Right Eye",
        enable_display: bool = True,
    ):
        """
        Initialize viewer.

        Args:
            window_name_left: Window title for left camera.
            window_name_right: Window title for right camera.
            enable_display: Whether to show windows.
        """
        self.window_name_left = window_name_left
        self.window_name_right = window_name_right
        self.enable_display = enable_display
        self._initialized = False

    def initialize(self) -> None:
        """Create display windows."""
        if not self.enable_display or self._initialized:
            return

        cv2.namedWindow(self.window_name_left, cv2.WINDOW_NORMAL)
        cv2.namedWindow(self.window_name_right, cv2.WINDOW_NORMAL)
        self._initialized = True

    def show_pair(
        self,
        left_frame: np.ndarray,
        right_frame: np.ndarray,
        left_result: Optional[DetectionResult] = None,
        right_result: Optional[DetectionResult] = None,
        fps: Optional[float] = None,
    ) -> int:
        """
        Display frame pair with overlays.

        Args:
            left_frame: Left camera frame (grayscale).
            right_frame: Right camera frame (grayscale).
            left_result: Detection result for left eye.
            right_result: Detection result for right eye.
            fps: Current FPS to display.

        Returns:
            Key code from waitKey (27 = ESC, ord('q') = quit).
        """
        if not self.enable_display:
            return -1

        if not self._initialized:
            self.initialize()

        # Convert to color for overlays
        left_vis = cv2.cvtColor(left_frame, cv2.COLOR_GRAY2BGR)
        right_vis = cv2.cvtColor(right_frame, cv2.COLOR_GRAY2BGR)

        # Draw overlays
        self._draw_overlay(left_vis, left_result, fps)
        self._draw_overlay(right_vis, right_result, fps)

        # Show
        cv2.imshow(self.window_name_left, left_vis)
        cv2.imshow(self.window_name_right, right_vis)

        return cv2.waitKey(1) & 0xFF

    def _draw_overlay(
        self, frame: np.ndarray, result: Optional[DetectionResult], fps: Optional[float]
    ) -> None:
        """Draw detection overlay on frame."""
        h, w = frame.shape[:2]

        # FPS text
        if fps is not None:
            text = f"FPS: {fps:.1f}"
            cv2.putText(
                frame,
                text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

        # Detection overlay
        if result is not None and result.ok:
            cx, cy = int(result.center_x), int(result.center_y)

            # Crosshair
            cv2.drawMarker(
                frame,
                (cx, cy),
                (0, 255, 0),
                cv2.MARKER_CROSS,
                20,
                2,
            )

            # Ellipse
            ellipse = (
                (result.center_x, result.center_y),
                (result.axis_major, result.axis_minor),
                result.angle,
            )
            cv2.ellipse(frame, ellipse, (0, 255, 255), 2)

            # Quality text
            quality_text = f"Q: {result.quality:.2f}"
            cv2.putText(
                frame,
                quality_text,
                (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 0),
                1,
            )
        else:
            # Failed detection
            cv2.putText(
                frame,
                "NO DETECTION",
                (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                1,
            )

    def close(self) -> None:
        """Close all windows."""
        if self.enable_display and self._initialized:
            cv2.destroyAllWindows()
            self._initialized = False
