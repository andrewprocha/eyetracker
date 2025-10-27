#!/usr/bin/env python3
"""Record a demo session with telemetry and video."""

import logging
import sys
from pathlib import Path

import yaml

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dual_eye_tracker.main import run_live_viewer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> int:
    """Record a demo session."""
    import argparse

    parser = argparse.ArgumentParser(description="Record demo session")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/default.yaml"),
        help="Config file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/demo"),
        help="Output directory",
    )
    parser.add_argument(
        "--duration",
        type=float,
        help="Duration in seconds (None = until user quits)",
    )

    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    # Enable recording
    config["ui"]["save_telemetry"] = True
    config["ui"]["save_video"] = True

    logger.info(f"Recording to: {args.output}")
    logger.info("Press ESC or 'q' to stop")

    return run_live_viewer(config, args.output)


if __name__ == "__main__":
    sys.exit(main())
