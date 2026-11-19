# How we make viral clips (lessons from the autoclipper session, 2026-11-18)

Everything lives in the `clipper/` folder of this kit. Read `STATE.md` there for the current state. Reuse these tools; don't rebuild them.

## 1. Picking the moment (the most important part)
- **Crowd proof beats algorithms.** Viewer-made Twitch clips, the ones with the most views, were the best signal. Chat spikes alone went 0 for 35 in review.
- **Twitch, no login needed:**
  - public GQL (client-id `kimne78kx3ncx6brgo4mv6wki5h1ko`) for VODs, chapters and clips;
  - streamlink for video;
  - anonymous IRC (justinfan) for chat.
- **Only the target game:** use the Twitch chapter markers, or the VOD category if there are no chapters.
- **Drop chat polls** ("type 1 in chat"): one reply making up ≥25% of chat is a poll, not a moment.

## 2. Cutting
- **The hook is speed:** the payoff lands in the first 1–3 s. Start ON the action, not before it. A cold-open teaser tested worse.
- **Length follows the moment,** up to 60 s. Start and end on sentence boundaries (whisper word timestamps).
- **Jump cuts:** remove only gaps that are silent AND have a still picture AND quiet game audio, at most 30% of the clip. A silent chase is action; keep it.
- **ffmpeg:** seek on the INPUT side (`-ss` before `-i`). Output-side seeking shifted the burned captions by about 8 s.

## 3. Layout (9:16, 1080x1920)
- The webcam goes on top, at y 230–838. The FULL 16:9 game frame goes below, at y 838–1446. Never crop the gameplay; the user hates that.
- No webcam: the full frame on a blurred background.
- **Webcam detection:** OpenCV YuNet face detector (`models/face_detection_yunet_2023mar.onnx`). Reuse the last webcam box per channel.
- **No title text and no channel link** on the video.

## 4. Captions
- Word-by-word, with the spoken word in yellow (libass ASS). Swears are censored. Keep them inside the safe zone, clear of the TikTok/IG like and comment buttons.
- Audio: `loudnorm=I=-14:TP=-1.5` + alimiter.

## 5. Effects and memes (what the user wants)
- **About one hit per 7-10 s, each tied to a game event or a spoken line (section 9 replaces the old "every 3-5 s"). EVERY hit different.** The user complained when the same sound and emoji repeated.
  - Never reuse a sound in one clip.
  - Rotate the visuals: meme video / emoji pop / flash (no cam zoom or shake, see section 9).
- **Real reactions** (loud, emphasized words, with the face check so game audio never triggers one) get a mood-matched meme sound:
  - laugh: bruh / aughhh
  - shock: vine boom / huh / oh hell nah / SEWEY
  - fail: metal pipe / record scratch / emotional damage
  - sus: sus
- **The 1–2 biggest moments** also get a meme video (placement: see section 9).
- **Assets:** `fx/memes/` (snd_*.mp3, ovl_*.mp4, downloaded with the user's OK from myinstants.com and archive.org), `fx/*.png` emoji (Pillow + Segoe UI Emoji, `embedded_color=True`), and `fx/boom.wav`, `whoosh.wav`, `tap.wav` (made with ffmpeg).
- **Code:** `autoclip.py`, functions `reaction_peaks`, `add_fx`, `memes.from_plan`. Test render: `fx_test/`.
- **Risk:** famous meme sounds can get YouTube copyright claims. The user accepted this.

## 6. Rating (gate before anything is shown or shipped)
- Every clip is scored by an INDEPENDENT reviewer agent with the virality rubric `~/.claude/skills/virality-predictor/SKILL.md` (0–100, converted to /10).
- The reviewer must not be the one who made the clip.
- **Ship only 6/10+.** Lower clips go to an "under 6" folder with the score in the file name; the user still watches them.
- The heuristic score in code is unreliable. Use the agent review.

## 7. Verifying (never claim without looking)
- Extract frames at 270x480 around each effect, hstack them, and look at them. Name what you see.
- Check the audio peak is under −1 dBFS and the voice is still audible under the sound effects.
- **Paid generation:** approve cheap keyframes first, then the expensive video (see `~/.claude/CLAUDE.md`).

## 8. Delivery
- File names follow "Streamer - funny situation". The user picks from 3 funny name candidates per clip.
- Batches of 5 clips at 6+ each go in `Downloads\GTA 6 - batch N\` with a captions.txt (campaign hashtags: Lacy #LACY, Clix #Clix).
- YouTube copies get a body-part-only pixel mosaic (`youtube_safe.py`, NudeNet on tiles). Never blur the whole frame.

## 9. Memes v2 (user feedback 2026-11-19: "no zoom in the camera", "ur meme dont match the thing happening", "too much a bit")
- **No zoom or shake on the webcam.** Ever. The punch-in and the filler zoom pulses are gone.
- **Memes are picked per moment by judgment**, in a plan file `<out_dir>/<base>.fx.json`: a list of `{"t", "sound", "visual", "why"}` (`visual` = overlay file, emoji name, `"flash"` or null). When the file exists it overrides the auto-pick.
- Every hit has a trigger in `why`: a game event in the frame (death, hit, fall, nudity, win) or a line the streamer says, timed to that frame or word within 0.2 s. Never a hit to fill time.
- **About 1 hit per 7-10 s** (5-7 in a 50 s clip). No sound twice. No filler beats. The whoosh on jump cuts stays.
- **Meme videos, 1-2 per clip:** green-screen ones keyed, ~420 px tall, in the bottom corner of the game panel away from the action. Non-green ones are a 0.8-1.5 s cutaway that replaces the game panel, then straight back. Never over the face or the captions.
- Prefer the clip's own streamer's memes (catalog `streamer`) when one fits the moment. Fit comes first.

## 10. Memes v3: sounds only (user 2026-11-19: "keep only sound bro and dont cut them", "only like 2-5 per clip")
- **Sounds only.** No meme videos, emoji, flashes or cutaways. The one exception is text cards like GTA SA "Mission passed! Respect +" (catalog `"text": true`) on a real win. The code strips every other visual.
- **2-5 meme sounds per clip**, only on the BIGGEST moments: the payoff, the streamer's biggest reaction, a big game event. The biggest moment always gets one. No small hits, no filler.
- **Full length, never cut.** A plan sound plays the whole file from its first audible sample (the leading silence is skipped automatically). Over ~4 s only if it fits before the next line that matters; otherwise pick a shorter one. The voice is ducked 5 dB under it and must stay understandable.
- GTA "Wasted" (`snd_gta_v_wasted.mp3`) is a user favourite: use it on any death, fail or big L.
- Captions must cover every spoken stretch, also while a meme sound plays.
