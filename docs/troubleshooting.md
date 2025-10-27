# Troubleshooting Guide for DualEyeTracker

## Common Issues and Solutions

### Camera Not Detected

**Error**: `Failed to open camera 0`

**Causes & Solutions:**

1. **Wrong Camera ID**
   ```bash
   # Test different camera IDs
   python scripts/diagnose_caps.py --camera 0
   python scripts/diagnose_caps.py --camera 1
   python scripts/diagnose_caps.py --camera 2
   ```

2. **Camera In Use**
   - Close other applications using the camera (Zoom, Skype, Windows Camera app)
   - Check Task Manager for processes holding camera

3. **Driver Issues**
   - Update camera drivers from manufacturer
   - Try different USB port
   - Restart computer

4. **Permissions**
   - Ensure Python has camera access (Windows Settings → Privacy → Camera)

### Frame Rate Capped at 30 FPS

**Symptom**: Camera reports 30 fps instead of 120 fps

**Solutions:**

1. **Try DirectShow Backend**
   ```yaml
   cameras:
     backend: "dshow"  # Usually better than MSMF
   ```

2. **Check Camera Capabilities**
   ```bash
   python scripts/diagnose_caps.py --camera 0 --backend dshow
   ```
   Look for `FPS` property - if it shows 30, camera may not support 120 fps at 320×240.

3. **Try MJPG Format**
   ```yaml
   cameras:
     pixel_format: "MJPG"  # May enable higher FPS on some cameras
   ```

4. **Verify Camera Specs**
   - Confirm camera actually supports 120 fps at 320×240
   - Some cameras require specific drivers or software

5. **Windows Camera Settings**
   - Some cameras have configuration utilities (check manufacturer website)
   - May need to enable "high speed mode" in camera settings

### Pupil Detection Failing

**Symptom**: `result.ok = False` or low detection rate

**Causes & Solutions:**

1. **Poor Lighting**
   - Increase IR illumination
   - Adjust exposure: `exposure_us: 6000` (longer exposure for more light)
   - Check histogram with diagnostic tool

2. **Tune Detection Parameters**
   ```yaml
   processing:
     min_ring_contrast: 10.0    # Lower threshold (was 15.0)
     min_circularity: 0.25      # Less strict (was 0.3)
     max_eccentricity: 0.98     # Allow more elliptical (was 0.95)
   ```

3. **Eyelid/Eyelash Interference**
   ```yaml
   processing:
     eyelid_exclusion_pct: 25.0   # Mask more of top/bottom (was 20.0)
     lash_kernel_length: 20        # Stronger suppression (was 15)
   ```

4. **Area Constraints**
   - If pupil is very small or large, adjust:
   ```yaml
   processing:
     min_area: 30        # Lower for small pupils (was 50)
     max_area: 8000      # Higher for large pupils (was 5000)
   ```

5. **Debug Visualization**
   ```python
   from dual_eye_tracker.processing.detector import PupilDetector
   detector = PupilDetector()

   # Generate debug image showing masks
   debug_img = detector.visualize_mask(frame)
   cv2.imshow("Debug", debug_img)
   cv2.waitKey(0)
   ```

### Frame Synchronization Issues

**Symptom**: High `dropped_left` or `dropped_right` in sync stats

**Causes & Solutions:**

1. **Timing Jitter Too Large**
   ```yaml
   sync:
     tolerance_ms: 8.0  # Increase tolerance (was 5.0)
   ```

2. **Cameras at Different Actual FPS**
   - Check if one camera is slower (diagnose each separately)
   - May need to use same physical camera model for both eyes

3. **USB Bandwidth Contention**
   - Connect cameras to different USB controllers
   - Reduce frame rate or resolution

4. **Processing Too Slow**
   - Monitor sync stats: if `queue_left` or `queue_right` growing, processing can't keep up
   - Reduce FPS target or optimize processing (see performance.md)

### High CPU Usage

**Symptom**: CPU at 100%, frame drops

**Solutions:**

1. **Reduce FPS**
   ```yaml
   cameras:
     fps: 100  # Down from 120
   ```

2. **Disable Display**
   ```yaml
   ui:
     enable_display: false
   ```

