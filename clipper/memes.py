"""Meme sounds, meme video overlays and emoji for the reaction FX, and the per-clip hit plan.

fx/memes/catalog.json lists every file with its kind (sound / overlay), moods, trim and loudness. New files dropped into
fx/memes/ are added by `python memes.py build` with a mood guessed from the file name (check them by eye, then edit).
Each entry is cut, levelled and (overlays) keyed once into fx/memes/cache/, so a render only reads ready files.

The user (2026-11-18): "ur hit is repetitive same sound and emojis" - so within one clip no sound is used twice and no
two hits in a row look alike (meme video / emoji / zoom / zoom+shake / flash)."""
import json
import random
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FX = HERE / "fx"
MEMES = FX / "memes"
CACHE = MEMES / "cache"
CATALOG = MEMES / "catalog.json"
FFMPEG = "ffmpeg"
MOODS = ("shock", "laugh", "fail", "hype", "cringe", "sus", "win")

# emoji png (160 px, made with Pillow + Segoe UI Emoji) per mood
EMOJI_CHARS = {"skull": "\U0001F480", "sob": "\U0001F62D", "flushed": "\U0001F633", "fire": "\U0001F525",
               "joy": "\U0001F602", "raised_eyebrow": "\U0001F928", "imp": "\U0001F608", "moai": "\U0001F5FF",
               "hundred": "\U0001F4AF", "scream": "\U0001F631"}
EMOJI_MOOD = {"laugh": ["joy", "sob", "skull"], "shock": ["flushed", "scream", "skull"], "fail": ["skull", "moai", "sob"],
              "sus": ["raised_eyebrow", "moai", "imp"], "cringe": ["flushed", "raised_eyebrow", "skull"],
              "win": ["fire", "hundred", "imp"], "hype": ["fire", "hundred", "scream"]}

# what the streamer said around the peak -> mood (first match wins)
MOOD_RE = [
    ("laugh", re.compile(r"\b(ha(ha)+|lol|lmao|laugh\w*|hehe)\b", re.I)),
    ("sus", re.compile(r"\b(sus|ayo|weird|suspicious|invite)\b", re.I)),
    ("cringe", re.compile(r"\b(ew+|cringe|gross|yikes|nasty|edg\w*|egg\w*)\b", re.I)),
    ("win", re.compile(r"\b(let'?s go|yes+|got (it|him)|won|win|gg|easy|god|passed|nice|good)\b", re.I)),
    ("fail", re.compile(r"\b(no+|damn|dang|shit|fuck\w*|dead|died|lost|missed|why)\b", re.I)),
    ("shock", re.compile(r"\b(what|wtf|huh|no way|who|oh my)\b|\?", re.I)),
]

# file-name keywords -> moods, for files added later without a hand-written entry
NAME_MOODS = [("laugh", "laugh"), ("lol", "laugh"), ("sus", "sus"), ("among", "sus"), ("doakes", "sus"),
              ("cringe", "cringe"), ("shock", "shock"), ("wow", "shock"), ("huh", "shock"), ("what", "shock"),
              ("boom", "shock"), ("fail", "fail"), ("pipe", "fail"), ("damage", "fail"), ("scratch", "fail"),
              ("no_no", "fail"), ("bruh", "fail"), ("passed", "win"), ("win", "win"), ("airhorn", "hype"),
              ("hype", "hype"), ("dance", "hype"), ("vibing", "hype"), ("sewey", "hype")]


def mood_of(text: str) -> str:
    for mood, rx in MOOD_RE:
        if rx.search(text or ""):
            return mood
    return "hype"


def load() -> list:
    try:
        return json.loads(CATALOG.read_text("utf-8"))["items"]
    except (OSError, ValueError, KeyError):
        return []


def run(args: list):
    r = subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode:
        raise RuntimeError(f"ffmpeg failed: {r.stderr[-800:]}")
    return r


