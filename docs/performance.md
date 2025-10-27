# Performance Guide for DualEyeTracker

## Performance Targets

**Goal**: Sustained ≥100 fps per camera with real-time processing

**Benchmark Criteria:**
- Measured FPS ≥90% of target FPS
- Processing latency <8ms per frame
- Frame drop rate <5%
- Synchronization drop rate <10%

## Profiling Your System

### Run Benchmark

```bash
python scripts/bench_fps.py --config configs/preset_120fps.yaml --duration 10 --warmup 3
```

Output includes:
- Measured FPS vs. target
- Detection latency statistics (mean, min, max)
- Frame and drop counts
- Pass/fail status

### Interpret Results

**Good Performance (PASS):**
```
Target FPS:      120.0
Measured FPS:    118.3
FPS Ratio:       98.6%
Detection Rate:  94.2%
detect           mean:   3.21 ms  min:   2.87 ms  max:   5.43 ms
```

**Insufficient Performance (FAIL):**
```
Target FPS:      120.0
Measured FPS:    87.4
FPS Ratio:       72.8%  <- Below 90% threshold
Detection Rate:  81.3%
detect           mean:   6.82 ms  min:   4.21 ms  max:  12.34 ms
```

## Optimization Strategies

### 1. Reduce Target FPS

If you can't sustain 120 fps, try 100 fps:

```yaml
cameras:
  fps: 100
  exposure_us: 6000
```

Trade-off: Lower temporal resolution, but more reliable capture.

### 2. Optimize Camera Backend

Try both DirectShow and MSMF:

```bash
# Test DirectShow
python scripts/bench_fps.py --config configs/preset_120fps.yaml

# Modify config to use MSMF
# backend: "msmf"

# Test MSMF
python scripts/bench_fps.py --config configs/preset_120fps.yaml
```

Typically DirectShow is faster, but MSMF may work better with certain cameras.

### 3. Disable Display During Recording

Visual rendering adds overhead. For recording sessions:

```yaml
ui:
  enable_display: false
  save_telemetry: true
  save_video: true
```

Or use headless mode in code:

```python
viewer = DualEyeViewer(enable_display=False)
```

### 4. Tune Processing Parameters

Reduce computational cost:

```yaml
processing:
  lash_kernel_length: 11          # Smaller kernel (was 15)
  morph_open_size: 2              # Smaller morphology (was 3)
  morph_close_size: 3             # Smaller closing (was 5)
  eyelid_exclusion_pct: 15.0      # Reduce masked area (was 20)
```

Trade-off: Slightly less robust to eyelashes, but faster.

### 5. Use ROI (Region of Interest)

If you know the approximate pupil location, crop frames before processing:

```python
# Example: Process only central 200x200 region
def crop_roi(frame):
    h, w = frame.shape
    cx, cy = w // 2, h // 2
    x1, y1 = cx - 100, cy - 100
    x2, y2 = cx + 100, cy + 100
    return frame[y1:y2, x1:x2]

roi_frame = crop_roi(full_frame)
result = detector.detect(roi_frame)
```

Trade-off: Must ensure pupil stays within ROI.

### 6. Optimize USB Bandwidth

- Connect cameras to separate USB controllers
- Use USB 3.0 ports (even for USB 2.0 cameras)
- Avoid USB hubs
- Close other USB-intensive applications

Check USB topology:

```
Windows Device Manager → Universal Serial Bus controllers
```

Ensure cameras are on different root hubs if possible.

### 7. Pixel Format Selection

Try different formats:

```yaml
cameras:
  pixel_format: "YUY2"   # Uncompressed, higher bandwidth
  # OR
  pixel_format: "MJPG"   # Compressed, lower bandwidth, higher CPU for decode
```

Benchmark both to see which performs better on your system.

## System Resource Monitoring

### CPU Usage

DualEyeTracker is CPU-bound. Monitor during operation:

**Task Manager (Windows):**
- Look for `python.exe` process
- Should use 15-30% of a modern 8-core CPU at 120 fps

**High CPU (>50%):**
- Reduce FPS target
- Disable display
- Simplify processing parameters
- Check for other background processes

### Memory Usage

Typical usage: 200-500 MB

**High Memory (>1 GB):**
- Ring buffer size may be too large (default is 10 frames per camera)
- Check for memory leaks (run for extended period and monitor)

### Disk I/O (Recording Mode)

Lossless video (FFV1 codec) is CPU-intensive but creates large files:

**Alternatives:**
- Use lossy MJPG codec: `codec: "MJPG"` in `DualVideoWriter`
- Record telemetry only (CSV is tiny)
- Record video at lower FPS than capture FPS (subsample)

## Common Bottlenecks

### 1. Camera Driver Buffering

**Symptom**: Constant frame drops, old frames returned

**Fix**:
```python
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer
```

Already set in `CameraWorker`, but some drivers ignore this.

### 2. GIL Contention (Python Global Interpreter Lock)

**Symptom**: Adding more cameras doesn't scale linearly

**Mitigation**: DualEyeTracker uses threads with NumPy/OpenCV operations that release GIL. If needed, consider multiprocessing for processing pipeline.

### 3. OpenCV VideoCapture Performance

Some cameras have poor OpenCV support. If FPS is capped:

**Try**:
- Different backend (DSHOW vs. MSMF)
- Latest camera firmware
- Alternative camera model with better UVC compliance

## Benchmarking Checklist

Before deploying:

- [ ] Run `bench_fps.py` with target config for ≥10 seconds
- [ ] Verify ≥90% of target FPS
- [ ] Check detection rate >85%
- [ ] Monitor CPU usage <50%
- [ ] Test sustained operation (≥5 minutes) for thermal throttling
- [ ] Verify synchronization drop rate <10%

## Platform-Specific Notes

### Windows 10/11

- DirectShow generally faster than MSMF
- Windows Camera app may interfere (close it)
- Power settings: Set to "High Performance" mode
- Disable USB selective suspend:
  - Control Panel → Power Options → Change plan settings → Advanced
  - USB settings → USB selective suspend → Disabled

### Laptop vs. Desktop

**Laptop Considerations:**
- Thermal throttling after a few minutes (use cooling pad)
- Shared USB controllers (limits bandwidth)
- Power management (disable to prevent camera sleep)

**Desktop Advantages:**
- Separate USB controllers (use different motherboard ports)
- Better sustained performance (no thermal throttling)
- More CPU cores for higher FPS

## Advanced: Custom Processing Pipeline

For maximum performance, implement custom pipeline:

```python
from dual_eye_tracker.utils.profiler import SimpleProfiler

profiler = SimpleProfiler()

while running:
    profiler.start("capture")
    left_frame = left_cam.get_frame()
    right_frame = right_cam.get_frame()
    profiler.stop("capture")

    profiler.start("sync")
    # ... synchronization ...
    profiler.stop("sync")

    profiler.start("detect")
    result = detector.detect(frame)
    profiler.stop("detect")

# Print profiling report
print(profiler.report())
```

Identify bottlenecks and optimize accordingly.

## Support

If performance issues persist:
1. Run diagnostic: `python scripts/diagnose_caps.py`
2. Run benchmark with profiling: `python scripts/bench_fps.py`
3. Check GitHub issues for similar problems
4. Open new issue with benchmark output and system specs
