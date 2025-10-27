"""FPS estimation with moving average."""

import time
from collections import deque
from typing import Optional


class FPSEstimator:
    """Estimates FPS using moving average of frame intervals."""

    def __init__(self, window_size: int = 30):
        """
        Initialize FPS estimator.

        Args:
            window_size: Number of frames to average.
        """
        self._timestamps: deque = deque(maxlen=window_size)
        self._last_time: Optional[float] = None

    def tick(self) -> None:
        """Register a new frame."""
        now = time.perf_counter()
        if self._last_time is not None:
            interval = now - self._last_time
            self._timestamps.append(interval)
        self._last_time = now

    def get_fps(self) -> float:
        """
        Get current FPS estimate.

        Returns:
            Estimated FPS, or 0 if insufficient data.
        """
        if len(self._timestamps) < 2:
            return 0.0

        avg_interval = sum(self._timestamps) / len(self._timestamps)
        if avg_interval == 0:
            return 0.0

        return 1.0 / avg_interval

    def reset(self) -> None:
        """Clear all data."""
        self._timestamps.clear()
        self._last_time = None
