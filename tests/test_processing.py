"""Tests for pupil detection and processing."""

import numpy as np
import pytest

from dual_eye_tracker.processing.detector import PupilDetector
from dual_eye_tracker.processing.result import DetectionResult


class TestDetectionResult:
    """Tests for DetectionResult data structure."""

    def test_failed_result(self):
        """Test failed result creation."""
        result = DetectionResult.failed()
        assert result.ok is False
        assert result.center_x == 0.0
        assert result.center_y == 0.0

    def test_successful_result(self):
        """Test successful result."""
        result = DetectionResult(
            ok=True,
            center_x=100.0,
            center_y=120.0,
            axis_major=30.0,
            axis_minor=25.0,
            angle=45.0,
            quality=0.8,
            eccentricity=0.5,
            area=700.0,
        )
        assert result.ok is True
        assert result.center == (100.0, 120.0)
        assert result.axes == (30.0, 25.0)


class TestPupilDetector:
    """Tests for PupilDetector."""

    @pytest.fixture
    def detector(self):
        """Create detector with default settings."""
        return PupilDetector()

    def test_detect_empty_frame(self, detector):
        """Test detection on empty frame."""
        frame = np.zeros((240, 320), dtype=np.uint8)
        result = detector.detect(frame)
        assert result.ok is False

    def test_detect_synthetic_pupil(self, detector):
        """Test detection on synthetic dark disk."""
        # Create bright background
        frame = np.ones((240, 320), dtype=np.uint8) * 200

        # Draw dark pupil (disk at center)
        center = (160, 120)
        radius = 20
        y, x = np.ogrid[: frame.shape[0], : frame.shape[1]]
        mask = (x - center[0]) ** 2 + (y - center[1]) ** 2 <= radius**2
        frame[mask] = 50

        result = detector.detect(frame)

        # Should detect successfully
        assert result.ok is True

        # Center should be close
        center_error = np.sqrt(
            (result.center_x - center[0]) ** 2 + (result.center_y - center[1]) ** 2
        )
        assert center_error <= 2.0, f"Center error: {center_error:.2f} px"

        # Radius should be reasonable (axes ~ 2*radius)
        avg_axis = (result.axis_major + result.axis_minor) / 2.0
        expected_diameter = 2 * radius
        axis_error_pct = abs(avg_axis - expected_diameter) / expected_diameter
        assert axis_error_pct <= 0.1, f"Axis error: {axis_error_pct:.1%}"

    def test_detect_with_eyelashes(self, detector):
        """Test robustness to thin dark lines (eyelashes)."""
        # Create bright background with dark pupil
        frame = np.ones((240, 320), dtype=np.uint8) * 200
        center = (160, 120)
        radius = 20

        # Draw pupil
        y, x = np.ogrid[: frame.shape[0], : frame.shape[1]]
        mask = (x - center[0]) ** 2 + (y - center[1]) ** 2 <= radius**2
        frame[mask] = 50

        # Add thin dark lines (simulated eyelashes)
        for i in range(5):
            y_pos = center[1] + radius + i * 5
            if y_pos < frame.shape[0]:
                frame[y_pos, center[0] - 15 : center[0] + 15] = 40

        result = detector.detect(frame)

        # Should still detect despite eyelashes
        assert result.ok is True

        # Center should still be reasonably accurate
        center_error = np.sqrt(
            (result.center_x - center[0]) ** 2 + (result.center_y - center[1]) ** 2
        )
        assert center_error <= 5.0, f"Center error with eyelashes: {center_error:.2f} px"

    def test_detect_border_rejection(self, detector):
        """Test that detections touching border are rejected."""
        frame = np.ones((240, 320), dtype=np.uint8) * 200

        # Draw pupil at edge
        center = (10, 120)  # Too close to left edge
        radius = 20
        y, x = np.ogrid[: frame.shape[0], : frame.shape[1]]
        mask = (x - center[0]) ** 2 + (y - center[1]) ** 2 <= radius**2
        frame[mask] = 50

        result = detector.detect(frame)

        # Should reject due to border proximity
        assert result.ok is False

    def test_visualize_mask(self, detector):
        """Test debug visualization."""
        frame = np.ones((240, 320), dtype=np.uint8) * 200
        vis = detector.visualize_mask(frame)

        assert vis.shape == (240, 320, 3)
        assert vis.dtype == np.uint8
