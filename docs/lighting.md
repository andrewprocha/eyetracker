# Lighting Guide for DualEyeTracker

## IR Illumination Recommendations

### Safety First

**IMPORTANT**: Ensure your IR illumination complies with eye safety standards (IEC 62471).

- Use IR LEDs in the 850-940nm wavelength range
- Limit power to eye-safe levels (typically <10 mW/cm² for continuous exposure)
- Consider using diffused illumination to avoid hotspots
- Never look directly at IR sources, even if invisible to the naked eye

### Optimal Setup

**Recommended Configuration:**
- 2-4 IR LEDs per eye
- 850nm or 940nm wavelength
- Diffused or wide-angle optics
- Position at 30-45° angle from camera axis

**Why IR?**
- Pupil appears very dark in IR
- Iris provides high contrast
- Less affected by ambient lighting
- Eyelashes are less prominent
- No visible distraction to subject

### Exposure Settings

**120 FPS Target:**
- Exposure time: 4-5ms (4000-5000 µs)
- Adjust IR LED brightness to achieve good dynamic range
- Target histogram: Pupil in 40-80 range, iris in 150-200 range

**100 FPS Target:**
- Exposure time: 5-8ms (5000-8000 µs)
- Allows more light collection
- Better for lower-power IR sources

### Avoiding Glints

Glints (corneal reflections) can interfere with pupil detection:

1. **Position LEDs**: Place IR sources to reflect outside the pupil area
2. **Use Diffused Illumination**: Reduces sharp reflections
3. **Multiple Sources**: Spread light from several angles
4. **Detection Robustness**: DualEyeTracker's ring-contrast check helps reject glints

### Testing Your Setup

**Use the Diagnostic Tool:**

```bash
# Capture a test frame and check histogram
python scripts/diagnose_caps.py --camera 0
```

**Good Indicators:**
- Pupil pixels: 40-80 intensity
- Iris pixels: 150-200 intensity
- Clear boundary between pupil and iris
- Minimal noise in uniform regions

**Poor Indicators:**
- Overexposed (>240): Reduce IR brightness or exposure
- Underexposed (<100 iris): Increase IR brightness or exposure
- Large glints covering pupil: Reposition IR sources
- High noise: May need longer exposure or more light

## Visible Light Considerations

While IR is recommended, DualEyeTracker can work with visible light:

### Visible Light Setup

- Use diffuse, uniform illumination
- Avoid direct overhead lighting (casts eyelid shadows)
- Prefer neutral temperature (4000-5000K)
- Maintain consistent ambient conditions

### Limitations

- Eyelashes more prominent in visible light
- Iris color affects contrast (light irises reduce contrast)
- Ambient light changes affect consistency
- Subject may find visible cameras more distracting

## Troubleshooting

### Pupil Too Dim
- **Cause**: Overexposure, washing out pupil
- **Fix**: Reduce IR brightness or decrease exposure time

### Pupil Not Detected
- **Cause**: Insufficient contrast or underexposure
- **Fix**: Increase IR brightness, increase exposure time, or adjust `min_ring_contrast` in config

### Inconsistent Detection
- **Cause**: Ambient light changes or glints
- **Fix**: Shield from ambient light, reposition IR sources, ensure stable IR power

### High Frame Drop Rate
- **Cause**: Exposure time too long for target FPS
- **Fix**: Reduce exposure time, ensure IR brightness compensates, or lower target FPS

## Example Configurations

### High-Speed (120 FPS)

```yaml
cameras:
  fps: 120
  exposure_us: 4000  # 4ms
```

Requires: Bright IR illumination, fast cameras

### Balanced (100 FPS)

```yaml
cameras:
  fps: 100
  exposure_us: 6000  # 6ms
```

Better for: Moderate IR brightness, typical UVC cameras

### Lower Speed (60 FPS)

```yaml
cameras:
  fps: 60
  exposure_us: 10000  # 10ms
```

Good for: Low IR power, initial testing, visible light

## Resources

- [IEC 62471 Photobiological Safety](https://www.iec.ch/)
- [SR Research Eye Tracking Best Practices](https://www.sr-research.com/)
- [Pupil Labs IR Safety Guidelines](https://docs.pupil-labs.com/)
