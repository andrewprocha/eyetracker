"""Tests for utility modules."""

import time

import pytest

from dual_eye_tracker.utils.fps_estimator import FPSEstimator
from dual_eye_tracker.utils.profiler import SimpleProfiler
from dual_eye_tracker.utils.timing import Timer


class TestTimer:
    """Tests for Timer."""

    def test_elapsed(self):
        """Test elapsed time measurement."""
        timer = Timer()
        time.sleep(0.1)
        elapsed = timer.elapsed()

        assert 0.09 <= elapsed <= 0.15, f"Elapsed: {elapsed:.3f}s"

    def test_reset(self):
        """Test timer reset."""
        timer = Timer()
        time.sleep(0.05)
        elapsed1 = timer.reset()

        time.sleep(0.05)
        elapsed2 = timer.elapsed()

        assert 0.04 <= elapsed1 <= 0.08
        assert 0.04 <= elapsed2 <= 0.08

    def test_manual_start(self):
        """Test manual start."""
        timer = Timer(auto_start=False)
        assert timer.elapsed() == 0.0

        timer.start()
        time.sleep(0.05)
        elapsed = timer.elapsed()
        assert elapsed > 0.04


class TestFPSEstimator:
    """Tests for FPSEstimator."""

    def test_fps_estimation(self):
        """Test FPS estimation with simulated ticks."""
        fps_est = FPSEstimator(window_size=10)

        # Simulate 60 FPS (16.67ms intervals)
        interval = 1.0 / 60.0

        for _ in range(20):
            fps_est.tick()
            time.sleep(interval)

        estimated_fps = fps_est.get_fps()

        # Should be close to 60 FPS (allow some tolerance)
        assert 50 <= estimated_fps <= 70, f"Estimated FPS: {estimated_fps:.1f}"

    def test_insufficient_data(self):
        """Test behavior with insufficient data."""
        fps_est = FPSEstimator()
        assert fps_est.get_fps() == 0.0

        fps_est.tick()
        assert fps_est.get_fps() == 0.0

    def test_reset(self):
        """Test reset functionality."""
        fps_est = FPSEstimator()

        for _ in range(10):
            fps_est.tick()
            time.sleep(0.01)

        fps_est.reset()
        assert fps_est.get_fps() == 0.0


class TestSimpleProfiler:
    """Tests for SimpleProfiler."""

    def test_basic_profiling(self):
        """Test basic timing operation."""
        prof = SimpleProfiler()

        prof.start("operation")
        time.sleep(0.05)
        prof.stop("operation")

        stats = prof.get_stats("operation")
        assert stats["count"] == 1
        assert 40 <= stats["mean"] <= 80  # ~50ms in milliseconds

    def test_multiple_operations(self):
        """Test multiple operations."""
        prof = SimpleProfiler()

        for _ in range(5):
            prof.start("fast")
            time.sleep(0.01)
            prof.stop("fast")

            prof.start("slow")
            time.sleep(0.02)
            prof.stop("slow")

        fast_stats = prof.get_stats("fast")
        slow_stats = prof.get_stats("slow")

        assert fast_stats["count"] == 5
        assert slow_stats["count"] == 5
        assert slow_stats["mean"] > fast_stats["mean"]

    def test_report_generation(self):
        """Test report generation."""
        prof = SimpleProfiler()

        prof.start("test_op")
        time.sleep(0.01)
        prof.stop("test_op")

        report = prof.report()
        assert "test_op" in report
        assert "mean" in report
        assert "Profiler Report" in report

    def test_get_all_stats(self):
        """Test getting all stats."""
        prof = SimpleProfiler()

        prof.start("op1")
        time.sleep(0.01)
        prof.stop("op1")

        prof.start("op2")
        time.sleep(0.01)
        prof.stop("op2")

        all_stats = prof.get_all_stats()
        assert "op1" in all_stats
        assert "op2" in all_stats
        assert all_stats["op1"]["count"] == 1

    def test_reset(self):
        """Test reset functionality."""
        prof = SimpleProfiler()

        prof.start("op")
        time.sleep(0.01)
        prof.stop("op")

        prof.reset()

        all_stats = prof.get_all_stats()
        assert len(all_stats) == 0
