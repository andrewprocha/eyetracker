"""Timing utilities."""

import time
from typing import Optional


class Timer:
    """Simple timer for measuring elapsed time."""

    def __init__(self, auto_start: bool = True):
        """
        Initialize timer.

        Args:
            auto_start: Whether to start timer immediately.
        """
        self._start_time: Optional[float] = None
        if auto_start:
            self.start()

    def start(self) -> None:
        """Start or restart timer."""
        self._start_time = time.perf_counter()

    def elapsed(self) -> float:
        """
        Get elapsed time in seconds.

        Returns:
            Elapsed time since start.
        """
        if self._start_time is None:
            return 0.0
        return time.perf_counter() - self._start_time

    def reset(self) -> float:
        """
        Reset timer and return elapsed time.

        Returns:
            Elapsed time before reset.
        """
        elapsed = self.elapsed()
        self.start()
        return elapsed
