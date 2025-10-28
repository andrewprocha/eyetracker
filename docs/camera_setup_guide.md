# Camera Setup Guide

## Camera Types and Configuration

DualEyeTracker works with two different camera setups. **It's critical to use the correct config preset for your camera type.**

### 🎯 Close-Up Eye Cameras (Most Common)

**Description:**
- Camera mounted 10-20cm from the eye
- Captures ONLY the eye (fills most of the frame)
- Typical in head-mounted rigs, chin rests, or desktop setups
- Pupil appears large (50-80 pixels diameter)

**Example frame:**
```
┌─────────────────────┐
│  ╱╱╱ eyelashes ╱╱╱  │
│                     │
│        ⚫           │  ← Pupil fills center
│      (pupil)        │
│                     │
│  ╱╱╱ eyelashes ╱╱╱  │
└─────────────────────┘
```

**Use this config:**
```bash
dual-eye-tracker --config configs/preset_closeup.yaml
```

**Key settings:**
- `eyelid_exclusion_pct: 0.0` - Eyelids don't cover much of frame
- `min_area: 300` - Pupils are large
- `min_ring_contrast: 10.0` - Lower threshold

---

### 👤 Distant Face Cameras (Less Common)

**Description:**
- Camera captures entire face or large portion
- Used in some desktop setups or webcam-based systems
- Pupil appears small (10-30 pixels diameter)
- Eyelids cover significant portions top/bottom

**Example frame:**
```
┌─────────────────────┐
│▓▓▓▓▓ eyelid ▓▓▓▓▓▓▓ │
│                     │
│        •            │  ← Small pupil
│                     │
│▓▓▓▓▓ eyelid ▓▓▓▓▓▓▓ │
└─────────────────────┘
```

**Use this config:**
```bash
dual-eye-tracker --config configs/default.yaml
# OR
dual-eye-tracker --config configs/preset_120fps.yaml
```

**Key settings:**
- `eyelid_exclusion_pct: 20.0` - Mask eyelid bands
- `min_area: 50` - Small pupils
- `min_ring_contrast: 15.0` - Higher quality requirement

---

## How to Know Which Type You Have

### Quick Test

Run the diagnostic tool:
```bash
python scripts/diagnose_caps.py --camera 0
```

Look at the captured frame:
- **If you see mostly iris/pupil filling the frame** → Close-up camera
- **If you see eyelids, skin, and small pupil** → Distant camera

### Visual Comparison

| Close-Up Camera | Distant Camera |
|----------------|----------------|
| Pupil: 50-80px diameter | Pupil: 10-30px diameter |
| Iris fills 60-80% of frame | Eye is 30-50% of frame |
| Eyelids barely visible | Eyelids prominent |
| Eyelashes cross over iris | Eyelashes at edges |

---

## Tuning for Your Specific Camera

If neither preset works well:

### Step 1: Generate Test Images
```bash
python scripts/tune_for_your_camera.py
```

This creates:
- `output/tuning/input_eye_closeup.png` - Synthetic test image
- `output/tuning/pipeline_*.png` - Processing visualizations
- `output/tuning/recommended_config.txt` - Optimized parameters

### Step 2: Analyze Pipeline

Open `pipeline_optimized_closeup.png` and check each stage:

**Stage 1 (Original):** Does the pupil have good contrast with iris?
- If no: Increase IR lighting or exposure time
- Pupil should be clearly darker than surrounding iris

**Stage 2 (Eyelid exclusion):** Are the red boxes covering the pupil?
- If yes: Reduce `eyelid_exclusion_pct` (try 0.0 for close-up)
- Red boxes should only cover actual eyelid regions

**Stage 3 (Eyelash suppression):** Are eyelashes still visible?
- If yes: Increase `lash_kernel_length` (try 20-25)
- Eyelashes should be lightened/removed

**Stage 4 (Otsu threshold):** Is the pupil a clean white blob?
- If fragmented: Increase `lash_kernel_length`
- If missing: Check lighting/exposure
- If multiple blobs: Lighting may have glints

**Stage 5 (Morphology cleanup):** Is the blob circular and smooth?
- If not: Adjust `morph_open_size` and `morph_close_size`
- Should be a single smooth blob

**Stage 6 (Detection):** Green crosshair + yellow ellipse = success!
- If "NOT DETECTED": Previous stages had issues
- If detected but wrong position: Check area constraints

### Step 3: Apply Recommended Config

Copy the parameters from `output/tuning/recommended_config.txt` to your config file:

```yaml
# configs/my_custom_config.yaml
cameras:
  left_id: 0
  right_id: 1
  width: 320
  height: 240
  fps: 120
  # ... other camera settings

processing:
  # Paste recommended parameters here
  eyelid_exclusion_pct: 0.0
  min_area: 300
  # ... etc
```

Then run with your custom config:
```bash
dual-eye-tracker --config configs/my_custom_config.yaml
```

---

## Common Issues

### Issue: "Detection Failed" on Real Camera

**Causes:**
1. Wrong preset for your camera type
2. Insufficient IR lighting
3. Exposure time too short or too long
4. Camera out of focus

**Solutions:**
```bash
# 1. Try close-up preset
dual-eye-tracker --config configs/preset_closeup.yaml

# 2. Check camera output
python scripts/diagnose_caps.py --camera 0

# 3. Test with your actual camera
# Capture a frame and process with tuning tool
```

### Issue: Pupil Detected in Wrong Location

**Causes:**
- Glints (IR reflections) detected as pupil
- Eyelid exclusion masking real pupil
- Area constraints too loose

**Solutions:**
- Reposition IR LEDs to avoid glints
- Set `eyelid_exclusion_pct: 0.0` for close-up
- Adjust `min_area` and `max_area` based on actual pupil size

### Issue: Intermittent Detection (Works Sometimes)

**Causes:**
- Eyelashes occasionally occluding pupil
- Subject looking at extreme angles
- Ambient lighting variations

**Solutions:**
- Increase `lash_kernel_length` to 20-25
- Reduce `min_ring_contrast` to 8-10
- Ensure stable IR lighting (no sunlight interference)

---

## Validation Checklist

Before running long recordings, validate your setup:

- [ ] Run diagnostic: `python scripts/diagnose_caps.py --camera 0`
- [ ] Check pupil size in captured frame (should be clear and dark)
- [ ] Test detection: `python scripts/tune_for_your_camera.py`
- [ ] Verify 90%+ detection success in pipeline visualizations
- [ ] Run benchmark: `dual-eye-tracker --mode benchmark`
- [ ] Achieve target FPS (100-120 fps sustained)
- [ ] Test live viewer for 30 seconds with real subject
- [ ] Confirm crosshair tracks pupil accurately during movement

---

## Preset Comparison Table

| Setting | Close-Up | Default/120fps |
|---------|----------|----------------|
| eyelid_exclusion_pct | 0.0 | 20.0 |
| min_area | 300 | 50 |
| max_area | 8000 | 5000 |
| min_circularity | 0.2 | 0.3 |
| min_ring_contrast | 10.0 | 15.0 |

**Rule of thumb:** Start with close-up preset, then adjust if needed.
