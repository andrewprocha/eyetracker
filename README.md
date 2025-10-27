# DualEyeTracker

Production-ready Python system for real-time, dual-camera pupil tracking on Windows.

## Features

- **High-Speed Capture**: Dual UVC USB cameras at 320×240, targeting 120 fps (tolerates 100–120 fps)
- **IR-Optimized Detection**: Robust pupil detection with eyelash and eyelid suppression
- **Real-Time Processing**: Low-latency threaded capture with synchronized frame pairing
- **Comprehensive Output**: Pupil center, ellipse parameters, quality metrics
- **Optional Visualization**: Live viewer with crosshair and ellipse overlays
- **Data Recording**: CSV telemetry and lossless video recording
- **Production Quality**: Complete test suite, type hints, CI/CD, and documentation

## System Requirements

- **OS**: Windows 10/11
- **Python**: 3.11
- **Hardware**: Two UVC-compliant USB cameras (IR cameras recommended)
- **USB**: Separate USB controllers preferred for optimal performance

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/dual-eye-tracker.git
cd dual-eye-tracker

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install package
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Run live viewer with default config
dual-eye-tracker

# Use specific config preset
dual-eye-tracker --config configs/preset_120fps.yaml

# Record session with telemetry and video
dual-eye-tracker --mode record --output output/session1

# Run FPS benchmark
dual-eye-tracker --mode benchmark --config configs/preset_120fps.yaml
```

### Python API

```python
from dual_eye_tracker.capture.camera_worker import CameraWorker
from dual_eye_tracker.processing.detector import PupilDetector

# Initialize camera
camera = CameraWorker(camera_id=0, width=320, height=240, fps=120)
camera.start()

# Initialize detector
detector = PupilDetector()

# Process frame
timestamp, frame = camera.get_frame()
result = detector.detect(frame)

if result.ok:
    print(f"Pupil center: ({result.center_x:.1f}, {result.center_y:.1f})")
    print(f"Quality: {result.quality:.2f}")

camera.stop()
```

## Configuration

Configuration is managed via YAML files in `configs/`:

- `default.yaml`: Default settings
- `preset_120fps.yaml`: Optimized for 120 FPS with good IR lighting
- `preset_100fps.yaml`: Balanced preset for systems that can't sustain 120 FPS

### Key Configuration Parameters

```yaml
cameras:
  left_id: 0              # Camera index
  right_id: 1
  width: 320              # Frame dimensions
  height: 240
  fps: 120                # Target framerate
  exposure_us: 4000       # Manual exposure (microseconds)
  backend: "dshow"        # DirectShow or MSMF
  pixel_format: "YUY2"    # YUY2 or MJPG

processing:
  eyelid_exclusion_pct: 20.0    # Mask top/bottom percentage
  lash_kernel_length: 15         # Eyelash suppression kernel size
  min_circularity: 0.3           # Minimum shape circularity
  max_eccentricity: 0.95         # Maximum ellipse eccentricity
  min_ring_contrast: 15.0        # Minimum boundary contrast
```

## Hardware Setup

### Camera Requirements

- UVC-compliant USB cameras
- IR cameras strongly recommended for robust pupil detection
- Capable of 320×240 @ 120 fps (or 100 fps minimum)
- Manual exposure control support

### USB Connection

- Connect each camera to a separate USB controller when possible
- Use USB 3.0 ports for best performance
- Avoid USB hubs if experiencing frame drops

### Lighting

- IR illumination recommended (850-940nm wavelength)
- **Safety**: Ensure IR power is within eye-safe limits (IEC 62471)
- Adjust exposure to balance frame rate and image brightness
- Avoid strong glints that may interfere with detection

### Troubleshooting 30 FPS Cap

If cameras are capped at 30 fps:

1. **Check Driver**: Ensure camera drivers are up-to-date
2. **Try MSMF Backend**: Set `backend: "msmf"` in config
3. **Verify Format**: Some cameras may need MJPG instead of YUY2
4. **Use Diagnostic Tool**:
   ```bash
   python scripts/diagnose_caps.py --camera 0 --backend dshow
   ```

## Utility Scripts

### Benchmark FPS

```bash
python scripts/bench_fps.py --config configs/preset_120fps.yaml --duration 5
```

Reports:
- Measured FPS vs. target
- Processing latency statistics
- Pass/fail based on 90% threshold

### Record Demo Session

```bash
python scripts/record_demo.py --config configs/default.yaml --output output/demo
```

Saves:
- `telemetry.csv`: Frame-by-frame pupil data
- `left.avi` / `right.avi`: Lossless video (FFV1 codec)

### Diagnose Camera

```bash
python scripts/diagnose_caps.py --camera 0 --backend dshow
```

Prints negotiated camera settings to verify capabilities.

## Testing

Run test suite:

```bash
# All tests
pytest

