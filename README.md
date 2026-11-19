# clip-kit

Everything needed to make two kinds of vertical shorts:

1. **GTA 6 Twitch clips** - pull the top Twitch clips, score them, render with captions, blur nudity, add a cover, post.
2. **Narrated shorts** (SixStars style) - a scripted voice-over over gameplay, built with Remotion + FFmpeg.

Plus a set of Claude Code skills that drive the workflow (scoring, shot planning, video reading).

## What is inside

| Folder | What |
|---|---|
| `skills/` | Claude Code skills: virality-predictor, agent-reach, watch-video, director, motion-reel, remotion, find-skills. See `skills/README.md` for machine-specific notes. |
| `clipper/` | The clip tool (`autoclip.py` live clipper, `export_clips.py`, `rerender.py`, ...) + guides (`CLIPPING_GUIDE.md`, `VIRAL_LESSONS.md`, `NUDITY_OPTIONS.md`, `ACCEPTANCE.md`). `clipper/extra/` has the helper scripts: `top.py` (Twitch top-clips list), `render1.py`, `cover.py`, `make_cover.py`, `pack.py`, `blur_spans.py`, `burn_hook.py`. |
| `shorts/` | The narrated-shorts pipeline: Remotion code (`src/`), build scripts (`tools/scripts/`), `SOUND-RULES.md`, and example scripts/scenarios in `videos/*/` (`FISH-SCRIPT.txt`, `SCENARIO.md`). |
| `sounds/` | Our own synthesised sound effects (claim-free) + `LICENSES.md`. |
| `research/` | Our GTA 6 trend and topic research (X, YouTube, TikTok, Instagram), video ideas, story options and clip reviews. Start with `research/README.md`. |
| `clipper/fx/` | The full meme library: `memes/` has 218 meme sounds (`snd_*.mp3`) and 54 meme overlays (`ovl_*.mp4`) with `catalog.json` (moods, trims) and `MEME_LIST.md`; plus emoji pngs and hit sounds. Run `python clipper\memes.py build` once to rebuild `fx/memes/cache/` (levelled/keyed copies). |

## Setup

You need:

- **Python 3.10+** (python.org)
- **ffmpeg** on PATH (Windows: `winget install Gyan.FFmpeg`)
- **yt-dlp** (`pip install yt-dlp`)
- **Node.js 18+** (for Remotion, `shorts/`)
- **Claude Code** (https://claude.com/claude-code)

```powershell
cd clipper
.\install.ps1            # installs streamlink + faster-whisper, checks ffmpeg, runs the self-test, prepares all memes
cd ..\shorts
npm install              # Remotion
pip install -r requirements.txt
```

### Install the skills

Copy the folders into your Claude Code skills directory:

```powershell
Copy-Item skills\* $HOME\.claude\skills\ -Recurse -Force     # Windows
# cp -r skills/* ~/.claude/skills/                           # macOS/Linux
```
(Skip `skills/README.md` if you like; it is only notes.) Restart Claude Code, then ask for a skill by name, e.g. "score this clip with virality-predictor".

## Workflow: clips

1. **Pull the top Twitch clips**: `python clipper\extra\top.py` (public Twitch data, no login). Or run the live clipper: `python clipper\autoclip.py --game "Grand Theft Auto VI" --top 3 --lang en`.
2. **Score** each candidate with the `virality-predictor` skill (0-100, shown as /10).
3. **Render + caption**: `clipper\extra\render1.py` / `autoclip.py` / `rerender.py` cut the moment, caption it with faster-whisper and make a 9:16 file.
4. **Blur nudity** if any (`clipper\extra\blur_spans.py`, options in `NUDITY_OPTIONS.md`).
5. **Hook + cover**: `burn_hook.py` (hook text), `make_cover.py` / `cover.py` (thumbnail).
6. **Pack and post**: `pack.py` collects the finished files; upload by hand to TikTok / YouTube Shorts / Instagram.

Read `clipper/CLIPPING_GUIDE.md` and `clipper/VIRAL_LESSONS.md` first.

## Workflow: narrated shorts

1. Write the scenario (`shorts/videos/<name>/SCENARIO.md`) and the voice script (`FISH-SCRIPT.txt`). Look at the examples.
2. Record the voice (see Fish Audio note), then `tools/scripts/voice.py` trims it and makes word times.
3. `tools/scripts/build.py` and `assemble.py` build the plan and mix; `npm run studio` / `npm run render` do the Remotion captions and layout.
4. `add_outro.py` joins an outro; `ig_cut.py` makes the Instagram version.
5. Mix check: `mix_check.py`. Sound rules: `shorts/SOUND-RULES.md`.

## Our rules

- **English clips**: score >= 8 and the moment is from the last 2 hours of the streamer's latest GTA 6 stream (the stream may have ended hours ago).
- **Russian clips**: any age, score >= 5.
- **No memes on clips.** Memes (sparingly) only on narrated shorts.
- **Blur nudity only.** Never censor, bleep, mute or star-out words.
- **Narration in full natural sentences**, never fragments. The closing question must be clear.
- **Open loop in every narrated short**: line 2 promises the most shocking fact/tip ("Stay to the end, because ...") and a late line pays it off. From `clipper/VIRAL_LESSONS.md`: watch time is the main factor, never a moment without a question.

## Things you must supply yourself

- **Fish Audio voice**: the narration uses Fish Audio TTS. You need your own account (fish.audio) and your own API key/voice; nothing of ours is included. Any other TTS works if you save a wav and run `voice.py`.
- **Gameplay/source footage**: not included. `shorts/tools/scripts/assemble.py` still has two hardcoded example paths (`Downloads\GTA 6\...`, `autoclipper\clips_crowd\...`, around lines 358-383); change them to your own files.
- **Fonts**: the Remotion code expects `shorts/public/fonts/Montserrat-BlackItalic.ttf` (SIL OFL, free from Google Fonts); not copied here.
- **Memes**: included in `clipper/fx/memes/` (from myinstants.com / archive.org). They are Rockstar's and other creators' content, so a video using them can get a Content ID claim; keep this repo private and don't re-share the files. `sounds/` is the claim-free fallback.
- **Env vars used by `clipper/extra/*.py`** (all optional, sensible defaults): `CLIP_WORK`, `CLIP_FRESH_DIR`, `CLIP_THUMBS_DIR`, `CLIP_READY_EN`, `CLIP_READY_RU`, `CLIP_UPLOAD_DIR`, `CLIP_READY_LOG`, `CLIP_NOTES_DIR`. Other: `WHISPER_PY` (watch-video), `ATLAS_API_KEY` (motion-reel Atlas script, optional paid service).

Some guides still read "his"/"Damir" - they were written by the original owner for himself; read them as examples.
