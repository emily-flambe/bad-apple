"""
Bad Apple!! Pitch + Spatial Color Renderer
==========================================
Renders Bad Apple (or any high-contrast B&W video) with colored pixels where:
  - Base hue comes from the dominant pitch of the music at that moment
  - Spatial offset comes from each pixel's angle around the screen center

Low notes → warm reds/oranges. High notes → cool blues/violets.
The angle-based spatial spread creates a pinwheel gradient across white areas.

Requirements:
    pip install opencv-python librosa numpy

Also needs ffmpeg on your PATH:
    brew install ffmpeg   (macOS)
    sudo apt install ffmpeg  (Linux)

Usage:
    python bad_apple_renderer.py
    (edit the CONFIG section below first)
"""

import numpy as np
import cv2
import librosa
import subprocess
import os
from pathlib import Path


# ─── CONFIG ───────────────────────────────────────────────────────────────────

VIDEO_PATH    = "bad_apple.mp4"   # path to your source video
OUTPUT_VIDEO  = "bad_apple_colored.mp4"
FRAMES_DIR    = Path("_frames_tmp")  # temp folder, deleted when done

THRESHOLD     = 128    # grayscale cutoff: above = white, below = black
SATURATION    = 0.95   # color saturation for white pixels (0–1)
BRIGHTNESS    = 1.0    # brightness for white pixels (0–1)

# How much the spatial (angle) component shifts the hue.
# 0.0 = pure pitch, no spatial. 1.0 = full 360° color wheel spread per frame.
SPATIAL_WEIGHT = 0.35

# Pitch frequency range to map across hues.
# Anything outside this range gets clamped. Adjust for your audio.
PITCH_HZ_MIN = 100.0   # maps to hue 0.0 (red)
PITCH_HZ_MAX = 1200.0  # maps to hue 0.75 (violet)

# Hue range to use (0–1 covers full wheel; 0–0.75 avoids red looping back)
HUE_RANGE_MIN = 0.0
HUE_RANGE_MAX = 0.75

# ──────────────────────────────────────────────────────────────────────────────


