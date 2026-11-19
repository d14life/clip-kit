"""Trim and level a recorded SixStars voice-over and generate word times.

    python tools/scripts/voice.py <slug> file:<path>

Writes a mono 44.1 kHz voice.wav and words.json for the episode.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
SR = 44100
MAX_PAUSE = float(os.environ.get("VOICE_MAX_PAUSE", "0.16"))  # seconds kept at every pause (long-form: 0.3)
PAUSE_FLOOR_DB = -38


def read_any(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy(), SR


def tighten(a, sr):
    """Cut every stretch of real silence down to MAX_PAUSE; trim the head and tail."""
    win = int(0.01 * sr)
    n = len(a) // win
    rms = np.sqrt((a[: n * win].reshape(n, win) ** 2).mean(axis=1) + 1e-12)
    quiet = 20 * np.log10(rms / (rms.max() + 1e-9)) < PAUSE_FLOOR_DB
    keep = np.ones(n, dtype=bool)
    max_w = int(MAX_PAUSE / 0.01)
    i = 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            run = j - i
            if i == 0:
                keep[i:max(i, j - 2)] = False
            elif j == n:
                keep[i + 4:j] = False
            elif run > max_w:
                cut = run - max_w
                mid = i + (run - cut) // 2
                keep[mid:mid + cut] = False
            i = j
        else:
            i += 1
    out = a[: n * win].reshape(n, win)[keep].reshape(-1)
    return out


def main():
    if len(sys.argv) != 3 or not sys.argv[2].startswith("file:"):
        sys.exit(__doc__)
    slug = sys.argv[1]
    episode = ROOT / "videos" / slug
    if not (episode / "script.json").is_file():
        sys.exit(f"Create the episode script at {episode / 'script.json'} first.")
    a, sr = read_any(sys.argv[2][5:])
    if len(a) < sr // 100 or not np.any(a):
        sys.exit("The take has no usable audio.")

    a = tighten(a, sr)
    if not len(a):
        sys.exit("The take is empty after trimming.")
    out_dir = ROOT / "public" / "audio" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "voice_tight.wav"
    sf.write(tmp, a, sr)
    tempo = float(os.environ.get("VOICE_TEMPO", "1.0"))
    final = out_dir / "voice.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-af",
                    f"atempo={tempo},loudnorm=I=-15:TP=-1.5:LRA=7,aresample={SR}", "-ac", "1", str(final)], check=True)
    tmp.unlink()

    from faster_whisper import WhisperModel

    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(final), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(np.frombuffer(raw, dtype=np.float32), word_timestamps=True, language="en")
    words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in s.words]
    if not words:
        sys.exit("No speech was detected. Check the take or supply checked word times.")
    (episode / "words.json").write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    dur = len(sf.read(final)[0]) / SR
    gaps = [words[i + 1]["s"] - words[i]["e"] for i in range(len(words) - 1)]
    print(f"voice.wav {dur:.2f} s, {len(words)} words heard, {len(words) / dur * 60:.0f} wpm, longest pause {max(gaps, default=0):.2f} s")


if __name__ == "__main__":
    main()
