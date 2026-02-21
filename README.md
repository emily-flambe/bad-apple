# Bad Apple Renderer

Renders Bad Apple!! (or any high-contrast black-and-white video) with color, where the hue of each white pixel is driven by two things at once:

- **Pitch** — the dominant musical frequency at that moment shifts the base hue across the whole frame (low notes → warm reds/oranges, high notes → cool blues/violets)
- **Spatial position** — each pixel's angle around the screen center adds a hue offset, creating a pinwheel gradient across the white silhouette areas

The result is a colored video where the palette pulses with the melody and the shapes have internal color structure.

## Requirements

```
pip install opencv-python librosa numpy
```

ffmpeg must also be on your PATH:
```
brew install ffmpeg       # macOS
sudo apt install ffmpeg   # Linux
```

## Files

| File | Purpose |
|------|---------|
| `bad_apple_renderer.py` | Main renderer — processes all frames and outputs a colored video |
| `trim_video.py` | Utility — extracts the first 10 seconds of the source video for testing |

## Usage

**1. (Optional) Trim a test clip first**

Edit `trim_video.py` if needed, then:
```
python trim_video.py
```
Produces `bad_apple_10s.mp4`.

**2. Run the renderer**

Point `VIDEO_PATH` in the CONFIG section of `bad_apple_renderer.py` at your source file, then:
```
python bad_apple_renderer.py
```
Produces `bad_apple_colored.mp4`.

## Tuning

All parameters are in the `CONFIG` block at the top of `bad_apple_renderer.py`:

| Parameter | Default | Effect |
|-----------|---------|--------|
| `SPATIAL_WEIGHT` | `0.35` | How wide the per-frame color spread is. `0` = flat color per frame, `1` = full rainbow pinwheel |
| `PITCH_HZ_MIN/MAX` | `100–1200` | Frequency range that maps across the full hue span |
| `HUE_RANGE_MIN/MAX` | `0.0–0.75` | Portion of the color wheel used (avoids red looping back to red) |
| `THRESHOLD` | `128` | Grayscale cutoff between black and white pixels |
| `SATURATION` | `0.95` | Color saturation of white pixels |

## How It Works

1. Audio is extracted from the video with ffmpeg
2. Pitch is detected per-frame using [librosa's pyin algorithm](https://librosa.org/doc/latest/generated/librosa.pyin.html) (probabilistic YIN)
3. Each frame is thresholded to binary (black/white)
4. White pixels are colored using HSV, where `hue = pitch_hue + angle_from_center × SPATIAL_WEIGHT`
5. Colored frames are reassembled into a video with the original audio via ffmpeg
