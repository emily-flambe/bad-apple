"""Re-render sample.mp4 with block averaging and audio preservation."""

import cv2
import numpy as np
import subprocess
import shutil
from pathlib import Path

INPUT = "media/source/sample.mp4"
OUTPUT = "media/output/sample_pixelated.mp4"
BLOCK = 32
FRAMES_DIR = Path("_pixelate_frames_tmp")

cap = cv2.VideoCapture(INPUT)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

w_trim = (w // BLOCK) * BLOCK
h_trim = (h // BLOCK) * BLOCK

FRAMES_DIR.mkdir(exist_ok=True)

frame_num = 0
while True:
    ok, frame = cap.read()
    if not ok:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)[:h_trim, :w_trim]

    blocks = gray.reshape(h_trim // BLOCK, BLOCK, w_trim // BLOCK, BLOCK)
    averaged = blocks.mean(axis=(1, 3)).astype(np.uint8)

    result = np.repeat(np.repeat(averaged, BLOCK, axis=0), BLOCK, axis=1)

    cv2.imwrite(str(FRAMES_DIR / f"frame_{frame_num:05d}.png"), result)
    frame_num += 1

cap.release()
print(f"Wrote {frame_num} frames as PNGs")

print("Assembling video with ffmpeg...")
subprocess.run([
    "ffmpeg", "-y",
    "-framerate", str(fps),
    "-i", str(FRAMES_DIR / "frame_%05d.png"),
    "-i", INPUT,
    "-map", "0:v",
    "-map", "1:a",
    "-c:v", "libx264",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "copy",
    "-shortest",
    OUTPUT,
], check=True)

print("Cleaning up temp frames...")
shutil.rmtree(FRAMES_DIR)

print(f"Done — {frame_num} frames → {OUTPUT}")
