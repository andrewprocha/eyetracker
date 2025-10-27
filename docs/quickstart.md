# Quick Start Guide for DualEyeTracker

## 5-Minute Setup

### Prerequisites

- Windows 10 or 11
- Python 3.11
- Two USB cameras (IR cameras recommended)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/dual-eye-tracker.git
cd dual-eye-tracker

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install package
pip install -e .
```

### First Run

```bash
# Run with default settings
dual-eye-tracker
```

Press `ESC` or `q` to quit.

### Verify Cameras

If cameras don't open, find correct camera IDs:

```bash
python scripts/diagnose_caps.py --camera 0
python scripts/diagnose_caps.py --camera 1
python scripts/diagnose_caps.py --camera 2
```

Update `configs/default.yaml`:

```yaml
cameras:
  left_id: 0   # Your left camera ID
  right_id: 1  # Your right camera ID
```

## Basic Workflows

### 1. Live Viewing

View both eyes in real-time with detection overlays:

```bash
dual-eye-tracker --config configs/default.yaml
```

What you'll see:
- Two windows (left and right eye)
- Green crosshair on detected pupil center
- Yellow ellipse around pupil
- FPS counter (top left)
- Quality score (bottom left)

### 2. Record a Session

Record telemetry and video:

```bash
dual-eye-tracker --mode record --output output/my_session
```

Output files:
- `output/my_session/telemetry.csv` - Frame-by-frame data
- `output/my_session/left.avi` - Left camera video
- `output/my_session/right.avi` - Right camera video

### 3. Run Benchmark

Test if your system can achieve target FPS:

```bash
dual-eye-tracker --mode benchmark --config configs/preset_120fps.yaml
```

Look for:
- `FPS Ratio: XX.X%` (should be ≥90%)
- `Benchmark PASSED` at end

## Understanding the Output

### Telemetry CSV

Each row contains one synchronized frame pair:

| Column | Description |
|--------|-------------|
| `timestamp` | Capture time (seconds since start) |
| `left_ok` | 1 if left pupil detected, 0 otherwise |
| `left_cx`, `left_cy` | Left pupil center (pixels) |
| `left_major`, `left_minor` | Ellipse axes (pixels) |
| `left_angle` | Rotation angle (degrees) |
| `left_quality` | Detection quality (0-1) |
| `left_eccentricity` | Ellipse eccentricity (0=circle, 1=line) |
| `left_area` | Contour area (pixels) |
| `right_*` | Same for right eye |

### Reading Telemetry

```python
import pandas as pd

df = pd.read_csv("output/my_session/telemetry.csv")

# Filter successful detections
valid = df[df["left_ok"] == 1]

# Get pupil positions
left_x = valid["left_cx"]
left_y = valid["left_cy"]

# Calculate statistics
print(f"Mean position: ({left_x.mean():.1f}, {left_y.mean():.1f})")
print(f"Detection rate: {valid.shape[0] / df.shape[0] * 100:.1f}%")
```

## Configuration Basics

### Edit Configuration

Copy and modify a preset:

```bash
copy configs\preset_120fps.yaml configs\my_config.yaml
```

Edit `configs/my_config.yaml`:

```yaml
cameras:
  left_id: 0
  right_id: 1
  fps: 100           # Reduce if 120 is too high
  exposure_us: 5000  # Increase for more light

processing:
  min_ring_contrast: 12.0  # Lower for easier detection
  min_circularity: 0.25    # Less strict shape requirement
```

Use your config:

```bash
dual-eye-tracker --config configs/my_config.yaml
```

### Key Parameters to Adjust

**If detection fails:**
- Decrease `min_ring_contrast` (try 10.0)
- Decrease `min_circularity` (try 0.25)
- Increase `max_eccentricity` (try 0.98)

**If eyelashes interfere:**
- Increase `eyelid_exclusion_pct` (try 25.0)
- Increase `lash_kernel_length` (try 20)

**If FPS is too low:**
- Decrease `fps` (try 100 or 60)
- Set `enable_display: false`
- Use `preset_100fps.yaml`

## Next Steps

### Improve Detection

1. **Optimize Lighting** - See [lighting.md](lighting.md)
   - Use IR LEDs for best results
   - Adjust exposure for good contrast
   - Avoid glints

2. **Tune Parameters** - See [troubleshooting.md](troubleshooting.md)
   - Start with presets
   - Adjust based on your specific cameras and lighting

### Analyze Data

1. **Load in Python:**
   ```python
   import pandas as pd
   df = pd.read_csv("output/my_session/telemetry.csv")
   ```

2. **Plot Gaze Position:**
   ```python
   import matplotlib.pyplot as plt

   plt.figure(figsize=(10, 5))
   plt.subplot(1, 2, 1)
   plt.plot(df["left_cx"], df["left_cy"], ".", alpha=0.5)
   plt.title("Left Eye Position")
   plt.xlabel("X (pixels)")
   plt.ylabel("Y (pixels)")

   plt.subplot(1, 2, 2)
   plt.plot(df["right_cx"], df["right_cy"], ".", alpha=0.5)
   plt.title("Right Eye Position")
   plt.show()
   ```

3. **Compute Metrics:**
   - Pupil diameter: `(major + minor) / 2`
   - Gaze disparity: `sqrt((left_cx - right_cx)**2 + (left_cy - right_cy)**2)`
   - Blink detection: `left_ok == 0 and right_ok == 0`

### Advanced Usage

- **Python API** - Integrate into your own code (see README.md)
- **Custom Processing** - Extend `PupilDetector` class
- **Real-Time Control** - Modify `main.py` for interactive experiments

## Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| Camera not found | Run `diagnose_caps.py` to find camera ID |
| FPS too low | Use `preset_100fps.yaml` |
| No detection | Increase lighting, lower `min_ring_contrast` |
| High CPU | Reduce FPS, set `enable_display: false` |
| Frame drops | Connect cameras to different USB ports |

See [troubleshooting.md](troubleshooting.md) for detailed solutions.

## Getting Help

- **Documentation**: Check `docs/` folder
- **Examples**: See `scripts/` for usage examples
- **Issues**: [GitHub Issues](https://github.com/yourusername/dual-eye-tracker/issues)

## Example Session

Complete workflow from installation to analysis:

```bash
# 1. Setup
git clone https://github.com/yourusername/dual-eye-tracker.git
cd dual-eye-tracker
python -m venv venv
venv\Scripts\activate
pip install -e ".[dev]"

# 2. Test cameras
python scripts/diagnose_caps.py --camera 0
python scripts/diagnose_caps.py --camera 1

# 3. Run benchmark
dual-eye-tracker --mode benchmark

# 4. Record session
dual-eye-tracker --mode record --output output/session1

# 5. Analyze data
python
>>> import pandas as pd
>>> df = pd.read_csv("output/session1/telemetry.csv")
>>> print(df.head())
>>> print(f"Detection rate: {df['left_ok'].mean() * 100:.1f}%")
```

Congratulations! You're now tracking eyes at high speed.
