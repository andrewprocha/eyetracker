"""Simple profiler for tracking operation timings."""

import time
from collections import defaultdict
from typing import Dict, List


class SimpleProfiler:
    """Tracks timing statistics for named operations."""

    def __init__(self):
        """Initialize profiler."""
        self._timings: Dict[str, List[float]] = defaultdict(list)
        self._active: Dict[str, float] = {}

    def start(self, name: str) -> None:
        """
        Start timing an operation.

        Args:
            name: Operation name.
        """
        self._active[name] = time.perf_counter()

    def stop(self, name: str) -> None:
        """
        Stop timing an operation.

        Args:
            name: Operation name.
        """
        if name not in self._active:
            return

        elapsed = time.perf_counter() - self._active[name]
        self._timings[name].append(elapsed)
        del self._active[name]

    def get_stats(self, name: str) -> Dict[str, float]:
        """
        Get timing statistics for an operation.

        Args:
            name: Operation name.

        Returns:
            Dictionary with mean, min, max, total (in ms).
        """
        if name not in self._timings or not self._timings[name]:
            return {"mean": 0.0, "min": 0.0, "max": 0.0, "total": 0.0, "count": 0}

        timings = self._timings[name]
        return {
            "mean": sum(timings) / len(timings) * 1000,
            "min": min(timings) * 1000,
            "max": max(timings) * 1000,
            "total": sum(timings) * 1000,
            "count": len(timings),
        }

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics for all operations.

        Returns:
            Dictionary mapping operation names to stats.
        """
        return {name: self.get_stats(name) for name in self._timings}

    def reset(self) -> None:
        """Clear all timing data."""
        self._timings.clear()
        self._active.clear()

    def report(self) -> str:
        """
        Generate text report of all timings.

        Returns:
            Formatted report string.
        """
        lines = ["Profiler Report:", "=" * 60]

        for name, stats in sorted(self.get_all_stats().items()):
            if stats["count"] == 0:
                continue
            lines.append(
                f"{name:30s}  "
                f"mean: {stats['mean']:6.2f} ms  "
                f"min: {stats['min']:6.2f} ms  "
                f"max: {stats['max']:6.2f} ms  "
                f"(n={stats['count']})"
            )

        return "\n".join(lines)
