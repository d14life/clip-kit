---
name: watch-video
description: "Actually watch a video from a URL: YouTube, Reels, TikTok, X, or a local file, via its transcript and frames. Use to watch, summarize, analyze, fact-check, or extract on-screen content."
---

# Watch a video

Claude cannot stream video. What it can do is **read a transcript** and **look at
frames as images** — together that is watching. This skill produces both.

## Run it

```bash
python3 ~/.claude/skills/watch-video/watch.py "<URL>"
```

It prints the paths it created. Then:

1. **Read `transcript.txt`** — what is said.
2. **Read frames** from `frames/` — what is shown. Pick ~10–15 spread evenly
   across the folder, plus every frame that looks like it holds text, a chart,
   code, a URL, or a UI.
3. Answer from both. Say plainly when something was not visible or not audible —
   never fill a gap with a guess.

Frames are the only way to catch website names, formulas, code, and on-screen
captions. Most short-form video puts its real payload **on screen, not in the
audio** — a transcript alone will miss it.

## Options

| flag | when |
|---|---|
| `--mode captions` | Long talks/lectures. Free, instant, no download. |
| `--mode whisper` | No captions, or you need exact wording. Local, no API cost. |
| `--mode auto` | Default. Captions over 20 min, whisper under. |
| `--fps 2` | Dense slides or fast screen-recordings. |
| `--max-frames 80` | Long tutorial where detail matters. Default 40. |
| `--no-frames` | Audio content only — skips the video download. |
| `--cookies cookies.txt` | Private/blocked posts. **Required for Instagram.** |
| `--out DIR` | Where to write. Default `./watched/<id>/`. |

## Cost

Downloading and transcribing are **local and free** — no tokens. Tokens are spent
only when reading frames, which is why frames are de-duplicated and capped.

For anything over ~20 minutes prefer `--mode captions`: the spoken words carry a
lecture, and downloading an hour of video to look at 3,600 near-identical frames
of a person talking buys nothing.

## Many videos at once

Run the script per URL, then fan out one subagent per video to read its
transcript and frames and return structured findings. Keep the reading in
subagents — frames are the expensive part and they should not all land in the
main context.

## Instagram / TikTok

Needs a logged-in `cookies.txt` (Netscape format, from a browser extension):

```bash
python3 ~/.claude/skills/watch-video/watch.py "<reel url>" --cookies ~/cookies.txt
```

Cookies contain a live session — never print, commit, or paste their contents.

## When it fails

- **`could not read video metadata`** — private, geo-blocked, or needs cookies.
- **`download failed`** — usually rate limiting; wait, or pass cookies.
- **Empty transcript** — the video has no speech. Rely on frames and say so.
- **`whisper env missing`** — create it:
  ```bash
  python3 -m venv ~/.venv-whisper && ~/.venv-whisper/bin/pip install faster-whisper
  ```
  then point `WHISPER_PY` in `watch.py` at it.

## Requirements

`yt-dlp` and `ffmpeg` (`brew install yt-dlp ffmpeg`), plus a `faster-whisper`
virtualenv for local transcription.
