"""python pack.py <final.mp4> <cover.jpg> <fileName> <title> <caption> <streamertag> <score> <created_at> [RU]"""
import sys, shutil, subprocess
from pathlib import Path
v, jpg, name, title, cap, tag, score, created = sys.argv[1:9]
ru = len(sys.argv) > 9
D = Path(__import__("os").environ.get("CLIP_READY_RU", "ready_ru") if ru else __import__("os").environ.get("CLIP_READY_EN", "ready_en"))
D.mkdir(exist_ok=True)
shutil.copy(v, D / f"{name}.mp4"); shutil.copy(jpg, D / f"{name}.jpg")
tags = "#GTA6 #GTAVI #" + tag + " #fyp"
(D / f"{name} - TITLE.txt").write_text(f"{title}\n\n{cap} {tags}\n", encoding="utf-8")
if True:
    o = Path(__import__("os").environ.get("CLIP_UPLOAD_DIR", "upload_ready/tt")); o.mkdir(exist_ok=True)
    f = D / f"{name}.mp4"; out = o / f"{name}.mp4"
    dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)]).decode())
    for k in (1.0, 0.9, 0.8):
        vb = int((9.4*8*1024/dur - 128)*k)
        a = ["ffmpeg","-loglevel","error","-y","-i",str(f),"-c:v","libx264","-b:v",f"{vb}k","-maxrate",f"{vb*3//2}k","-bufsize",f"{vb*2}k","-passlogfile",str(o)+"\p_x"]
        subprocess.run(a+["-pass","1","-an","-f","null","NUL"],check=True)
        subprocess.run(a+["-pass","2","-c:a","aac","-b:a","128k","-movflags","+faststart",str(out)],check=True)
        if out.stat().st_size < 10_000_000: break
    shutil.copy(jpg, o / f"{name}.jpg")
    print(f"tt copy {out.stat().st_size/1e6:.2f} MB")
open(__import__("os").environ.get("CLIP_READY_LOG", "fresh_ready.txt"),"a",encoding="utf-8").write(f"{name} | {created} | {score} | {D/(name+'.mp4')}\n")
print("packed", name)
