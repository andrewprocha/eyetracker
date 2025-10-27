"""Threaded camera worker for high-speed capture."""

import logging
import threading
import time
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

from dual_eye_tracker.capture.ring_buffer import RingBuffer

logger = logging.getLogger(__name__)


class CameraWorker:
    """Background thread for capturing frames from a single camera."""

    def __init__(
        self,
        camera_id: int,
        width: int = 320,
        height: int = 240,
        fps: int = 120,
        exposure_us: Optional[int] = None,
        backend: str = "dshow",
        buffer_size: int = 10,
        pixel_format: str = "YUY2",
    ):
        """
        Initialize camera worker.

        Args:
            camera_id: Camera index (0, 1, ...).
            width: Frame width.
            height: Frame height.
            fps: Target frames per second.
            exposure_us: Manual exposure in microseconds (None = auto).
            backend: OpenCV backend ("dshow" or "msmf").
            buffer_size: Ring buffer size.
            pixel_format: Preferred format ("YUY2" or "MJPG").
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps
        self.exposure_us = exposure_us
        self.backend = backend
        self.pixel_format = pixel_format

        self._buffer = RingBuffer(maxsize=buffer_size)
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_count = 0
        self._drop_count = 0

    def start(self) -> bool:
        """
        Open camera and start capture thread.

        Returns:
            True if successful.
        """
        if self._running:
            logger.warning(f"Camera {self.camera_id} already running")
            return True

        # Open camera
        backend_code = cv2.CAP_DSHOW if self.backend == "dshow" else cv2.CAP_MSMF
        self._cap = cv2.VideoCapture(self.camera_id, backend_code)

        if not self._cap.isOpened():
            logger.error(f"Failed to open camera {self.camera_id}")
            return False

        # Configure camera
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap.set(cv2.CAP_PROP_FPS, self.fps)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal driver buffer

        # Set pixel format via FOURCC (best effort)
        if self.pixel_format == "YUY2":
            fourcc = cv2.VideoWriter_fourcc(*"YUY2")
            self._cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        elif self.pixel_format == "MJPG":
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            self._cap.set(cv2.CAP_PROP_FOURCC, fourcc)

        # Disable auto settings
        self._cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        self._cap.set(cv2.CAP_PROP_AUTO_WB, 0)

        if self.exposure_us is not None:
            # Try to set manual exposure
            self._cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Manual mode
            # Convert microseconds to OpenCV units (negative log2 seconds)
            # For direct value, some drivers accept absolute value
            self._cap.set(cv2.CAP_PROP_EXPOSURE, self.exposure_us)

        # Log negotiated settings
        actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self._cap.get(cv2.CAP_PROP_FPS)
        logger.info(
            f"Camera {self.camera_id} opened: {actual_w}x{actual_h} @ {actual_fps:.1f} fps"
        )

        # Start thread
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

        return True

    def stop(self) -> None:
        """Stop capture and release camera."""
        if not self._running:
            return

        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)

        if self._cap is not None:
            self._cap.release()
            self._cap = None

        logger.info(
            f"Camera {self.camera_id} stopped. "
            f"Captured: {self._frame_count}, Dropped: {self._drop_count}"
        )

    def _capture_loop(self) -> None:
        """Main capture loop (runs in background thread)."""
        while self._running and self._cap is not None:
            ret, frame = self._cap.read()
            if not ret:
                logger.warning(f"Camera {self.camera_id} failed to read frame")
                time.sleep(0.001)
                continue

            # Convert to grayscale immediately
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame

            timestamp = time.perf_counter()
            self._frame_count += 1

            # Check if buffer is full (indicates processing is too slow)
            if self._buffer.size() >= self._buffer._buffer.maxlen - 1:
                self._drop_count += 1

            self._buffer.put((timestamp, gray))

    def get_frame(self) -> Optional[Tuple[float, np.ndarray]]:
        """
        Retrieve next frame from buffer.

        Returns:
            Tuple of (timestamp, frame) or None if empty.
        """
        return self._buffer.get()

    def get_stats(self) -> Dict[str, int]:
        """
        Get capture statistics.

        Returns:
            Dictionary with frame and drop counts.
        """
        return {
            "camera_id": self.camera_id,
            "frame_count": self._frame_count,
            "drop_count": self._drop_count,
            "buffer_size": self._buffer.size(),
        }

    def is_running(self) -> bool:
        """
        Check if worker is running.

        Returns:
            True if running.
        """
        return self._running
