import argparse
import subprocess


def trim(input_file, output_file, start=None, end=None, duration=None):
    cmd = ["ffmpeg", "-y"]
    if start is not None:
        cmd += ["-ss", str(start)]
    cmd += ["-i", input_file]
    if duration is not None:
        cmd += ["-t", str(duration)]
    elif end is not None:
        cmd += ["-to", str(end)]
    cmd += ["-c", "copy", output_file]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trim a video clip")
    parser.add_argument("input", help="Input video file")
    parser.add_argument("output", help="Output video file")
    parser.add_argument("-ss", "--start", type=float, default=None, help="Start time in seconds")
    parser.add_argument("-to", "--end", type=float, default=None, help="End time in seconds")
    parser.add_argument("-t", "--duration", type=float, default=None, help="Duration in seconds")
    args = parser.parse_args()

    trim(args.input, args.output, start=args.start, end=args.end, duration=args.duration)
