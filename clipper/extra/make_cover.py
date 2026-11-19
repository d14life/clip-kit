"""Cover jpg: one frame of the finished 9:16 clip + the same hook title as in the video.
   python -P make_cover.py <clip.mp4> <seconds> <hook.txt> <clip.json> <out.jpg>"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
import autoclip as a  # noqa: E402
from PIL import Image  # noqa: E402

mp4, t, hook, meta, out = sys.argv[1], float(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5])
work = Path(__import__("os").environ.get("CLIP_WORK", "work"))
frame = work / (out.stem + "_frame.png")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", mp4, "-frames:v", "1", str(frame)], check=True)
d = json.loads(meta.read_text("utf-8"))
png = work / (out.stem + "_title.png")
y = a.hook_png(hook.read_text("utf-8").strip(), png, a.hook_bottom(d["vertical_layout"], d["facecam"], d["framing"]))
img = Image.open(frame).convert("RGBA")
assert img.size == (1080, 1920), img.size
img.alpha_composite(Image.open(png), (a.HOOK_SIDE, y))
img.convert("RGB").save(out, quality=92)
print("cover", out, "title y", y)
