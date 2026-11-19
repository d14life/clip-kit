# SOUND-RULES - mix spec for the GTA 6 shorts (spec only, nothing implemented yet)

## 0. Evidence quality (read first)
Search found no measured mixes from named top channels. What exists is editor guides and vendor blogs; the numbers below
are their consensus plus my own choices, marked **(mine)**. Treat dB values as a starting point to tune by ear. The meme rules are Damir's own.

Sources: [Zella - sound at cuts](https://zellahq.com/blog/sound-design-at-cuts-whoosh-impact-riser/) ·
[Pixflow - whooshes](https://pixflow.net/blog/cinematic-whoosh-sound-effects/) ·
[Krotos - sound design](https://krotos.studio/blog/what-is-sound-design-in-video-editing) ·
[CapCut - ducking](https://www.capcut.com/create/audio-ducking-for-clear-dialogue-in-video) ·
[Hollyland - ducking](https://store.hollyland.com/apps/arenza/blogs/creator-hub/what-is-audio-ducking) ·
[OpenClip - loudness](https://openclip.app/learn/audio-normalization) ·
[Fora Soft - LUFS 2026](https://www.forasoft.com/learn/audio-for-video/articles-audio/lufs-targets-per-platform-2026) ·
[ReelSoundEffect - meme overuse](https://reelsoundeffect.com/how-to-use-meme-sound-effects-without-overdoing-them/).

## 1. Facts from sources
| Topic | Rule | Source |
|---|---|---|
| Final loudness | -14 LUFS integrated, -1 dBTP. YouTube normalises to -14 (never boosts). TikTok/Reels publish no target; -14 is the safe single master. Optional louder derivative around -10 LUFS. | OpenClip, Fora Soft |
| Music under voice | 6-10 dB under dialogue (Krotos); music peaks 12-18 dB under dialogue peaks (domer.io via search); duck 6-12 dB, attack 30-80 ms, release 250-700 ms. Ducking 15-20 dB on every line is a flagged mistake; full silence sounds like an error. | Krotos, CapCut, Hollyland |
| Sidechain | Voice feeds the compressor on the music track. | OpenClip |
| Whoosh | -6 dB rel. speech (Zella), -12 to -18 (Pixflow), -18 to -24 (YouTubeSFX). Start just before the cut, peak on it, tail after; 400-500 ms for a 0.5 s move. High-pass at 80-100 Hz. If a viewer consciously notices it, it is too loud. | Zella, Pixflow |
| Impact | exactly on the cut; 50 ms early reads sloppy. | Zella |
| Riser | starts about 1 s before the key claim and stops abruptly on it; never over dialogue. | Zella, add.app |
| Restraint | do not sound every cut; sounding every join turns the mix into percussion. Mismatched energy is worse than silence. Mix order: dialogue, then music, then effects. | Zella |
| Meme sounds | one or two well placed beat ten; rotate, do not repeat. | ReelSoundEffect |

## 2. Mix spec (levels in dB relative to the narration, which is -15 LUFS short-term)
| Layer | Level | Notes |
|---|---|---|
| Narration | 0 (reference) | unchanged; `voice.py` already masters to -15 LUFS |
| Music bed | **-16 dB** while voice speaks, **-10 dB** in gaps > 0.4 s **(mine, inside the 6-18 dB source range)** | sidechain: threshold 0.03, ratio 6, attack 40 ms, release 400 ms. Genre: dark half-time trap / tension pad, no melody, no vocals. Fade in 0.2 s, out 0.3 s. |
| Bed during a streamer pop | **-24 dB** (fade 150 ms before join, back 150 ms after) | the pop keeps its own audio; the bed must not fight it |
| Game audio under narration | **-24 dB**, low-passed at 6 kHz **(mine, no source found)** | currently the footage is muted in `Short.tsx` (`OffthreadVideo muted`); only add if Damir hears the video as lifeless |
| Streamer pop audio | loudnorm to -15 LUFS (already) + 30 ms fade in/out | hard concat joins click today |
| Whoosh | **-12 dB** | lead 150 ms (already), only at the pop in-join and the pop out-join |
| Riser | **-14 dB** | 1.0 s riser ending exactly on the payoff word; max 1 per video |
| Impact / sub drop | **-6 dB** impact, **-8 dB** sub drop | on the payoff frame, max 1-2 per video |
| Record scratch | **-8 dB** | only on a "wait, what" reversal beat |
| Freeze-frame hit | **-9 dB** | on the freeze frame, 0 ms offset |
| pop_in blip | **-16 dB** | when a caption/mock card appears (existing `pop` role) |
| Meme sounds | **-10 dB** each, own loudnorm to -20 LUFS first, **ducked under any voice** (same sidechain as the bed, 8 dB) | see section 4 |
| Master | **-14 LUFS, TP -1.5**, one two-pass loudnorm as the LAST step after the outro | currently each stage normalises to -15 or leaves it; final is never measured |

SFX per beat type (all other cuts: silent):
| Beat | Sound |
|---|---|
| Hook / first frame | none, or `pop_in`; the voice is the hook |
| Cut into a pop | `whoosh_short` (lead 150 ms) |
| Cut out of a pop | `whoosh_down` (lead 100 ms) |
| Section change / new map or scene | `whoosh_long`, only if the picture moves |
| Build to the payoff (last 1 s before it) | `riser_1s` ending on the payoff word |
| Payoff | `impact_hit` + `sub_drop` together (-6 / -8 dB), no whoosh |
| Reversal ("but...", "turns out") | `record_scratch` |
| Freeze frame | `freeze_hit` |
| Death / fail ending | `wasted_hit.wav` (original), or the real Wasted meme if the claim risk is accepted |
| Win ending | the Mission Passed meme (section 4) |
Budget: **no more than 6 SFX + 5 memes per 30 s; whoosh only at pop joins; never two different SFX within 0.5 s.**

## 3. Transitions into and out of the pops
1. Whoosh peaks on the join frame (existing `WHOOSH_LEAD = 0.15`).
2. Bed ducks to -24 dB from join-150 ms, returns at out-join+150 ms.
3. Clip audio: 30 ms `afade` in and out so the concat does not click.
4. Narration never overlaps the pop audio (already true: the body is cut).

## 4. Meme rules (Damir, clipping session 2026-11-19, plus CLIPPING_GUIDE sections 9-10)
- 2-5 memes per video, only on BIG moments; the single biggest moment must have one.
- Each meme matches a game event or a spoken line; the plan states why.
- Play full length: never trimmed, never overlapping another meme, never running past the end of the video.
  Any sound longer than the room left before the end is not allowed there.
- Ducked under voices (-10 dB level and the 8 dB sidechain duck from section 2).
- No camera zoom, no emoji spam, no flashes. Sound only, plus the GTA text cards below.
- A streamer-face/voice meme only inside that streamer's own pop (`snd_kai_cenat_gta_6` only in a Kai pop).
- GTA text screens ("Mission passed! Respect +", "Wasted") are loved: use as the closing beat on a win / a fail.
- Never reuse one sound in a clip.

Files in `media/sfx/memes/` (all lengths measured with ffprobe; "END" = only as the last beat because it is long):
| Beat | Pick (length) |
|---|---|
| Payoff / shock | `snd_vine_boom` 1.25 s, `snd_sewey` 1.49 s |
| Reveal / sus | `snd_sus_sound_effect` 1.14 s, `snd_gta_cheat_activated_sound` 2.14 s, `snd_gta_v_busted` 7.84 s END |
| Laugh / fail-funny | `snd_bruh` 0.82 s, `snd_aughhh_tiktok` 1.84 s, `snd_ba_dum_tss` 3.37 s |
| Fail | `snd_emotional_damage_steven_he` 2.61 s, `snd_metal_pipe_falling` 3.17 s, `snd_sad_violin` 4.55 s, `snd_record_scratch` 0.65 s |
| Death ending | `snd_gta_v_wasted_sound_effect` 7.76 s END, text card `ovl_gta_v_wasted_black_screen_effect_video_s.mp4` 8.62 s END |
| Win ending | `snd_gta_v_mission_passed_jingle` 4.73 s, `snd_gta_sa_mission_passed_hq_respect` 7.47 s END, text card `ovl_gta_san_andreas_respect_mission_passed_g.mp4` 9.40 s END |
| Hype | `snd_trevor_scream_1` 2.57 s, `snd_airhorn_dj` 2.98 s |
| Streamer-only | `snd_kai_cenat_gta_6` 5.01 s (Kai pop) |
OPEN: the two text cards are 8.6 s and 9.4 s long. Whether the whole card plays (it would need the last 9 s of the short) or
only its text beat is a Damir decision; I did not inspect them frame by frame. Four overlong sounds (Hell Nah 10.4 s, Huh Cat 7.3 s,
Lamar 10.7 s, IV Mission Failed 16 s) were left out because they cannot play in full inside a 30 s short.

## 5. Code changes needed (not made)
1. **`src/Short.tsx` (bed `<Audio>`, lines 41-44)**: move the bed out of Remotion. Today it plays under the body only, so it
   vanishes inside every pop (the body is cut there). Remove it, or keep it only for the no-pop render.
2. **`tools/scripts/assemble.py::build()`**: after `concat`, add the bed: `amovie`/extra input `media/sfx/bed_dark_70.wav`
   (`-stream_loop -1`), `volume=-16dB`, then `sidechaincompress` keyed by `[acat]` (voice plus clip audio) so it ducks under any speech;
   extra `volume` envelope to -24 dB across each `[t-0.15, t+clip_len+0.15]` window (use the existing `joins` list and `frames`). New constants
   `BED`, `BED_DB`, `POP_BED_DB` beside `WHOOSH`, `LUFS`.
3. **`assemble.py` whoosh block (lines 190-197)**: replace the single `WHOOSH` with `whoosh_short` at the in-join (gain `-12 dB`, not `0.35`)
   and `whoosh_down` at the out-join; also `afade=t=in:d=0.03,afade=t=out:d=0.03` on each clip's audio chain (line 177).
4. **`assemble.py` new `plan.json` key `"memes": [{"t": sec, "file": "...", "why": "..."}]`**: new function `add_memes(plan, total)`:
   probe each file, require 2 <= count <= 5, sorted, `t + dur <= total`, `t_i + dur_i <= t_{i+1}`; `loudnorm I=-20`, `volume=-10dB`,
   `adelay`, sidechain-duck under voice (8 dB). Raise ValueError on any violation. Reject any streamer-tagged file outside that streamer's pop
   (use `streamer` from `autoclipper/fx/memes/catalog.json`; add a `"streamer"` field to each plan entry).
5. **`tools/scripts/build.py` lines 160-170 (`sfx.append`)**: replace the per-shot `whoosh`+`hit` pair with the beat table in section 2
   (riser at payoff-30 frames, `impact_hit`+`sub_drop` at the payoff, `record_scratch` on a reversal, nothing on ordinary cuts). Add a
   `beat` field to the shot/script schema if one does not exist (CONTRACT GAP: `videos/<slug>/script.json` has no beat type; Damir to name it).
6. **`src/types.ts` `Sfx`**: constrain `name` to the new filenames; `src/Short.tsx` line 47: `volume = 10 ** (s.db / 20)` instead of `s.vol * 0.5`; copy the used WAVs from `media/sfx/` into `public/sfx/`.
7. **`tools/scripts/add_outro.py` (after the concat, line 60)**: append the one master `loudnorm=I=-14:TP=-1.5:LRA=7` pass (two-pass, like `measure_loudness`).
8. **New `tools/scripts/mix_check.py`**: ffmpeg `ebur128` on the final mp4; fail unless integrated is -14 +/-1 LUFS and true peak <= -1 dBTP.
   Also check the bed is audible: bed-only gap loudness between -31 and -24 LUFS.
9. **Acceptance test after implementing**: render one short with 2 pops; verify by `mix_check.py`, then Damir listens (QA is by ear, not automated).

## 6. What was built (planes, 2026-11-19) and the names it added (CONTRACT GAP: no tech.md here; Damir to confirm)
Items 1-4, 7 and 8 above are now in code; 5 and 6 (beat-table SFX) were skipped: `script.itemSfx: false` just turns the old per-item whoosh/hit off.
Every new name is optional; leaving it out keeps the old behaviour.
- `script.json`: `bed: false` (no Remotion bed; assemble.py lays it), `itemSfx: false`, phrase `pre: [{shot, dur, item?, nat?, out_s?, layout?, mask?}]`
  (wordless shots before the phrase; silence is inserted into the voice), phrase/pre `layout: "desktop"`, `mask: [[x0,y0,x1,y1], ...]`
  (source-fraction boxes blurred and darkened), `nat: <gain>` (keep the clip's own audio), `out_s` (source second the audio fades out),
  `item: [0, ...]` (unnumbered header).
- `plan.json`: `bed: "<wav>"` (switches on the section-2 mix: bed, pop whooshes, 30 ms clip fades, memes), pop `h_out` with no `vertical`
  (horizontal-only pop), `x` (crop focus 0-1), `fit: [x0,y0,x1,y1]` (show that box full-width on black instead of the 9:16 crop), `cam: [x0,y0,x1,y1]` (inset box; omit for no inset), `memes: [{file, phrase, at, why,
  start?, len?, key?, similarity?, crop?, streamer?}]` (time = phrase caption start + `at`; `key` = green-screen overlay video).
- timeline (`src/data/<slug>.json`): `voice` (audio path, used when pre-silences are inserted), `bed: false`, shot `layout`, `vol`.
- `add_outro.py --lufs -14`: the master pass. `mix_check.py <mp4>`: the -14 / -1 dBTP gate (the bed-gap check in item 8 is not done).

## 7. Heavier meme pass (planes, 2026-11-19, Damir: "too light, more memes and meme sounds, GTA memes, no streamer memes")
- The meme count rule is now **at least 2, at most 5 starting in any 30 s window** (was 2-5 per video); every sound once.
- `plan.json` `sfx: [{file, phrase|pop, at?, lead?, db, why}]`: beat SFX at named moments (onset = anchor + at - lead; set
  `lead` to the file's measured peak so a whoosh peaks on the cut). When present it replaces the automatic whoosh in and out of
  every pop. Checked: at most 6 onsets in any 30 s, none within 0.5 s of another SFX or meme onset, all inside the video.
- `pop: j` (memes and sfx): anchor on the j-th pop's join instead of a caption start.
- Measured peaks: whoosh_short 0.22 s, whoosh_long 0.39 s, whoosh_down 0.22 s, riser_1s 0.96 s (ends 1.00 s), impact_hit and sub_drop 0.0 s.
