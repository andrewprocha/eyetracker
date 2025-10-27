"""Tests for camera capture and synchronization."""

import time

import numpy as np
import pytest

from dual_eye_tracker.capture.ring_buffer import RingBuffer
from dual_eye_tracker.capture.sync import FrameSynchronizer


class TestRingBuffer:
    """Tests for RingBuffer."""

    def test_put_get(self):
        """Test basic put/get operations."""
        buf = RingBuffer(maxsize=5)

        assert buf.is_empty()
        assert buf.size() == 0

        buf.put("item1")
        buf.put("item2")

        assert buf.size() == 2
        assert not buf.is_empty()

        item = buf.get()
        assert item == "item1"
        assert buf.size() == 1

    def test_overflow(self):
        """Test buffer overflow behavior."""
        buf = RingBuffer(maxsize=3)

        for i in range(5):
            buf.put(f"item{i}")

        # Should only contain last 3 items
        assert buf.size() == 3

        items = buf.peek_all()
        assert items == ["item2", "item3", "item4"]

    def test_clear(self):
        """Test clear operation."""
        buf = RingBuffer(maxsize=5)
        buf.put("item1")
        buf.put("item2")

        buf.clear()
        assert buf.is_empty()
        assert buf.size() == 0

    def test_empty_get(self):
        """Test get from empty buffer."""
        buf = RingBuffer(maxsize=5)
        item = buf.get()
        assert item is None


class TestFrameSynchronizer:
    """Tests for FrameSynchronizer."""

    def test_basic_pairing(self):
        """Test basic frame pairing."""
        sync = FrameSynchronizer(tolerance_ms=5.0)

        # Create dummy frames
        left_frame = np.zeros((240, 320), dtype=np.uint8)
        right_frame = np.ones((240, 320), dtype=np.uint8)

        # Add frames with close timestamps
        sync.add_left(1.000, left_frame)
        sync.add_right(1.001, right_frame)

        # Should get a pair
        pair = sync.get_pair()
        assert pair is not None

        timestamp, left, right = pair
        assert 1.0 <= timestamp <= 1.001
        assert np.array_equal(left, left_frame)
        assert np.array_equal(right, right_frame)

        # Stats should show 1 paired frame
        stats = sync.get_stats()
        assert stats["paired_count"] == 1

    def test_out_of_tolerance(self):
        """Test rejection of frames outside tolerance."""
        sync = FrameSynchronizer(tolerance_ms=5.0)

        left_frame = np.zeros((240, 320), dtype=np.uint8)
        right_frame = np.ones((240, 320), dtype=np.uint8)

        # Add frames with large time difference
        sync.add_left(1.000, left_frame)
        sync.add_right(1.020, right_frame)  # 20ms difference

        # Should not pair (>5ms tolerance)
        pair = sync.get_pair()
        # First call drops left frame, no pair yet
        assert pair is None

        # Stats should show dropped frame
        stats = sync.get_stats()
        assert stats["dropped_left"] >= 1

    def test_simulated_jitter(self):
        """Test pairing with realistic timestamp jitter."""
        sync = FrameSynchronizer(tolerance_ms=5.0)

        # Simulate 10 frames from each camera with small jitter
        np.random.seed(42)
        base_time = 1.0
        frame_interval = 1.0 / 120.0  # 120 FPS

        for i in range(10):
            t_base = base_time + i * frame_interval
            left_jitter = np.random.uniform(-0.001, 0.001)
            right_jitter = np.random.uniform(-0.001, 0.001)

            left_frame = np.full((240, 320), i, dtype=np.uint8)
            right_frame = np.full((240, 320), i + 100, dtype=np.uint8)

            sync.add_left(t_base + left_jitter, left_frame)
            sync.add_right(t_base + right_jitter, right_frame)

        # Should pair most frames
        paired_count = 0
        while True:
            pair = sync.get_pair()
            if pair is None:
                break
            paired_count += 1

        # Should successfully pair most frames (allow 1-2 to remain unpaired)
        assert paired_count >= 8, f"Only paired {paired_count}/10 frames"

    def test_clear(self):
        """Test clearing queues."""
        sync = FrameSynchronizer(tolerance_ms=5.0)

        frame = np.zeros((240, 320), dtype=np.uint8)
        sync.add_left(1.0, frame)
        sync.add_right(1.0, frame)

        sync.clear()

        stats = sync.get_stats()
        assert stats["queue_left"] == 0
        assert stats["queue_right"] == 0


class TestCameraWorker:
    """Tests for CameraWorker (requires actual camera)."""

    @pytest.mark.skipif(
        True, reason="Requires physical camera; enable manually for hardware testing"
    )
    def test_camera_capture(self):
        """Test camera capture (requires camera at index 0)."""
        from dual_eye_tracker.capture.camera_worker import CameraWorker

        worker = CameraWorker(
            camera_id=0, width=320, height=240, fps=120, backend="dshow"
        )

        assert worker.start()

        # Wait for some frames
        time.sleep(1.0)

        # Should have captured frames
        frame_data = worker.get_frame()
        assert frame_data is not None

        timestamp, frame = frame_data
        assert frame.shape == (240, 320)
        assert frame.dtype == np.uint8

        # Get stats
        stats = worker.get_stats()
        assert stats["frame_count"] > 0

        worker.stop()
