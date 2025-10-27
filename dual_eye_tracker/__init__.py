"""DualEyeTracker - Production-ready dual-camera pupil tracking system."""

__version__ = "0.1.0"
__author__ = "DualEyeTracker Contributors"
__license__ = "MIT"

from dual_eye_tracker.capture.camera_worker import CameraWorker
from dual_eye_tracker.capture.sync import FrameSynchronizer
from dual_eye_tracker.processing.detector import PupilDetector
from dual_eye_tracker.processing.result import DetectionResult

__all__ = [
    "CameraWorker",
    "FrameSynchronizer",
    "PupilDetector",
    "DetectionResult",
]