def extract_audio(video_path: str, audio_path: str = "_audio_tmp.wav") -> str:
    """Pull audio track from video into a WAV file."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-ac", "1", audio_path],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return audio_path


def get_pitch_per_frame(audio_path: str, fps: float, total_frames: int) -> np.ndarray:
    """
    Analyze audio and return one pitch value (Hz) per video frame.
    Uses librosa's pyin algorithm — probabilistic YIN, works well on melody.
    Falls back to a neutral mid-range pitch for unvoiced/silent frames.
    """
    print("  Loading audio...")
    y, sr = librosa.load(audio_path, sr=None)

    print("  Running pitch detection (this takes ~10–30 seconds)...")
    f0, voiced_flag, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),  # ~65 Hz
        fmax=librosa.note_to_hz("C7"),  # ~2093 Hz
        sr=sr,
    )

    # Replace NaN (unvoiced frames) with a fallback pitch
    fallback_hz = (PITCH_HZ_MIN + PITCH_HZ_MAX) / 2
    f0_clean = np.where(np.isnan(f0), fallback_hz, f0)

    # f0 is sampled at librosa's hop rate; resample to video frame rate
    audio_times = librosa.times_like(f0, sr=sr)
    frame_times = np.arange(total_frames) / fps
    pitch_per_frame = np.interp(frame_times, audio_times, f0_clean)

    return pitch_per_frame


def pitch_to_hue(hz: float) -> float:
    """
    Map a pitch in Hz to a hue value [HUE_RANGE_MIN, HUE_RANGE_MAX].
    Uses a log scale because pitch perception (octaves) is logarithmic.
    """
    hz = np.clip(hz, PITCH_HZ_MIN, PITCH_HZ_MAX)
    log_min = np.log(PITCH_HZ_MIN)
    log_max = np.log(PITCH_HZ_MAX)
    t = (np.log(hz) - log_min) / (log_max - log_min)  # 0–1 linear in log space
    return HUE_RANGE_MIN + t * (HUE_RANGE_MAX - HUE_RANGE_MIN)


def build_spatial_offset_map(h: int, w: int) -> np.ndarray:
    """
    Precompute a (h, w) array of spatial hue offsets based on each pixel's
    angle around the screen center. Values are in [0, 1], where 1 = full
    color wheel rotation. Multiplied by SPATIAL_WEIGHT at render time.

    The result is a pinwheel gradient: pixels at the same angle from center
    share the same spatial offset, regardless of distance.
    """
    cx, cy = w / 2.0, h / 2.0
    x = np.arange(w) - cx
    y = np.arange(h) - cy
    xx, yy = np.meshgrid(x, y)

    # arctan2 returns [-π, π]; shift to [0, 1]
    angle_norm = (np.arctan2(yy, xx) / (2 * np.pi)) + 0.5
    return angle_norm.astype(np.float32)


def color_frame(gray: np.ndarray, pitch_hue: float, spatial_map: np.ndarray) -> np.ndarray:
    """
    Convert a grayscale frame to a colored frame.
    - Black pixels → stay black (0, 0, 0)
    - White pixels → HSV color with hue = pitch_hue + spatial_offset
    """
    h, w = gray.shape
    white_mask = gray > THRESHOLD

    # Hue: combine pitch (global) + spatial angle (per-pixel), wrap at 1.0
    hue = (pitch_hue + spatial_map * SPATIAL_WEIGHT) % 1.0

    # Build HSV image (float32, H in [0,1], S/V in [0,1])
    sat = np.full((h, w), SATURATION, dtype=np.float32)
    val = np.full((h, w), BRIGHTNESS, dtype=np.float32)
    hsv_float = np.stack([hue, sat, val], axis=-1)

    # OpenCV expects H in [0,180], S/V in [0,255] for uint8
    hsv_u8 = (hsv_float * np.array([180, 255, 255])).astype(np.uint8)
    bgr = cv2.cvtColor(hsv_u8, cv2.COLOR_HSV2BGR)

    # Zero out black pixels
    result = np.zeros((h, w, 3), dtype=np.uint8)
    result[white_mask] = bgr[white_mask]
    return result


def main():
    FRAMES_DIR.mkdir(exist_ok=True)

    # ── Open video ────────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video: {VIDEO_PATH}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps          = cap.get(cv2.CAP_PROP_FPS)
    width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"Video: {total_frames} frames @ {fps:.2f} fps — {width}×{height}")

    # ── Audio & pitch ─────────────────────────────────────────────────────────
    print("Extracting audio...")
    audio_path = extract_audio(VIDEO_PATH)

    print("Analyzing pitch...")
    pitches = get_pitch_per_frame(audio_path, fps, total_frames)

    # ── Precompute spatial map (same for every frame) ─────────────────────────
    spatial_map = build_spatial_offset_map(height, width)

    # ── Process frames ────────────────────────────────────────────────────────
    print("Coloring frames...")
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hue  = pitch_to_hue(pitches[frame_idx])
        colored = color_frame(gray, hue, spatial_map)

        out_path = FRAMES_DIR / f"frame_{frame_idx:05d}.png"
        cv2.imwrite(str(out_path), colored)

        if frame_idx % 150 == 0:
            pct = 100 * frame_idx / total_frames
            print(f"  [{pct:5.1f}%] frame {frame_idx:5d} — "
                  f"{pitches[frame_idx]:6.1f} Hz → hue {hue:.3f}")

        frame_idx += 1

    cap.release()
    print(f"Processed {frame_idx} frames.")

    # ── Reassemble video with original audio ──────────────────────────────────
    print("Assembling final video...")
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(FRAMES_DIR / "frame_%05d.png"),
        "-i", audio_path,
        "-c:v", "libx264",
        "-crf", "18",           # quality: lower = better, 18 is near-lossless
        "-pix_fmt", "yuv420p",  # required for broad compatibility
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        OUTPUT_VIDEO,
    ], check=True)

    # ── Cleanup temp files ────────────────────────────────────────────────────
    print("Cleaning up temp files...")
    for f in FRAMES_DIR.iterdir():
        f.unlink()
    FRAMES_DIR.rmdir()
    os.remove(audio_path)

    print(f"\nDone! Output: {OUTPUT_VIDEO}")
    print("Tweak SPATIAL_WEIGHT and PITCH_HZ_MIN/MAX in CONFIG to adjust the look.")


if __name__ == "__main__":
    main()