# Specific test file
pytest tests/test_processing.py

# With coverage
pytest --cov=dual_eye_tracker

# Verbose output
pytest -v
```

Test coverage includes:
- Synthetic pupil detection (dark disk with eyelashes)
- Frame synchronization with jitter
- Ring buffer operations
- FPS estimation and profiling

## Development

### Code Quality

```bash
# Format code
black dual_eye_tracker/ tests/ scripts/

# Lint
ruff check dual_eye_tracker/ tests/ scripts/

# Type check
mypy dual_eye_tracker/

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### CI/CD

GitHub Actions runs on every push:
- Code formatting (black)
- Linting (ruff)
- Type checking (mypy)
- Test suite (pytest)

## Documentation

- [Lighting Guide](docs/lighting.md): IR safety and exposure recommendations
- [Performance Guide](docs/performance.md): Profiling and optimization
- [Troubleshooting](docs/troubleshooting.md): Common issues and solutions

## Architecture

```
dual_eye_tracker/
├── capture/          # Camera workers, ring buffers, frame sync
├── processing/       # Pupil detection, preprocessing, ellipse fitting
├── ui/               # Real-time viewer with overlays
├── io/               # Telemetry CSV and video writers
└── utils/            # Timing, FPS estimation, profiling
```

### Processing Pipeline

1. **Capture**: Threaded camera workers with minimal driver buffers
2. **Sync**: Timestamp-based pairing with configurable tolerance
3. **Preprocessing**: Eyelid exclusion, eyelash suppression (line morphology)
4. **Segmentation**: Otsu thresholding for dark pupil
5. **Cleanup**: Morphological open/close
6. **Detection**: Contour filtering, ellipse fitting, quality checks
7. **Output**: Center coordinates, axes, angle, quality score

## Example Workflows

### Benchmark Only

```bash
dual-eye-tracker --mode benchmark --config configs/preset_120fps.yaml
```

### Live Visualization

```bash
dual-eye-tracker --config configs/default.yaml
# Press ESC or 'q' to quit
```

### Record Session

```bash
dual-eye-tracker --mode record --config configs/default.yaml --output output/session1
```

Output:
- `output/session1/telemetry.csv`
- `output/session1/left.avi`
- `output/session1/right.avi`

## Performance Expectations

On typical Windows hardware with two UVC IR cameras at 320×240:

- **Target**: 120 fps per camera
- **Acceptable**: ≥100 fps sustained after warmup
- **Benchmark Pass**: ≥90% of target FPS

If performance is insufficient:
- Use `preset_100fps.yaml`
- Disable display during recording
- Reduce processing resolution or use ROI
- Check USB bandwidth and CPU usage

## License

MIT License - see [LICENSE](LICENSE) file.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests and checks pass
5. Submit a pull request

## Citation

If you use DualEyeTracker in research, please cite:

```bibtex
@software{dualeyetracker2025,
  title={DualEyeTracker: Production-Ready Dual-Camera Pupil Tracking},
  author={DualEyeTracker Contributors},
  year={2025},
  url={https://github.com/yourusername/dual-eye-tracker}
}
```

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/dual-eye-tracker/issues)
- **Documentation**: See `docs/` directory
- **Examples**: See `scripts/` directory
