#!/usr/bin/env python3
"""Diagnose camera capabilities and negotiated settings."""

import logging
import sys
from pathlib import Path

import cv2

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def diagnose_camera(camera_id: int, backend: str = "dshow") -> None:
    """
    Print negotiated camera settings.

    Args:
        camera_id: Camera index.
        backend: Backend to use.
    """
    backend_code = cv2.CAP_DSHOW if backend == "dshow" else cv2.CAP_MSMF

    logger.info(f"Opening camera {camera_id} with {backend}...")
    cap = cv2.VideoCapture(camera_id, backend_code)

    if not cap.isOpened():
        logger.error(f"Failed to open camera {camera_id}")
        return

    # Try to set high FPS
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 120)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # Read negotiated values
    props = {
        "FRAME_WIDTH": cv2.CAP_PROP_FRAME_WIDTH,
        "FRAME_HEIGHT": cv2.CAP_PROP_FRAME_HEIGHT,
        "FPS": cv2.CAP_PROP_FPS,
        "FOURCC": cv2.CAP_PROP_FOURCC,
        "BUFFERSIZE": cv2.CAP_PROP_BUFFERSIZE,
        "EXPOSURE": cv2.CAP_PROP_EXPOSURE,
        "AUTO_EXPOSURE": cv2.CAP_PROP_AUTO_EXPOSURE,
        "AUTOFOCUS": cv2.CAP_PROP_AUTOFOCUS,
        "AUTO_WB": cv2.CAP_PROP_AUTO_WB,
        "BRIGHTNESS": cv2.CAP_PROP_BRIGHTNESS,
        "CONTRAST": cv2.CAP_PROP_CONTRAST,
        "GAIN": cv2.CAP_PROP_GAIN,
    }

    logger.info("=" * 60)
    logger.info(f"Camera {camera_id} ({backend}) Properties:")
    logger.info("=" * 60)

    for name, prop in props.items():
        value = cap.get(prop)
        if name == "FOURCC":
            # Decode FOURCC
            fourcc_int = int(value)
            fourcc_str = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)])
            logger.info(f"{name:20s}: {fourcc_int} ({fourcc_str})")
        else:
            logger.info(f"{name:20s}: {value}")

    # Test frame capture
    logger.info("")
    logger.info("Testing frame capture...")
    ret, frame = cap.read()

    if ret:
        logger.info(f"Frame captured: {frame.shape}, dtype: {frame.dtype}")
    else:
        logger.error("Failed to capture frame")

    cap.release()
    logger.info("=" * 60)


def main() -> int:
    """Main entry."""
    import argparse

    parser = argparse.ArgumentParser(description="Diagnose camera capabilities")
    parser.add_argument("--camera", type=int, default=0, help="Camera ID")
    parser.add_argument(
        "--backend", choices=["dshow", "msmf"], default="dshow", help="Backend"
    )

    args = parser.parse_args()

    diagnose_camera(args.camera, args.backend)
    return 0


if __name__ == "__main__":
    sys.exit(main())