def probe_dur(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def probe_size(path: Path) -> tuple:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    w, h = r.stdout.strip().split(",")[:2]
    return int(w), int(h)


def levels(path: Path) -> tuple:
    s = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    mean = re.search(r"mean_volume: (-?[\d.]+)", s)
    peak = re.search(r"max_volume: (-?[\d.]+)", s)
    return (float(mean.group(1)) if mean else -30.0), (float(peak.group(1)) if peak else 0.0)


def onset(path: Path) -> float:
    """Seconds of silence (under -45 dB) at the start of a sound file."""
    s = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path), "-af", "silencedetect=n=-45dB:d=0.02", "-vn", "-f", "null",
                        "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    st, en = re.search(r"silence_start: (-?[\d.]+)", s), re.search(r"silence_end: ([\d.]+)", s)
    return float(en.group(1)) if st and en and float(st.group(1)) <= 0.01 else 0.0


def src(item: dict) -> Path:
    return (MEMES / item["file"]).resolve()


def cached(item: dict, what: str) -> Path:
    """The ready file: what = 'wav' (levelled sound, also an overlay's own audio) or 'mov' (keyed overlay)."""
    win = f".{float(item['start']):g}-{float(item['len']):g}" if item.get("window") else ""   # a plan's own window
    out = CACHE / f"{Path(item['file']).stem}{'.full' if item.get('full') else ''}{win}.{what}"
    if out.exists():
        return out
    CACHE.mkdir(parents=True, exist_ok=True)
    cut = ["-ss", f"{item.get('start', 0)}", "-t", f"{item['len']}", "-i", str(src(item))]
    if what == "wav":
        run([*cut, "-vn", "-af", f"volume={item.get('gain_db', 0)}dB,afade=t=out:st={max(0, item['len'] - 0.08)}:d=0.08",
             "-ar", "48000", "-ac", "2", str(out)])
        return out
    x, y, w, h = item.get("crop") or (0, 0, 1, 1)
    vf = [f"crop=iw*{w}:ih*{h}:iw*{x}:ih*{y}", "scale=-2:'min(400,ih)'", "fps=30"]
    if item.get("key"):
        vf += [f"chromakey={item['key']}:{item.get('similarity', 0.15)}:0.08"]
        if item.get("despill", True):   # off for yellow art: despill takes the green out of yellow -> orange
            vf += ["despill=type=green:mix=0.6"]
    else:   # not a green screen: a framed picture with a white border
        vf += ["pad=iw+12:ih+12:6:6:white"]
    vf += ["format=rgba"]
    run([*cut, "-an", "-vf", ",".join(vf), "-c:v", "qtrle", str(out)])
    return out


