"""Video writer for dual camera streams."""

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class DualVideoWriter:
    """Writes dual camera streams to video files."""

    def __init__(
        self,
        left_path: Path,
        right_path: Path,
        fps: float = 120.0,
        codec: str = "FFV1",
        width: int = 320,
        height: int = 240,
    ):
        """
        Initialize video writer.

        Args:
            left_path: Output path for left camera.
            right_path: Output path for right camera.
            fps: Recording framerate.
            codec: FourCC codec (FFV1 = lossless, MJPG = lossy).
            width: Frame width.
            height: Frame height.
        """
        self.left_path = left_path
        self.right_path = right_path
        self.fps = fps
        self.codec = codec
        self.width = width
        self.height = height

        self._left_writer: Optional[cv2.VideoWriter] = None
        self._right_writer: Optional[cv2.VideoWriter] = None
        self._frame_count = 0

    def open(self) -> None:
        """Open video writers."""
        self.left_path.parent.mkdir(parents=True, exist_ok=True)
        self.right_path.parent.mkdir(parents=True, exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*self.codec)

        self._left_writer = cv2.VideoWriter(
            str(self.left_path), fourcc, self.fps, (self.width, self.height), False
        )
        self._right_writer = cv2.VideoWriter(
            str(self.right_path), fourcc, self.fps, (self.width, self.height), False
        )

        if not self._left_writer.isOpened() or not self._right_writer.isOpened():
            raise RuntimeError("Failed to open video writers")

        logger.info(f"Video writers opened: {self.left_path}, {self.right_path}")

    def write_pair(self, left_frame: np.ndarray, right_frame: np.ndarray) -> None:
        """
        Write frame pair.

        Args:
            left_frame: Left camera frame (grayscale).
            right_frame: Right camera frame (grayscale).
        """
        if self._left_writer is None or self._right_writer is None:
            raise RuntimeError("DualVideoWriter not opened")

        self._left_writer.write(left_frame)
        self._right_writer.write(right_frame)
        self._frame_count += 1

    def close(self) -> None:
        """Release video writers."""
        if self._left_writer is not None:
            self._left_writer.release()
            self._left_writer = None

        if self._right_writer is not None:
            self._right_writer.release()
            self._right_writer = None

        logger.info(f"Video writers closed: {self._frame_count} frames written")
