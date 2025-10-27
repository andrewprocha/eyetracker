"""CSV telemetry writer for gaze data."""

import csv
import logging
from pathlib import Path
from typing import Optional, TextIO

from dual_eye_tracker.processing.result import DetectionResult

logger = logging.getLogger(__name__)


class TelemetryWriter:
    """Writes frame-by-frame telemetry to CSV."""

    def __init__(self, output_path: Path):
        """
        Initialize telemetry writer.

        Args:
            output_path: Path to output CSV file.
        """
        self.output_path = output_path
        self._file: Optional[TextIO] = None
        self._writer: Optional[csv.DictWriter] = None
        self._row_count = 0

        # CSV columns
        self._fieldnames = [
            "timestamp",
            "left_ok",
            "left_cx",
            "left_cy",
            "left_major",
            "left_minor",
            "left_angle",
            "left_quality",
            "left_eccentricity",
            "left_area",
            "right_ok",
            "right_cx",
            "right_cy",
            "right_major",
            "right_minor",
            "right_angle",
            "right_quality",
            "right_eccentricity",
            "right_area",
        ]

    def open(self) -> None:
        """Open CSV file and write header."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.output_path, "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=self._fieldnames)
        self._writer.writeheader()
        logger.info(f"Telemetry file opened: {self.output_path}")

    def write_pair(
        self, timestamp: float, left: DetectionResult, right: DetectionResult
    ) -> None:
        """
        Write detection pair to CSV.

        Args:
            timestamp: Frame timestamp.
            left: Left eye detection.
            right: Right eye detection.
        """
        if self._writer is None:
            raise RuntimeError("TelemetryWriter not opened")

        row = {
            "timestamp": f"{timestamp:.6f}",
            "left_ok": int(left.ok),
            "left_cx": f"{left.center_x:.2f}" if left.ok else "",
            "left_cy": f"{left.center_y:.2f}" if left.ok else "",
            "left_major": f"{left.axis_major:.2f}" if left.ok else "",
            "left_minor": f"{left.axis_minor:.2f}" if left.ok else "",
            "left_angle": f"{left.angle:.2f}" if left.ok else "",
            "left_quality": f"{left.quality:.3f}" if left.ok else "",
            "left_eccentricity": f"{left.eccentricity:.3f}" if left.ok else "",
            "left_area": f"{left.area:.1f}" if left.ok else "",
            "right_ok": int(right.ok),
            "right_cx": f"{right.center_x:.2f}" if right.ok else "",
            "right_cy": f"{right.center_y:.2f}" if right.ok else "",
            "right_major": f"{right.axis_major:.2f}" if right.ok else "",
            "right_minor": f"{right.axis_minor:.2f}" if right.ok else "",
            "right_angle": f"{right.angle:.2f}" if right.ok else "",
            "right_quality": f"{right.quality:.3f}" if right.ok else "",
            "right_eccentricity": f"{right.eccentricity:.3f}" if right.ok else "",
            "right_area": f"{right.area:.1f}" if right.ok else "",
        }

        self._writer.writerow(row)
        self._row_count += 1

    def close(self) -> None:
        """Close CSV file."""
        if self._file is not None:
            self._file.close()
            self._file = None
            self._writer = None
            logger.info(f"Telemetry file closed: {self._row_count} rows written")
