"""Burn the hook title onto an already-finished 9:16 clip (same PNG, position and timing as autoclip.py).
   python -P burn_hook.py <in.mp4> <hook.txt> <clip.json> <out.mp4>"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
import autoclip as a  # noqa: E402

src, hook, meta, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
assert not out.exists(), f"refusing to overwrite {out}"
d = json.loads(meta.read_text("utf-8"))
png = Path(__import__("os").environ.get("CLIP_WORK", "work")) / (out.stem + "_title.png")
y = a.hook_png(hook.read_text("utf-8").strip(), png, a.hook_bottom(d["vertical_layout"], d["facecam"], d["framing"]))
vf = (f"[1:v]format=rgba,fade=t=in:st=0:d=0.15:alpha=1,fade=t=out:st=3.0:d=0.3:alpha=1[hk];"
      f"[0:v][hk]overlay=x={a.HOOK_SIDE}:y='{y}-24*exp(-t*20)':eof_action=pass:enable='lte(t,{a.HOOK_END})'[v]")
subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-loop", "1", "-framerate", "60", "-t", f"{a.HOOK_END}", "-i", str(png),
                "-filter_complex", vf, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                "-pix_fmt", "yuv420p", "-r", "60", "-c:a", "copy", "-movflags", "+faststart", str(out)], check=True)
print("wrote", out, "title y", y)
