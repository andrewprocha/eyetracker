"""Detection result data structure."""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class DetectionResult:
    """Result of pupil detection on a single frame."""

    ok: bool
    """Whether detection succeeded."""

    center_x: float = 0.0
    """Pupil center X coordinate."""

    center_y: float = 0.0
    """Pupil center Y coordinate."""

    axis_major: float = 0.0
    """Major axis length."""

    axis_minor: float = 0.0
    """Minor axis length."""

    angle: float = 0.0
    """Rotation angle in degrees."""

    quality: float = 0.0
    """Quality metric (0-1), e.g., ring contrast."""

    eccentricity: float = 0.0
    """Ellipse eccentricity (0=circle, 1=line)."""

    area: float = 0.0
    """Contour area in pixels."""

    @property
    def center(self) -> Tuple[float, float]:
        """Return center as (x, y) tuple."""
        return (self.center_x, self.center_y)

    @property
    def axes(self) -> Tuple[float, float]:
        """Return axes as (major, minor) tuple."""
        return (self.axis_major, self.axis_minor)

    @classmethod
    def failed(cls) -> "DetectionResult":
        """Create a failed detection result."""
        return cls(ok=False)

    def __repr__(self) -> str:
        if not self.ok:
            return "DetectionResult(ok=False)"
        return (
            f"DetectionResult(ok=True, center=({self.center_x:.1f},{self.center_y:.1f}), "
            f"axes=({self.axis_major:.1f},{self.axis_minor:.1f}), "
            f"quality={self.quality:.2f})"
        )
