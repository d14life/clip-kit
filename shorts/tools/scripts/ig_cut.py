"""Make the Instagram cut of a Short: <slug>-ig, with a FOLLOW tag and no spoken "subscribe".

Run:
    tools/.venv/Scripts/python.exe tools/scripts/ig_cut.py <slug>

Copies videos/<slug>/script.json to videos/<slug>-ig/ with "cta": "FOLLOW", drops every phrase that
says "subscribe", and cuts those words out of the processed voice (public/audio/<slug>/voice.wav),
shifting the word times after the cut. Then run build.py <slug>-ig and render it.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import align  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
GUARD = 0.04   # keep this much before the next kept word so its onset is not clipped
FADE = 0.008


def main():
    slug = sys.argv[1]
    out_slug = slug + "-ig"
    script = json.loads((ROOT / "videos" / slug / "script.json").read_text(encoding="utf-8"))
    heard = json.loads((ROOT / "videos" / slug / "words.json").read_text(encoding="utf-8"))
    audio, sr = sf.read(ROOT / "public" / "audio" / slug / "voice.wav")

    phrases = script["phrases"]
    drop = [("subscribe" in p["say"].lower()) for p in phrases]
    # a phrase that only finishes a dropped sentence ("what works.") goes with it
    for i in range(1, len(phrases)):
        if drop[i - 1] and not phrases[i - 1]["say"].rstrip().endswith((".", "?", "!", ",")):
            drop[i] = True

    flat, owner = [], []
    for pi, p in enumerate(phrases):
        for w in p["say"].split():
            flat.append(w)
            owner.append(pi)
    times, _ = align(flat, heard)

    cuts = []  # (t0, t1) in the voice, merged over runs of dropped phrases
    i = 0
    while i < len(flat):
        if drop[owner[i]]:
            j = i
            while j < len(flat) and drop[owner[j]]:
                j += 1
            t0 = times[i][0]
            t1 = (times[j][0] - GUARD) if j < len(flat) else len(audio) / sr
            cuts.append((t0, max(t0, t1)))
            i = j
        else:
            i += 1

    keep, pos = [], 0.0
    for t0, t1 in cuts:
        keep.append((pos, t0))
        pos = t1
    keep.append((pos, len(audio) / sr))
    n = int(FADE * sr)
    parts = []
    for k, (a, b) in enumerate(keep):
        seg = audio[int(a * sr):int(b * sr)].copy()
        if k > 0:
            seg[:n] *= np.linspace(0, 1, n)
        if k < len(keep) - 1:
            seg[-n:] *= np.linspace(1, 0, n)
        parts.append(seg)
    new_audio = np.concatenate(parts)

    new_heard = []
    for h in heard:
        if any(t0 - 1e-6 <= h["s"] < t1 for t0, t1 in cuts):
            continue
        shift = sum(t1 - t0 for t0, t1 in cuts if t1 <= h["s"] + 1e-6)
        new_heard.append({"w": h["w"], "s": round(h["s"] - shift, 3), "e": round(h["e"] - shift, 3)})

    script["slug"] = out_slug
    script["cta"] = "FOLLOW"
    script["phrases"] = [p for p, d in zip(phrases, drop) if not d]
    vdir = ROOT / "videos" / out_slug
    adir = ROOT / "public" / "audio" / out_slug
    vdir.mkdir(parents=True, exist_ok=True)
    adir.mkdir(parents=True, exist_ok=True)
    (vdir / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=1), encoding="utf-8")
    (vdir / "words.json").write_text(json.dumps(new_heard, ensure_ascii=False), encoding="utf-8")
    sf.write(adir / "voice.wav", new_audio, sr)
    removed = [p["say"] for p, d in zip(phrases, drop) if d]
    print(f"{out_slug}: dropped {removed or 'nothing'}; cut {sum(b - a for a, b in cuts):.2f} s; voice {len(new_audio) / sr:.2f} s")


if __name__ == "__main__":
    main()
