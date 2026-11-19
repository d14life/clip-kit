"""Join a finished vertical body to a supplied SixStars outro with FFmpeg."""

import argparse
import json
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[2]
SAMPLES_PER_FRAME = 48000 // 30


def frame_count(path: Path) -> int:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    streams = json.loads(result.stdout)["streams"]
    video = next((stream for stream in streams if stream["codec_type"] == "video"), {})
    if (video.get("width"), video.get("height"), video.get("avg_frame_rate")) != (1080, 1920, "30/1"):
        raise ValueError(f"{path.name} must use 1080×1920 video at 30 fps.")
    if not any(stream["codec_type"] == "audio" for stream in streams):
        raise ValueError(f"{path.name} needs an audio track.")
    frames = video.get("nb_frames", "")
    if not frames.isdigit() or int(frames) < 1:
        raise ValueError(f"Export {path.name} as an MP4 with a visible video track.")
    return int(frames)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("body", type=Path)
    parser.add_argument("platform", choices=("youtube", "instagram", "tiktok"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--lufs", type=float, help="master the joined audio with a two-pass loudnorm (TP -1.5)")
    args = parser.parse_args()

    body = args.body.resolve()
    outro = ROOT / "videos" / "outro" / f"outro-{args.platform}.mp4"
    output = (args.output or body.with_name(f"{body.stem}-outro.mp4")).resolve()
    if output.suffix.lower() != ".mp4" or output.exists():
        parser.error("Choose a new .mp4 output path.")

    try:
        counts = [frame_count(body), frame_count(outro)]
        if counts[1] != 120:
            raise ValueError(f"{outro.name} must contain exactly 120 frames.")

        # Video and audio each occupy exactly the segment's picture duration.
        filters = []
        for i, frames in enumerate(counts):
            filters.append(f"[{i}:v]setsar=1,settb=1/30,setpts=N[v{i}]")
            filters.append(
                f"[{i}:a]aresample=48000:async=1:first_pts=0,"
                f"aformat=channel_layouts=stereo,apad,"
                f"atrim=end_sample={frames * SAMPLES_PER_FRAME},asetpts=N/SR/TB[a{i}]"
            )
        filters.append("[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]")

        output.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=output.parent) as folder:
            temporary = Path(folder) / "joined.mp4"
            subprocess.run(
                ["ffmpeg", "-v", "error", "-i", str(body), "-i", str(outro),
                 "-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[a]",
                 "-r", "30", "-c:v", "libx264", "-crf", "17", "-preset", "medium",
                 "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                 "-movflags", "+faststart", str(temporary)],
                check=True,
            )
            if frame_count(temporary) != sum(counts):
                raise ValueError("The joined video duration differs from the body plus 120 frames.")
            if args.lufs is not None:
                norm = f"loudnorm=I={args.lufs}:TP=-1.5:LRA=7"
                probe = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(temporary), "-vn", "-af",
                                        norm + ":print_format=json", "-f", "null", "-"],
                                       capture_output=True, text=True, check=True)
                m = json.loads(re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", probe.stderr, re.S)[-1])
                mastered = Path(folder) / "mastered.mp4"
                subprocess.run(
                    ["ffmpeg", "-v", "error", "-i", str(temporary), "-map", "0:v", "-map", "0:a", "-c:v", "copy",
                     "-af", f"{norm}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
                            f"offset={m['target_offset']}:linear=true,aresample=48000",
                     "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(mastered)],
                    check=True)
                temporary = mastered
            temporary.rename(output)
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        parser.exit(1, f"Outro export failed. {exc}\n")
    print(f"{output}\n{sum(counts)} frames at 30 fps ({sum(counts) / 30:.2f} seconds)")


if __name__ == "__main__":
    main()
