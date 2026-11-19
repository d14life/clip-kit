"""One common white for every shot of the reel (Damir 2026-11-16: "all things the same gradient white", b07 overexposed).

public/final/<clip>.mp4 -> public/final/<clip>-g.mp4. Per frame:
  1. background estimate (neutral patches along the top and bottom rows, brightest half, temporally smoothed)
  2. per-channel gain so the top row lands on #F6F6F3 and the bottom row too (gain ramps top -> bottom),
     applied to neutral pixels only (weight falls to 0 by saturation 60, so the orange #FC6444 accent is untouched)
  3. neutral highlights above the background roll off softly (asymptote 252): nothing clips at 255
The soft darker edge comes from the edit's global vignette overlay, same for every shot.
Run: python3 scripts/grade_all.py [clip ...]   (prints before/after background samples)
"""
import subprocess, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1] / 'public/final'
W, H = 1080, 1920
TGT = np.array([246.0, 246.0, 243.0])
CLIPS = ['mx5-scene1v4', 'scene2', 'c4-s3-aimap', 'sd-ads-clean', 'c9-s4-flap', 'm4-b07', 'c11-grow', 'o8-wall', 'c5-b08-long-clean', 'o9-logo', 'o11-loop']
XS = [60, 300, 540, 780, 1020]
ROWS = {'top': 60, 'bot': 1860}
PTS = {'TL': (60, 60), 'TC': (540, 60), 'TR': (1020, 60), 'BL': (60, 1860), 'BC': (540, 1860), 'BR': (1020, 1860)}


def read(path):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(out, np.uint8).reshape(-1, H, W, 3)


def patch(a, x, y): return np.median(a[y - 20:y + 20, x - 20:x + 20].reshape(-1, 3), 0)


def row_bg(a, y):
    c = [p for p in (patch(a, x, y) for x in XS) if p.max() - p.min() < 14 and p.mean() <= 251]
    if not c: return None
    c.sort(key=lambda p: -p.mean())
    return np.mean(c[:max(1, (len(c) + 1) // 2)], 0)


def smooth(rows):
    ok = [i for i, r in enumerate(rows) if r is not None]
    if not ok: return np.tile(TGT, (len(rows), 1))
    a = np.array([rows[i] if rows[i] is not None else rows[min(ok, key=lambda j: abs(j - i))] for i in range(len(rows))])
    m = np.array([np.median(a[max(0, i - 7):i + 8], 0) for i in range(len(a))])
    return np.array([m[max(0, i - 2):i + 3].mean(0) for i in range(len(m))])


def samples(a): return ' '.join(f"{k}={'/'.join(str(int(round(v))) for v in patch(a, *xy))}" for k, xy in PTS.items())


ramp = np.clip((np.arange(H) - 700) / 1220, 0, 1); ramp = (ramp * ramp * (3 - 2 * ramp))[:, None, None]  # smoothstep, 0 above y 700
for name in sys.argv[1:] or CLIPS:
    F = read(ROOT / f'{name}.mp4')
    top, bot = smooth([row_bg(f, ROWS['top']) for f in F]), smooth([row_bg(f, ROWS['bot']) for f in F])
    gt, gb = np.clip(TGT / top, 0.9, 1.12), np.clip(TGT / np.maximum(bot, 1), 0.9, 1.12)
    gb = np.minimum(gb, gt * 1.06)  # bottom never lifted more than 6 % over the top
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                            '-c:v', 'libx264', '-crf', '14', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(ROOT / f'{name}-g.mp4')], stdin=subprocess.PIPE)
    mid = len(F) // 2
    for i, f in enumerate(F):
        a = f.astype(np.float32)
        sat = a.max(2, keepdims=True) - a.min(2, keepdims=True)
        w = np.clip((60 - sat) / 40, 0, 1)  # 1 = neutral, 0 = coloured (orange untouched)
        g = gt[i] + (gb[i] - gt[i]) * ramp
        b = a * (1 + (g - 1) * w)
        k = TGT.mean() + 6 * (1 - np.exp(-np.maximum(b - TGT.mean(), 0) / 6))  # soft roll-off above the background
        b = np.where((b > TGT.mean()) & (w > 0), b + (k - b) * w, b)
        o = np.clip(np.rint(b), 0, 255).astype(np.uint8)
        enc.stdin.write(o.tobytes())
        if i == mid:
            print(f'{name}:{i} before {samples(f)} max {f.max()} clip {100 * (f.min(2) >= 254).mean():.2f}%')
            print(f'{name}:{i} after  {samples(o)} max {o.max()} clip {100 * (o.min(2) >= 254).mean():.2f}%  gain top {np.round(gt[i], 3)} bot {np.round(gb[i], 3)}')
    enc.stdin.close(); enc.wait()