def make_emoji():
    """Colour emoji pngs (160 px) that fx/ lacks, drawn locally from Segoe UI Emoji."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(r"C:\Windows\Fonts\seguiemj.ttf", 128)
    for name, ch in EMOJI_CHARS.items():
        out = FX / f"{name}.png"
        if out.exists():
            continue
        im = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((100, 100), ch, font=font, embedded_color=True, anchor="mm")
        im = im.crop(im.getbbox())
        side = max(im.size)
        sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        sq.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
        sq.resize((160, 160), Image.LANCZOS).save(out)
        print("emoji", out.name)


def build():
    """Add files in fx/memes/ that the catalog lacks (moods guessed from the name), measure length and loudness of
    entries that lack them, then fill the cache."""
    items = load()
    known = {i["file"] for i in items}
    for f in sorted(MEMES.glob("*")):
        if f.is_dir() or f.suffix.lower() not in (".mp3", ".wav", ".mp4", ".webm", ".mov", ".m4a", ".ogg"):
            continue
        if f.name in known:
            continue
        kind = "overlay" if f.suffix.lower() in (".mp4", ".webm", ".mov") else "sound"
        moods = sorted({m for k, m in NAME_MOODS if k in f.stem.lower()}) or ["hype"]
        d = probe_dur(f)
        item = {"file": f.name, "kind": kind, "mood": moods, "start": 0.0, "len": round(min(d, 2.5), 2),
                "guessed": True}
        if kind == "overlay":
            item.update({"key": "0x00FF00", "similarity": 0.15, "audio": False})
        else:
            item["role"] = "hit"
        items.append(item)
        print("added", f.name, moods, "(guessed - check by eye)")
    for it in items:
        if (it["kind"] == "sound" or it.get("audio")) and "gain_db" not in it:
            tmp = CACHE / "_probe.wav"
            CACHE.mkdir(parents=True, exist_ok=True)
            run(["-ss", f"{it.get('start', 0)}", "-t", f"{it['len']}", "-i", str(src(it)), "-vn", str(tmp)])
            mean, peak = levels(tmp)
            tmp.unlink()
            # every sound at the same loudness (mean -17 dB), never above -1.5 dBFS before the mix
            it["gain_db"] = round(min(-17.0 - mean, -1.5 - peak), 1)
    CATALOG.write_text(json.dumps({"version": 1, "about": __doc__.split("\n\n")[0], "moods": list(MOODS),
                                   "items": items}, indent=1), "utf-8")
    for it in items:
        if it["kind"] == "sound" or it.get("audio"):
            cached(it, "wav")
        if it["kind"] == "overlay":
            cached(it, "mov")
    make_emoji()
    print(len(items), "catalog entries")


# ------------------------------------------------------------------ the hit plan

VISUALS = ("emoji", "flash")      # reactions without a meme video, in rotation (no cam zoom/shake)
FILLER_VISUALS = ("zoom", "flash", "shake")


def plan(hits: list, seed: str, memes: int = 1, streamer: str | None = None) -> list:
    """hits: [{"t", "kind": "reaction"|"filler", "mood", "rank", "face"}] sorted by time (rank 0 = biggest).
    Adds "sound" (catalog item), "visual" and "emoji"/"overlay". No sound twice in a clip, no visual twice in a row,
    the `memes` biggest reactions get a meme video. Among the picks that fit the mood, the clip's own streamer's
    memes (catalog "streamer", e.g. channel "kaicenat" = "Kai Cenat") come first. Same seed -> same plan."""
    own = (lambda i: (i.get("streamer") or "").replace(" ", "").lower() == streamer.lower()) if streamer else None
    rng = random.Random(seed)
    items = [i for i in load() if not i.get("off")]
    sounds = [i for i in items if i["kind"] == "sound"]
    overlays = [i for i in items if i["kind"] == "overlay"]
    used, used_emoji, prev_vis, prev_emoji, vi, fi = set(), [], None, None, 0, 0
    big, taken = set(), []             # the biggest reactions, never two meme videos on neighbouring hits
    for idx in sorted((i for i, h in enumerate(hits) if h["kind"] == "reaction" and h.get("rank") is not None),
                      key=lambda i: hits[i]["rank"]):
        if len(big) < memes and all(abs(idx - j) > 1 for j in taken):
            big.add(hits[idx]["rank"])
            taken.append(idx)

    def pick(pool, mood=None):
        free = [i for i in pool if i["file"] not in used]
        fit = [i for i in free if mood in i["mood"]] if mood else free
        if own and mood:
            fit = [i for i in fit if own(i)] or fit
        choice = rng.choice(fit or free) if (fit or free) else None
        if choice:
            used.add(choice["file"])
        return choice

    for h in hits:
        mood = h.get("mood") or "hype"
        if h["kind"] == "reaction" and h.get("rank") in big:
            ov = pick(overlays, mood) or pick(overlays)
            if ov:
                h.update(visual="meme", overlay=ov)
                h["sound"] = ov if ov.get("audio") else pick([s for s in sounds if s.get("role") == "hit"], mood)
                prev_vis = "meme"
                continue
        if h["kind"] == "reaction":
            for _ in VISUALS:
                vis, vi = VISUALS[vi % len(VISUALS)], vi + 1
                if vis != prev_vis:
                    break
            h["sound"] = (pick([s for s in sounds if s.get("role") == "hit"], mood)
                          or pick([s for s in sounds if s.get("role") == "hit"]))
            if vis == "emoji":
                opts = [e for e in EMOJI_MOOD.get(mood, EMOJI_MOOD["hype"]) if e != prev_emoji]
                fresh = [e for e in opts if e not in used_emoji]
                h["emoji"] = prev_emoji = rng.choice(fresh or opts)
                used_emoji.append(h["emoji"])
        else:
            for _ in FILLER_VISUALS:
                vis, fi = FILLER_VISUALS[fi % len(FILLER_VISUALS)], fi + 1
                if vis != prev_vis:
                    break
            h["sound"] = pick([s for s in sounds if s.get("role") == "filler"])
        h["visual"] = prev_vis = vis
    return hits


def from_plan(entries: list, dur: float) -> list:
    """A hand-written plan (<base>.fx.json): [{"t": s in the final clip, "sound": catalog file | null,
    "visual": overlay file | emoji name | "flash" | null, "why": the trigger, "side"/"len": optional}] -> hits as
    plan() makes them. Catalog entries marked "off" are allowed here. A bad entry raises: a plan is written on purpose,
    so a typo must not turn silently into a missing meme."""
    items = {i["file"]: i for i in load()}
    hits, used = [], set()
    for e in sorted(entries, key=lambda e: float(e["t"])):
        t = float(e["t"])
        if not 0 <= t < dur:
            raise ValueError(f"fx plan: t={t} is outside the clip (0-{dur:.2f} s)")
        h = {"t": round(t, 2), "kind": "reaction", "why": e.get("why", ""), "visual": None, "sound": None,
             "side": e.get("side"), "len": e.get("len")}
        snd, vis = e.get("sound"), e.get("visual")
        if snd and snd == vis and snd in items and items[snd]["kind"] == "overlay" and items[snd].get("streamer"):
            # a streamer meme: his face pops up with its own words - one 1-2 s window of the clip, sound and picture
            ln = float(e.get("len") or 1.5)
            if not 0.8 <= ln <= 2.5:
                raise ValueError(f"fx plan: a streamer pop-up runs 1-2 s, not {ln}")
            if snd in used:
                raise ValueError(f"fx plan: sound {snd} used twice")
            used.add(snd)
            win = dict(items[snd], start=float(e.get("start", items[snd].get("start", 0))), len=ln, window=True,
                       crop=e.get("crop") or items[snd].get("crop"))
            h.update(sound=win, overlay=win, visual="popup", popup=True, len=ln)
            hits.append(h)
            continue
        if snd:
            if snd not in items or not (items[snd]["kind"] == "sound" or items[snd].get("audio")):
                raise ValueError(f"fx plan: {snd} is not a sound in the catalog")
            if snd in used:
                raise ValueError(f"fx plan: sound {snd} used twice")
            used.add(snd)
            # the whole file, untrimmed (user: "dont cut them"): from 0 to its real end
            h["sound"] = dict(items[snd], start=0, len=round(probe_dur(src(items[snd])), 2), full=True)
            h["t"] = round(max(0.0, t - onset(src(items[snd]))), 2)   # the first audible sample on the trigger
        if vis in items and items[vis]["kind"] == "overlay":
            h.update(visual="meme", overlay=items[vis])
        elif vis == "flash":
            h["visual"] = "flash"
        elif vis and (FX / f"{vis}.png").exists():
            h.update(visual="emoji", emoji=vis)
        elif vis:
            raise ValueError(f"fx plan: unknown visual {vis}")
        hits.append(h)
    return hits


def describe(hits: list) -> str:
    out = []
    for h in hits:
        snd = Path(h["sound"]["file"]).stem.replace("snd_", "").replace("ovl_", "") if h.get("sound") else "-"
        vis = (h.get("visual") or "-") + (f" {h['emoji']}" if h.get("emoji") else "") + (
            f" {Path(h['overlay']['file']).stem.replace('ovl_', '')}" if h.get("overlay") else "")
        out.append(f"{h['t']:.1f}s {snd} + {vis}" + (f" ({h['why']})" if h.get("why") else ""))
    return "; ".join(out)


if __name__ == "__main__":
    if sys.argv[1:] == ["build"]:
        build()
    else:
        print(__doc__)
