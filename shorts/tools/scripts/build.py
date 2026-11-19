"""Turn script.json + words.json into a frame-accurate timeline and cut the 9:16 footage clips.

Run:
    tools/.venv/Scripts/python.exe tools/scripts/build.py <slug> [--no-cut]

Reads   videos/<slug>/script.json, videos/<slug>/words.json, public/audio/<slug>/voice.wav
Writes  src/data/<slug>.json                 the timeline the Remotion composition draws
        public/footage/<slug>/sNNN_<hash>.mp4  one 1080x1920 clip per shot (cached)

Every time comes from the voice: a phrase starts on its first spoken word, the shot cuts there,
the caption words appear 0.03 s before they are spoken, and the Short ends on the last word.
"""
import difflib
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
FPS = 30
LEAD = 0.03
MAX_SHOT = 1.7


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def align(script_words, heard):
    a = [norm(w) for w in script_words]
    b = [norm(h["w"]) for h in heard]
    times = [None] * len(a)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = (heard[j1 + k]["s"], heard[j1 + k]["e"])
        elif tag == "replace" and j2 > j1:
            s, e = heard[j1]["s"], heard[j2 - 1]["e"]
            n = i2 - i1
            for k in range(n):
                times[i1 + k] = (s + (e - s) * k / n, s + (e - s) * (k + 1) / n)
    missed = sum(t is None for t in times)
    for i, t in enumerate(times):
        if t is None:
            prev = next((times[j] for j in range(i - 1, -1, -1) if times[j]), (0.0, 0.0))
            nxt = next((times[j] for j in range(i + 1, len(times)) if times[j]), None)
            end = nxt[0] if nxt else prev[1] + 0.2
            times[i] = (prev[1], max(prev[1] + 0.05, end))
    return times, missed


def fr(t):
    return int(round(t * FPS))


def crop_filter(x, z=1.0, y=0.5, pad=False):
    """9:16 window, centred on (x, y) as fractions of the frame, 1/z of the frame height tall.
    z=1 is the classic full-height crop. With pad, the window may run past the bottom edge (black below),
    which lifts HUD prompts that sit at the bottom of the frame clear of the caption band."""
    if z == 1.0:
        return r"crop=ih*9/16:ih:min(max(iw*{x}-ih*9/32\,0)\,iw-ih*9/16):0".format(x=x)
    h = 1.0 / z                      # window height, fraction of ih
    w = h * 9 / 16 * 9 / 16          # window width, fraction of iw (16:9 source)
    x0 = min(max(x - w / 2, 0.0), 1.0 - w)
    y0 = max(y - h / 2, 0.0)
    pre = ""
    if pad and y0 + h > 1.0:
        pre = "pad=iw:ih*{:.4f}:0:0:black,".format(y0 + h)
        return pre + "crop=iw*{:.5f}:ih*{:.5f}:iw*{:.5f}:ih*{:.5f}".format(w, h / (y0 + h), x0, y0 / (y0 + h))
    y0 = min(y0, 1.0 - h)
    return "crop=iw*{:.5f}:ih*{:.5f}:iw*{:.5f}:ih*{:.5f}".format(w, h, x0, y0)