3. **Simplify Processing**
   ```yaml
   processing:
     lash_kernel_length: 11      # Smaller (was 15)
     morph_open_size: 2          # Smaller (was 3)
   ```

4. **Close Background Applications**
   - Check Task Manager for other CPU-intensive processes
   - Disable antivirus real-time scanning temporarily (for testing)

### Video Recording Fails

**Error**: `Failed to open video writers`

**Solutions:**

1. **Install FFV1 Codec**
   - FFV1 may not be available in all OpenCV builds
   - Try MJPG instead:
   ```python
   video_writer = DualVideoWriter(..., codec="MJPG")
   ```

2. **Disk Space**
   - Ensure sufficient disk space (lossless video is large)
   - 120 fps × 320×240 grayscale ≈ 9 MB/s per camera

3. **File Permissions**
   - Check output directory is writable
   - Try different output path

4. **Use AVI Container**
   - Ensure output files have `.avi` extension
   - Some codecs don't work with other containers

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'dual_eye_tracker'`

**Solutions:**

1. **Install Package**
   ```bash
   pip install -e .
   ```

2. **Check Virtual Environment**
   ```bash
   # Ensure venv is activated
   venv\Scripts\activate  # Windows

   # Verify installation
   pip list | findstr dual
   ```

3. **Python Path Issues**
   ```bash
   # Temporary workaround
   set PYTHONPATH=%CD%
   python -m dual_eye_tracker.main
   ```

### Test Failures

**Error**: `pytest` tests fail

**Solutions:**

1. **Install Dev Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

2. **NumPy/OpenCV Compatibility**
   - Ensure compatible versions:
   ```bash
   pip install opencv-python>=4.8.0 numpy>=1.24.0
   ```

3. **Skip Camera Tests**
   - Hardware tests are marked with `skipif`
   - Run without hardware:
   ```bash
   pytest -v -k "not camera"
   ```

## Diagnostic Commands

### Full System Check

```bash
# Check camera capabilities
python scripts/diagnose_caps.py --camera 0 --backend dshow
python scripts/diagnose_caps.py --camera 1 --backend dshow

# Run benchmark
python scripts/bench_fps.py --config configs/preset_120fps.yaml --duration 5

# Test detection on single camera
dual-eye-tracker --config configs/default.yaml
```

### Verbose Logging

Add debug logging to troubleshoot:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Was INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### Check Package Integrity

```bash
# List installed files
pip show -f dual-eye-tracker

# Reinstall if needed
pip uninstall dual-eye-tracker
pip install -e .
```

## Getting Help

If issues persist:

1. **Gather Information:**
   - Run diagnostic commands above
   - Note error messages and tracebacks
   - System specs (OS version, Python version, camera model)
   - Output of `pip list`

2. **Check Existing Issues:**
   - Search [GitHub Issues](https://github.com/yourusername/dual-eye-tracker/issues)
   - May already have solution or workaround

3. **Open New Issue:**
   - Provide all diagnostic information
   - Include config file if relevant
   - Minimal reproducible example if possible

4. **Community Forums:**
   - Consider posting to relevant forums (Python, OpenCV, computer vision)
   - Link to DualEyeTracker repo for context

## Known Limitations

- **No GPU Acceleration**: All processing is CPU-based (by design for portability)
- **Windows Only**: Tested on Windows 10/11; Linux/macOS support not guaranteed
- **UVC Cameras Only**: Requires UVC-compliant cameras; proprietary SDKs not supported
- **Python GIL**: Multi-threading limited by Python GIL for pure Python code
- **OpenCV Backend Limitations**: Some camera features may not be accessible via OpenCV

## Platform-Specific Issues

### Windows 11

- Some USB cameras have compatibility issues with Windows 11
- Try updating to latest Windows 11 build
- Check manufacturer for Windows 11-specific drivers

### Laptop Power Management

- Cameras may disconnect on battery power
- Disable USB selective suspend (see performance.md)
- Use "High Performance" power plan

### Antivirus Interference

- Some antivirus software blocks camera access
- Add Python executable to whitelist
- Temporarily disable for testing (re-enable after)
