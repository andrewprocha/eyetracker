"""Frame synchronization for dual cameras."""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class FrameSynchronizer:
    """Pairs frames from two cameras by nearest timestamp."""

    def __init__(self, tolerance_ms: float = 5.0):
        """
        Initialize synchronizer.

        Args:
            tolerance_ms: Maximum time difference for pairing (milliseconds).
        """
        self.tolerance_s = tolerance_ms / 1000.0
        self._left_queue: List[Tuple[float, np.ndarray]] = []
        self._right_queue: List[Tuple[float, np.ndarray]] = []
        self._paired_count = 0
        self._dropped_left = 0
        self._dropped_right = 0

    def add_left(self, timestamp: float, frame: np.ndarray) -> None:
        """
        Add frame from left camera.

        Args:
            timestamp: Capture timestamp.
            frame: Frame data.
        """
        self._left_queue.append((timestamp, frame))
        self._trim_queue(self._left_queue)

    def add_right(self, timestamp: float, frame: np.ndarray) -> None:
        """
        Add frame from right camera.

        Args:
            timestamp: Capture timestamp.
            frame: Frame data.
        """
        self._right_queue.append((timestamp, frame))
        self._trim_queue(self._right_queue)

    def _trim_queue(self, queue: List[Tuple[float, np.ndarray]], max_size: int = 20) -> None:
        """Keep queue size bounded by dropping oldest frames."""
        if len(queue) > max_size:
            dropped = len(queue) - max_size
            if queue is self._left_queue:
                self._dropped_left += dropped
            else:
                self._dropped_right += dropped
            queue[:] = queue[-max_size:]

    def get_pair(self) -> Optional[Tuple[float, np.ndarray, np.ndarray]]:
        """
        Retrieve synchronized pair if available.

        Returns:
            Tuple of (timestamp, left_frame, right_frame) or None.
        """
        if not self._left_queue or not self._right_queue:
            return None

        # Find best match
        left_ts, left_frame = self._left_queue[0]
        best_idx = -1
        best_diff = float("inf")

        for i, (right_ts, _) in enumerate(self._right_queue):
            diff = abs(left_ts - right_ts)
            if diff < best_diff:
                best_diff = diff
                best_idx = i

        # Check tolerance
        if best_diff > self.tolerance_s:
            # No match within tolerance, drop oldest left frame
            self._left_queue.pop(0)
            self._dropped_left += 1
            return None

        # Valid pair found
        right_ts, right_frame = self._right_queue.pop(best_idx)
        self._left_queue.pop(0)
        self._paired_count += 1

        # Use average timestamp
        avg_ts = (left_ts + right_ts) / 2.0
        return (avg_ts, left_frame, right_frame)

    def get_stats(self) -> Dict[str, int]:
        """
        Get synchronization statistics.

        Returns:
            Dictionary with pairing and drop counts.
        """
        return {
            "paired_count": self._paired_count,
            "dropped_left": self._dropped_left,
            "dropped_right": self._dropped_right,
            "queue_left": len(self._left_queue),
            "queue_right": len(self._right_queue),
        }

    def clear(self) -> None:
        """Clear all queued frames."""
        self._left_queue.clear()
        self._right_queue.clear()
