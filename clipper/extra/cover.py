"""python cover.py <final_vertical.mp4> <source_clip.mp4> <face_t> <bg_t> <crop_x> <NAME> <line1> <line2> <out.jpg>
bg = 9:16 slice of the ORIGINAL clip at bg_t (clean), face = rembg cutout of the streamer's cam panel at face_t."""
import sys, io, html, subprocess, json, re
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np
V, S, ft, bt, cx, name, l1, l2, out = sys.argv[1:10]
ft, bt, cx = float(ft), float(bt), int(cx)
H = Path(__import__("os").environ.get("CLIP_FRESH_DIR", "fresh")); T = Path(__import__("os").environ.get("CLIP_THUMBS_DIR", "thumbs"))
F = "ffmpeg"
def frame(p, t): return Image.open(io.BytesIO(subprocess.run([F,"-v","error","-ss",str(t),"-i",p,"-frames:v","1","-f","image2pipe","-vcodec","png","-"],capture_output=True,check=True).stdout)).convert("RGB")
slug = re.sub(r"\W+", "_", Path(out).stem)[:30]
src = frame(S, bt); w, h = src.size; cw = round(h * 9 / 16); cx = min(cx, w - cw)
src.crop((cx, 0, cx + cw, h)).resize((1080, 1920), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2)).save(H / f"bg_{slug}.png")
cam = frame(V, ft).crop((0, 230, 1080, 838))
from rembg import remove, new_session
cut = remove(cam, session=new_session("u2net_human_seg")).convert("RGBA")
a = np.array(cut)[:, :, 3]; ys, xs = np.where(a > 128)
cut = cut.crop((max(0, xs.min()-10), max(0, ys.min()-10), xs.max()+10, ys.max()+10))
al = cut.split()[3]
pad = 22; big = Image.new("RGBA", (cut.width + 2*pad, cut.height + 2*pad), (0,0,0,0))
m = Image.new("L", big.size, 0); m.paste(al, (pad, pad)); m = m.filter(ImageFilter.MaxFilter(2*14+1)).filter(ImageFilter.GaussianBlur(1.5))
big.paste((255,255,255,255), (0,0), m); big.alpha_composite(cut, (pad, pad)); big.save(H / f"st_{slug}.png")
sz = big.size; sh = 760; sw = round(sz[0] * sh / sz[1])
if sw > 1000: sw = 1000; sh = round(sz[1] * sw / sz[0])
e = html.escape
tl = "".join(f'<div class="ln t"><span class="h back" style="font-size:118px">{e(l)}</span><span class="h tf" style="font-size:118px">{e(l)}</span></div>' for l in (l1, l2) if l)
page = f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:PD;src:url("file:///{(T/'font'/'pricedown.otf').as_posix()}")}}
html,body{{margin:0;width:1080px;height:1920px;overflow:hidden;background:#12051f}}
.bg{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:saturate(1.2) contrast(1.06)}}
.tint{{position:absolute;inset:0;background:linear-gradient(180deg,#2a0b4d 0%,#ff2d8a 45%,#ff8a3d 70%,#3a0d5c 100%);mix-blend-mode:soft-light;opacity:.6}}
.ov{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(25,8,50,.55) 0%,rgba(25,8,50,0) 18%,rgba(25,8,50,0) 42%,rgba(30,6,48,.66) 56%,rgba(26,6,44,.62) 76%,rgba(20,4,36,.35) 92%,rgba(20,4,36,.5) 100%)}}
.st{{position:absolute;left:50%;top:150px;height:{sh}px;transform:translateX(-50%) rotate(-2.5deg);filter:drop-shadow(0 18px 28px rgba(20,0,40,.7))}}
.blk{{position:absolute;left:60px;right:60px;top:{150+sh+30}px;text-align:center;transform:rotate(-2.5deg);transform-origin:50% 0}}
.ln{{position:relative;line-height:1;white-space:nowrap}}
.h{{font-family:PD;display:inline-block;white-space:nowrap;letter-spacing:.01em}}
.ln .tf,.ln .nf{{position:absolute;left:50%;top:0;transform:translateX(-50%)}}
.name .back{{font-size:260px;color:#1a0630;-webkit-text-stroke:30px #1a0630;text-shadow:0 14px 0 #1a0630,0 26px 40px rgba(0,0,0,.6)}}
.name .nf{{font-size:260px;background:linear-gradient(180deg,#ff3fa4 8%,#ff5f7a 45%,#ff9a3c 80%,#ffc25a 100%);-webkit-background-clip:text;background-clip:text;color:transparent}}
.t{{margin-top:6px}}
.t .back{{color:#1a0630;-webkit-text-stroke:20px #1a0630;text-shadow:0 8px 0 #1a0630,0 14px 26px rgba(0,0,0,.55)}}
.t .tf{{background:linear-gradient(180deg,#ffffff 0%,#ffffff 55%,#ffe3f1 75%,#9ff3ea 100%);-webkit-background-clip:text;background-clip:text;color:transparent}}
.badge{{position:absolute;left:80px;top:58px;transform:rotate(-6deg);font-family:PD;font-size:84px;line-height:1}}
.badge .b1{{color:#1a0630;-webkit-text-stroke:14px #1a0630}}
.badge .b2{{position:absolute;left:0;top:0;background:linear-gradient(90deg,#ff3fa4,#ff8a3d 55%,#ffc25a);-webkit-background-clip:text;background-clip:text;color:transparent}}
.bar{{position:absolute;left:0;right:0;bottom:0;height:16px;background:linear-gradient(90deg,#19d3c5,#7b2cbf 35%,#ff2d8a 65%,#ff8a3d)}}
</style></head><body>
<img class="bg" src="bg_{slug}.png"><div class="tint"></div><div class="ov"></div>
<img class="st" src="st_{slug}.png" style="width:{sw}px">
<div class="badge"><span class="b1">GTA VI</span><span class="b2">GTA VI</span></div>
<div class="blk"><div class="ln name"><span class="h back">{e(name)}</span><span class="h nf">{e(name)}</span></div>{tl}</div><div class="bar"></div>
<script>document.fonts.ready.then(()=>{{for(const l of document.querySelectorAll('.ln')){{const w=l.firstElementChild.getBoundingClientRect().width;const max=l.classList.contains('name')?920:890;if(w>max)l.style.zoom=max/w}}}});</script></body></html>'''
pg = H / f"page_{slug}.html"; pg.write_text(page, encoding="utf-8")
shot = H / f"shot_{slug}.png"
subprocess.run([r"C:\Program Files\Google\Chrome\Application\chrome.exe","--headless=new","--disable-gpu","--hide-scrollbars","--allow-file-access-from-files","--force-device-scale-factor=1","--window-size=1080,1920","--virtual-time-budget=5000",f"--screenshot={shot}",pg.as_uri()],check=True,capture_output=True,timeout=90)
Image.open(shot).convert("RGB").save(out, quality=93); print("cover", out)
