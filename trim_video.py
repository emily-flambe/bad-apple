import subprocess

subprocess.run([
    "ffmpeg", "-i", "full_video.mp4",
    "-t", "5",         # duration in seconds
    "-c", "copy",      # copy streams directly, no re-encode
    "bad_apple_5s.mp4"
], check=True)
