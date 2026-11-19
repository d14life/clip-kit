"""python render1.py <mp4> <channel> <base> <hook title> <t0> <t1> -> autoclipper/clips_fresh_en/<base>_vertical.mp4"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
import autoclip as a
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
mp4, ch, base, hook, t0, t1 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]), float(sys.argv[6])
cfg, _ = a.parse_args(["x"])
cfg.captions = True; cfg.fx = False; cfg.teaser = False; cfg.formats = ["vertical"]; cfg.hook = True
out = Path(str(Path(str(__import__("pathlib").Path(__file__).resolve().parents[1]))/"clips_fresh_en")); out.mkdir(exist_ok=True)
(out / f"{base}.hook.txt").write_text(hook, "utf-8")
import subprocess
dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",mp4]).decode())
t1 = min(t1, dur)
sess = a.HERE / "work" / ch / "fresh"; sess.mkdir(parents=True, exist_ok=True)
seg = a.Segment(Path(mp4).resolve(), 0.0, dur, dur)
sp = a.Spike(onset=t0+1, bucket_start=t0, score=0, baseline=1, threshold=1, ratio=0, sample=[])
job = a.ClipJob(channel=ch, spike=sp, start=t0, end=t1, stream={}, session_dir=sess, segments=[seg],
                extra={"fixed": True, "file_base": base, "out_dir": str(out)})
f = a.ClipFactory(cfg); f.preload(); f.make(job)
print("done", out / f"{base}_vertical.mp4")
