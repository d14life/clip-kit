"""PLACEHOLDER timings + silent voice.wav so previews can render before any voice exists.
Run: python tools/scripts/placeholder_voice.py <slug>   (REPLACE with the real voice + words.json later)"""
import json, sys
from pathlib import Path
import numpy as np, soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
WPS, GAP = 2.7, 0.25
slug = sys.argv[1]
script = json.loads((ROOT / "videos" / slug / "script.json").read_text(encoding="utf-8"))
t, words = 0.0, []
for p in script["phrases"]:
    for w in p["say"].split():
        words.append({"w": w, "s": round(t, 3), "e": round(t + 1 / WPS, 3)})
        t += 1 / WPS
    t += GAP
(ROOT / "videos" / slug / "words.json").write_text(json.dumps(words, indent=1), encoding="utf-8")
adir = ROOT / "public" / "audio" / slug
adir.mkdir(parents=True, exist_ok=True)
sf.write(adir / "voice.wav", np.zeros(int((t + 0.5) * 44100), dtype="int16"), 44100)
note = "PLACEHOLDER: timings at 2.7 words/s, 0.25 s phrase gap, silent audio. Replace with the real voice + words.json, then rerun build.py.\n"
(ROOT / "videos" / slug / "PLACEHOLDER.txt").write_text(note, encoding="utf-8")
(adir / "PLACEHOLDER.txt").write_text(note, encoding="utf-8")
print(slug, round(t, 1), "s")