def cut_clip(src, t, dur, x, out, z=1.0, y=0.5, pad=False, gamma=None, span=None, bars=0.0, layout=None, mask=None, nat=None, out_s=None):
    """span: the source window is only this many seconds long (a trailer shot): read just that, slow it to fill dur.
    bars: black letterbox fraction top and bottom, cropped away before the 9:16 window.
    layout "desktop": keep 16:9, a window 1/z of the frame centred on (x, y), scaled to 1080x608.
    mask: [[x0, y0, x1, y1], ...] source fractions blurred and darkened first (burned captions, avatars, alerts).
    nat: keep the source audio (the volume is applied in Remotion); out_s: source second where that audio must stop."""
    if layout == "desktop":
        s = 1.0 / z
        vf = "crop=iw*{s:.5f}:ih*{s:.5f}:iw*{:.5f}:ih*{:.5f}".format(min(max(x - s / 2, 0), 1 - s), min(max(y - s / 2, 0), 1 - s), s=s)
    else:
        vf = crop_filter(x, z, y, pad)
    if bars:
        vf = "crop=iw:ih*{:.4f}:0:ih*{:.4f},".format(1 - 2 * bars, bars) + vf
    for k, (x0, y0, x1, y1) in enumerate(mask or []):
        box = "iw*{:.4f}:ih*{:.4f}:iw*{:.4f}:ih*{:.4f}".format(x1 - x0, y1 - y0, x0, y0)
        vf = (f"split[m{k}a][m{k}b];[m{k}b]crop={box},boxblur=24:3,eq=brightness=-0.25[m{k}c];"
              f"[m{k}a][m{k}c]overlay=W*{x0:.4f}:H*{y0:.4f}," + vf)
    if span and dur > span:
        vf = "setpts={:.4f}*PTS,".format(dur / span) + vf
    size = "1080:608" if layout == "desktop" else "1080:1920"
    vf += f",scale={size}:flags=lanczos," + ("minterpolate=fps={fps}:mi_mode=blend" if span and dur > span else "fps={fps}").format(fps=FPS) + ",format=yuv420p"
    if gamma:  # lift a dark scene; a grade, not a change to what is shown
        vf += ",eq=gamma={:.2f}".format(gamma)
    input_args = ["-ss", f"{t:.3f}"] + (["-t", f"{span:.3f}"] if span else [])
    if Path(src).suffix.lower() in {".jpg", ".jpeg", ".png"}:
        input_args = ["-loop", "1", "-framerate", str(FPS)]
        src = str(ROOT / src)
    audio = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"] if nat else ["-an"]
    if nat and out_s:  # a swear right after the window must not leak in when the voice line runs long
        audio += ["-af", f"afade=t=out:st={max(out_s - t - 0.06, 0):.3f}:d=0.06"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *input_args, "-i", src, "-t", f"{dur:.3f}", *audio,
                    "-vf", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-g", "10", str(out)], check=True)


def main():
    slug = sys.argv[1]
    do_cut = "--no-cut" not in sys.argv
    vdir = ROOT / "videos" / slug
    script = json.loads((vdir / "script.json").read_text(encoding="utf-8"))
    heard = json.loads((vdir / "words.json").read_text(encoding="utf-8"))
    voice_len = len(sf.read(ROOT / "public" / "audio" / slug / "voice.wav")[0]) / 44100

    phrases = script["phrases"]
    flat, owner = [], []
    for pi, p in enumerate(phrases):
        for w in p["say"].split():
            flat.append(w)
            owner.append(pi)
    times, missed = align(flat, heard)
    print(f"{len(flat)} script words, {len(heard)} heard, {missed} not matched exactly")

    # "pre": [{"shot", "dur", ...}] on a phrase = wordless shots played before its first word; the voice gets
    # that much silence inserted there, so everything after it moves later.
    pre_fr = [sum(fr(s["dur"]) for s in p.get("pre", [])) for p in phrases]
    before = [sum(pre_fr[:pi]) for pi in range(len(phrases))]  # frames of pre inserted before phrase pi's pre
    starts_v = [times[owner.index(pi)][0] for pi in range(len(phrases))]
    starts_v[0] = 0.0
    starts = [s + before[pi] / FPS for pi, s in enumerate(starts_v)]
    shift = [(before[pi] + pre_fr[pi]) / FPS for pi in range(len(phrases))]
    total = fr(min(voice_len, times[-1][1] + 0.04) + shift[-1])
    f0 = [fr(s) for s in starts] + [total]

    tl_voice = {}
    if any(pre_fr):
        v, vsr = sf.read(ROOT / "public" / "audio" / slug / "voice.wav")
        parts, last = [], 0
        for pi, n in enumerate(pre_fr):
            if n:
                cut = int(round(starts_v[pi] * vsr))
                parts += [v[last:cut], np.zeros(n * vsr // FPS, dtype=v.dtype)]
                last = cut
        sf.write(ROOT / "public" / "audio" / slug / "body.wav", np.concatenate(parts + [v[last:]]), vsr)
        tl_voice = {"voice": f"audio/{slug}/body.wav"}

    clip_dir = ROOT / "public" / "footage" / slug
    clip_dir.mkdir(parents=True, exist_ok=True)
    shots, caps, items, mocks, sfx, title_words = [], [], [], [], [], []
    item_sfx = script.get("itemSfx", True)

    def place(tag, spec, a, n, split):
        # shot: [source, second, x] or [source, second, x, zoom, y]; optional "pad", "gamma", "layout", "mask", "nat"
        src_key, t, x = spec["shot"][:3]
        extra = (list(spec["shot"][3:]) + [1.0, 0.5])[:2] if len(spec["shot"]) > 3 else [1.0, 0.5]
        opts = {"z": float(extra[0]), "y": float(extra[1]), "pad": bool(spec.get("pad")), "gamma": spec.get("gamma"), "span": spec.get("span"), "bars": spec.get("bars", 0.0)}
        plain = opts == {"z": 1.0, "y": 0.5, "pad": False, "gamma": None, "span": None, "bars": 0.0}
        opts.update({k: spec[k] for k in ("layout", "mask", "nat", "out_s") if spec.get(k)})
        plain = plain and len(opts) == 6
        h = hashlib.md5((f"{src_key}|{t}|{x}|{n}" + ("" if plain else json.dumps(opts, sort_keys=True))).encode()).hexdigest()[:10]
        name = f"{slug}/{tag}_{h}.mp4"
        out = ROOT / "public" / "footage" / name
        if do_cut and not out.exists():
            for old in clip_dir.glob(f"{tag}_*.mp4"):
                old.unlink()
            cut_clip(script["sources"][src_key], t, n / FPS + 0.25, x, out, **opts)
        more = {k: v for k, v in (("layout", spec.get("layout")), ("vol", spec.get("nat"))) if v}
        if split and n / FPS > float(script.get("maxShot", MAX_SHOT)):
            half = n // 2
            shots.append({"from": a, "dur": half, "file": "footage/" + name, "start": 0, "zoom": 1.0, **more})
            shots.append({"from": a + half, "dur": n - half, "file": "footage/" + name, "start": half, "zoom": 1.16, **more})
        else:
            shots.append({"from": a, "dur": n, "file": "footage/" + name, "start": 0, "zoom": 1.0, **more})

    def add_item(it, at):
        n, label, icon = it
        items.append({"from": at, "to": total, "n": n, "label": label, "icon": icon})
        if item_sfx:
            sfx.append({"from": max(0, at - 4), "name": "whoosh", "vol": 0.5})
            sfx.append({"from": at, "name": "hit", "vol": 0.75})

    wi = 0
    for pi, p in enumerate(phrases):
        a, b = f0[pi], max(f0[pi + 1], f0[pi] + 1)
        s0 = a  # first frame of the spoken part
        for j, ps in enumerate(p.get("pre", [])):
            n = fr(ps["dur"])
            place(f"s{pi:03d}p{j}", ps, s0, n, False)
            if "item" in ps:
                add_item(ps["item"], s0)
            s0 += n
        place(f"s{pi:03d}", p, s0, max(b - s0, 1), True)
        words, key_used = [], False
        for w in p["say"].split():
            ws = times[wi][0] + shift[pi]
            wi += 1
            is_key = (not key_used) and norm(w) == norm(p.get("key", ""))
            key_used = key_used or is_key
            words.append({"t": w.upper(), "f": max(s0, fr(ws - LEAD)), "c": p["c"] if is_key else "w"})
        words[0]["f"] = s0
        if p.get("instant"):  # whole phrase readable from its first frame (used for the hook)
            for w_ in words:
                w_["f"] = s0
        caps.append({"from": a, "to": b, "words": words})
        for k, tw in enumerate(p.get("titleWords", [])):
            txt, _, col = tw.partition("|")
            title_words.append({"t": txt, "f": 0 if script.get("titleInstant") else a + k * max(3, (b - a) // 2), "c": col or "w"})
        if "item" in p:
            add_item(p["item"], s0)
        if (p.get("ask") or p.get("endItem")) and items and items[-1]["to"] == total:  # closing lines drop the header
            items[-1]["to"] = a
        if "mock" in p:
            m = dict(p["mock"])
            mocks.append({"from": a + 2, "to": total, "type": m.pop("type"), "props": m})
            sfx.append({"from": a + 2, "name": "pop", "vol": 0.6})
    for i in range(len(items) - 1):
        items[i]["to"] = items[i + 1]["from"]
    bounds = sorted([m["from"] for m in mocks] + [it["from"] for it in items] + [it["to"] for it in items] + [total])
    for m in mocks:
        nxt = next(bd for bd in bounds if bd > m["from"])
        m["to"] = min(nxt - 1, m["from"] + int(3.2 * FPS))

    tl = {"slug": slug, "fps": FPS, "frames": total, "titleEnd": items[0]["from"] if items else total,
          "titleWords": title_words,
          "askFrom": next((f0[i] for i, p in enumerate(phrases) if p.get("ask")), total),
          "subFrom": next((f0[i] for i, p in enumerate(phrases) if p.get("sub")), (items[-1]["from"] + 45) if items and not script.get("earlyOnly") else total),
          **({"cta": script["cta"]} if script.get("cta") else {}),
          **({"ctaLine": script["ctaLine"]} if script.get("ctaLine") else {}),
          **{"earlySubFrom": f0[i] for i, p in enumerate(phrases) if p.get("earlySub")},
          **tl_voice, **({"bed": False} if script.get("bed") is False else {}), "shots": shots, "items": items, "captions": caps, "mocks": mocks, "sfx": sfx}
    (ROOT / "src" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "src" / "data" / f"{slug}.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")

    durs = sorted(s["dur"] / FPS for s in shots)
    secs = total / FPS
    print(f"{total} frames = {secs:.2f} s | {len(shots)} shots = {len(shots) / secs * 60:.0f} cuts/min | "
          f"median shot {durs[len(durs) // 2]:.2f} s, longest {durs[-1]:.2f} s | "
          f"{len(flat) / secs * 60:.0f} wpm | {len(mocks)} mock-ups")


if __name__ == "__main__":
    main()
