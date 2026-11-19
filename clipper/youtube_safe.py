"""YouTube-safe copies: a pixel-mosaic box over exposed body parts ONLY (user: "just the part of the body"),
everything else stays sharp.
   python youtube_safe.py "Downloads/GTA 6/Lacy - shower scene.mp4" ...   (no args: every clip in Downloads/GTA 6)

Measured on these GTA clips: NudeNet on the whole 9:16 frame found nothing (bodies too small after its 320 px resize);
on 2x2 zoomed tiles of the gameplay panel it finds close-ups well but misses some steamy/distant frames. So boxes
are found ~10x a second, padded, and HELD for HOLD seconds after the last sighting so a missed frame does not
uncover anything. Check results by eye."""
import json
import subprocess
import sys
from pathlib import Path

import cv2
from nudenet import NudeDetector

DEST = Path.home() / "Downloads" / "GTA 6"
EXPOSED = {"BUTTOCKS_EXPOSED", "FEMALE_BREAST_EXPOSED", "FEMALE_GENITALIA_EXPOSED", "MALE_GENITALIA_EXPOSED", "ANUS_EXPOSED"}
GAME_Y0, GAME_Y1 = 838, 1446   # stack layout: the full game frame sits here in the 1080x1920 clip
CHECKS_PER_S = 10
MIN_SCORE = 0.3
PAD = 0.35                     # grow each box by this share on every side
HOLD = 1.0                     # keep a box this long after it was last seen
MOSAIC = 18                    # pixel block size of the censor


def find_boxes(det, game, tmp: Path) -> list:
    """Exposed-body boxes (x0, y0, x1, y1) in game-panel pixels, from 2x2 overlapping zoomed tiles."""
    H, W = game.shape[:2]
    boxes = []
    for ty in (0, H // 3):
        for tx in (0, W // 3):
            tile = cv2.resize(game[ty:ty + 2 * H // 3, tx:tx + 2 * W // 3], None, fx=1.5, fy=1.5)
            p = tmp / "tile.png"
            cv2.imwrite(str(p), tile)
            for h in det.detect(str(p)):
                if h["class"] in EXPOSED and h["score"] >= MIN_SCORE:
                    x, y, w, hh = (v / 1.5 for v in h["box"])
                    px, py = w * PAD, hh * PAD
                    boxes.append((int(tx + x - px), int(ty + y - py), int(tx + x + w + px), int(ty + y + hh + py)))
    return boxes


def censor(frame, box):
    x0, y0, x1, y1 = box
    x0, x1 = max(0, x0), min(frame.shape[1], x1)
    y0, y1 = max(0, y0), min(frame.shape[0], y1)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return
    roi = frame[y0:y1, x0:x1]
    small = cv2.resize(roi, (max(1, (x1 - x0) // MOSAIC), max(1, (y1 - y0) // MOSAIC)), interpolation=cv2.INTER_AREA)
    frame[y0:y1, x0:x1] = cv2.resize(small, (x1 - x0, y1 - y0), interpolation=cv2.INTER_NEAREST)


def make_copy(det, clip: Path, tmp: Path) -> dict:
    cap = cv2.VideoCapture(str(clip))
    fps = cap.get(cv2.CAP_PROP_FPS) or 60
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if (w, h) != (1080, 1920):
        cap.release()
        return {"skipped": "not a 9:16 clip"}
    step = max(1, int(round(fps / CHECKS_PER_S)))
    # pass 1: where are the boxes (so a clip with nothing in it gets no copy)
    found, i = [], 0
    while True:
        ok = cap.grab()
        if not ok:
            break
        if i % step == 0:
            ok, img = cap.retrieve()
            if ok:
                for b in find_boxes(det, img[GAME_Y0:GAME_Y1], tmp):
                    # never outside the game panel: a padded box near its top edge reached up onto Lacy's chin
                    # in the webcam panel above
                    y0, y1 = max(GAME_Y0, b[1] + GAME_Y0), min(GAME_Y1, b[3] + GAME_Y0)
                    if y1 - y0 > 8:
                        found.append((i / fps, (b[0], y0, b[2], y1)))
        i += 1
    cap.release()
    if not found:
        return {"boxes": 0}
    # pass 2: write the censored copy (frames piped to ffmpeg, original audio copied)
    out = clip.with_name(clip.stem + " (YouTube).mp4")
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
                           "-r", f"{fps:.3f}", "-i", "pipe:0", "-i", str(clip), "-map", "0:v", "-map", "1:a?",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-threads", "4", "-pix_fmt", "yuv420p",
                           "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    cap = cv2.VideoCapture(str(clip))
    i, k, covered = 0, 0, 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = i / fps
        active = [b for (ts, b) in found if ts - 0.15 <= t <= ts + HOLD]
        for b in active:
            censor(frame, b)
        covered += bool(active)
        ff.stdin.write(frame.tobytes())
        i += 1
    cap.release()
    ff.stdin.close()
    ff.wait()
    return {"boxes": len(found), "censored_s": round(covered / fps, 1), "file": out.name}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    clips = [Path(a) for a in sys.argv[1:]] or sorted(p for p in DEST.glob("*.mp4") if "(YouTube)" not in p.name)
    det = NudeDetector()
    tmp = Path(__file__).resolve().parent / "work" / "yt_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    report = {}
    for clip in clips:
        old = clip.with_name(clip.stem + " (YouTube).mp4")
        r = make_copy(det, clip, tmp)
        report[clip.name] = r
        if r.get("boxes") == 0 and old.exists():
            old.unlink()                               # an earlier copy of a clip with nothing to censor
        print(f"{clip.name}: " + (f"censored {r['censored_s']}s ({r['boxes']} sightings) -> {r['file']}" if r.get("file")
                                  else r.get("skipped") or "nothing to censor, no YouTube copy needed"))
    (DEST / ".youtube_blur.json").write_text(json.dumps(report, indent=1), "utf-8")


if __name__ == "__main__":
    main()
