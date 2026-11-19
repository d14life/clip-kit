# autoclip — automatic Twitch live clipper

Leave it running. It waits for the stream, records it from the first second, watches chat,
and every time chat explodes it cuts the moment, writes captions and renders a ready-to-post
vertical short. No Twitch account, no token, no paid tools.

```
streamlink  ──► rolling recording (10 s segments, wall-clock stamped)
Twitch chat ──► score every 10 s ──► spike vs. 5-min baseline? ──► cut 30 s (ffmpeg)
                                                                 ──► captions (faster-whisper)
                                                                 ──► 9:16 short + 16:9 + .srt + thumbnail
```

## Setup (once)

```powershell
.\install.ps1
```

Installs `streamlink` and `faster-whisper` with pip, installs ffmpeg with winget if missing,
and runs the detector self-test. The whisper model (~460 MB for `small`) downloads on first run.

## Run

```powershell
python autoclip.py kaicenat theburntpeanut
```
Watches those channels. Offline ones are checked every 30 s and recording starts the moment they go live.

```powershell
python autoclip.py --game "Grand Theft Auto VI" --top 3 --lang en
```
Auto mode: finds the 3 biggest live English GTA VI streams and watches them; when one ends, the next
biggest takes its slot (re-checked every 5 min). `--lang` trusts the language each channel declares,
and some declare it wrongly (a Portuguese stream tagged EN was picked in testing). Captions detect the
spoken language per clip regardless.

```powershell
python autoclip.py --vod kaicenat --best 10
```
Past-stream mode: the best 10 moments of the channel's latest broadcast — including the one that is
live right now, so you get the part that happened before you started. It reads the whole chat replay
(no login) and the clips viewers already made, ranks moments where both agree highest, then downloads
only those 30 s pieces. A video link or ID works too: `--vod https://www.twitch.tv/videos/2932305259`.

Stop with **Ctrl+C**: clips already detected are still finished before it exits.
`--max-minutes 120` stops by itself.

## What you get

```
clips/
  index.jsonl                         one line per clip (all channels)
  kaicenat/2026-11-19/
    kaicenat_213405_x3.4_vertical.mp4    1080x1920, blurred fill, captions, channel credit
    kaicenat_213405_x3.4_horizontal.mp4  1920x1080 with captions
    kaicenat_213405_x3.4.srt             plain captions for re-editing
    kaicenat_213405_x3.4.jpg             thumbnail
    kaicenat_213405_x3.4.json            score, transcript, what chat was saying
```
`x3.4` = chat was 3.4 times busier than normal, so a higher number is usually a bigger moment.

## How the edit is made (rules taken from the skill packs, each one checked by code)

| Rule | From | Check |
|---|---|---|
| Text stays in x 120–960, y 210–1480 (clear of like/comment/share and the bottom caption) | ai-video-editing-skills `qc-check`, shortform-video-editor `principles.md` | every clip: the text layer is rendered alone and scanned frame by frame → `qc` in the clip's .json |
| Captions follow each word as it's said; 1–3 words; never end on "the/to/and…"; no "um/uh" | `captions`, `principles.md` | word timestamps from whisper; burned on the clip's own timeline |
| Hook = a human headline for the moment, built word by word, landing at 1.3 s; none rather than a weak one | Content Skills `virality`, `on-screen-text-writer` | viewer-clip titles first, else a repeated chat phrase of 2+ words; slurs filtered |
| Loudness about -14 LUFS, peaks under -1 dB | `qc-check` | loudnorm + limiter |
| Post text: the point first, credit, a few relevant tags | Content Skills `caption-and-hashtags` | `_post.txt` beside each clip |

Posting, DMs and comment replies from Content Skills are deliberately not part of this tool.

## Tuning

| Option | Default | Effect |
|---|---|---|
| `--sensitivity` | 2.0 | spike = this many times the normal chat score. Lower = more clips |
| `--pre` / `--post` | 20 / 10 | seconds kept before / after the moment chat starts reacting |
| `--buffer-minutes` | 30 | recording kept on disk; `0` keeps the whole stream (~3.6 GB/h at 1080p60) |
| `--quality` | 1080p60 … best | streamlink quality list |
| `--whisper-model` | small | `base` is faster, `medium` is more accurate |
| `--language` | auto | force caption language, e.g. `en` |
| `--zoom` | 1.0 | vertical: crop the sides (e.g. 1.3) so the game fills more of the short |
| `--encoder` | x264 | `amf` uses the AMD GPU encoder |
| `--formats` | vertical,horizontal | drop one to save time |

Every session's chat is logged to `work/<channel>/<session>/chat.jsonl`. To see where a different
setting would have clipped, replay it without recording anything:

```powershell
python autoclip.py --analyze work\kaicenat\20261119-200000\chat.jsonl --sensitivity 1.6
```

## Phone layout and clip length

- **Webcam on top, the full 16:9 game frame below** — gameplay is never cropped. The webcam is found
  automatically (a face that stays in one place); with no webcam the whole game frame sits on a blurred fill.
- **Length follows the moment** (15–60 s): the clip keeps going while chat is still hyped, and starts
  and ends on sentence breaks from the transcript, so nobody is cut mid-word.
- `--only-game "Grand Theft Auto VI"` clips only during GTA: past streams use Twitch's chapter markers,
  live streams re-check the category every minute.

## How the timing works

- Each recording segment's end is stamped with the wall clock when its last byte arrives;
  chat messages are stamped with the wall clock when they arrive. Both are on the same clock.
- Chat is scored per 10 s window: every message counts 1, hype words (KEKW, LMAO, ???, W, …) +0.5,
  "clip it" +1, each chatter at most 3 times per window, known bots ignored.
- A window is a spike when it beats `max(8, sensitivity × median of the last 5 min, median + 5√median)`.
  It fires once, then waits until chat calms down (and at least 45 s) before it can fire again.
- The clip anchors on the second the reaction starts (not the window), then keeps 20 s before and 10 s after.

## Honest limits

- It only works while the stream is live: it can't rewind a stream that has already ended.
- It finds moments **chat** reacts to. A great moment that chat ignores is missed.
- Live checks and auto mode use Twitch's public web API (no login); Twitch can change it.
- Clips are other people's content. Follow the streamer's clipping rules and the platform's terms before posting.
