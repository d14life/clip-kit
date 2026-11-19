---
name: director
description: Use when planning shots, writing a shot list, cutting a montage, or reviewing a cut for short-form sports/app promo video (Reels/TikTok, 9:16, 15-45 s), especially Remotion UI clips plus three.js footage.
---

# Director: cutting pro short-form promos

Evidence: `references/pro-examples.md` (measured timings + sources). Anything marked [unverified] is a
heuristic from vendor blogs or house practice, not measured. Replace it with a number from our own
test cut when you have one.

Context: 9:16, 15-45 s, no live action, no talking head. Raw material = Remotion UI clips + three.js
stadium/match renders. You are the camera operator, so every "shot" is something you can re-render.

## A. Pre-production

1. **Write the one-line story first.** One sentence: "A fan opens the app, sees the live match, feels the
   roar, taps the CTA." Every shot must serve one beat of it. Cut anything that does not.
2. **Pick the emotional beat per shot before picking the shot.** Murch's Rule of Six ranks cut quality:
   emotion 51, story 23, rhythm 10, eye-trace 7, 2D plane 5, 3D space 4. When cut points
   conflict, sacrifice from the bottom: break spatial continuity before you break emotion or story.
   For fast video, eye-trace deserves more than 7%: put the next shot's focal point where the eye
   already is (centre-frame to centre-frame).
3. **Shot list = a table.** Columns: ID, beat, shot size (WIDE/MED/CLOSE/INSERT), content, camera
   move, source (Remotion comp / three.js scene), duration on screen (frames), text on screen, sound cue.
   Write inserts and cutaways as their own rows, not footnotes.
4. **Coverage per beat (render all four, then choose in the edit):**
   - WIDE: stadium, pitch, full phone/UI layout (establishes space).
   - MEDIUM: one player/one card/one panel (the story unit).
   - CLOSE: face-sized detail: a number ticking, the ball at the boot, a button.
   - INSERT: abstract punctuation (badge, crest, scoreboard digits, particle burst, light flare).
   Wide + medium + close of each key subject is the standard coverage set (wrapbook, howtofilmschool).
5. **Render long, cut tight.** House rule [unverified as a published number]: every raw take is at least
   2x the longest time it can be on screen, with extra tail. Reels shots live about 0.7-1.5 s (section B) so
   render 3-4 s minimum per take and 5-6 s for heroes you may ramp or push in on.
6. **Handles.** Render at least 0.5 s (15 frames at 30 fps) of still-moving frames BEFORE the action
   starts and 0.5 s AFTER it ends [house rule, unverified]. Handles let you slide the cut earlier/later
   to land on the beat and make dissolves and whips possible without freezing.
7. **Direction continuity map.** Decide screen direction per shot BEFORE rendering: if shot A's subject
   moves left-to-right, shot B starts moving left-to-right or is a deliberate reversal. A whip-pan
   transition works only when direction and speed of the outgoing and incoming pans match (nofilmschool).
8. **Lock the music first.** Pick the track, find BPM and the drop timestamp, mark the hit list (see D),
   then build the shot list to it. Reels are cut to the track, not the other way round.
9. **Safe zone.** Keep all text and CTAs inside the central area clear of the Reels/TikTok bottom UI and right
   action column [exact pixel margins unverified: check the platform spec before locking].

## B. The cut

### Hook, 0-2 s
- Something moving, in frame, on frame 1. No black, no logo sting, no fade-in. Measured: 4 of 6 pro sports films
  make their first cut within 0.04-1.2 s; the slow openers (Rain or Shine 2.8 s, Real Madrid BTS 6.1 s) are
  mood pieces, not Reels hooks.
- Face or product inside 1 s (Definitely City shows the kit on a person at 0.8 s). For us: a player
  silhouette, the app mid-action, or the stadium mid-motion. Not a title card.
- The hook must be the most visually striking thing you have, not the establishing shot. Open on action
  (Manchester Calling: feet moving, flash, hand pasting poster, all inside 1 s).
- Platform data claims (vendor blogs, [unverified] primary data): viewer decides in about 1.4 s on Reels, 1.7 s
  on TikTok. Counter-view: the "3 seconds" number comes from an old view metric, and a buildup hook won on
  completion. So: grab by 1 s, then give a reason to stay (a question, a countdown, an unfinished motion).
- First text appears by 0.5 s and says the payoff in 6 words or fewer.

### Average shot length (measured)
- Six pro sports films (6 files, 30-250 s): avg shot 0.78-1.76 s, median 0.68-1.29 s. The four 30-54 s kit
  films: avg 0.78-1.55 s. These figures likely OVERSTATE true length by 15-50% (detector misses soft cuts).
- Rule: **body average 0.8-1.3 s, medians under 1 s.** Hook 0.4-0.8 s per shot. Hero/UI hold 2-3 s.
- Vendor blogs say 2-4 s per cut [unverified]. That is a floor for explainers, too slow for sports energy.
- Never hold a three.js wide for longer than the camera move justifies: if nothing changes in the frame
  for 1 s, cut or move.

### Pacing curve: fast, slow, fast
- Measured shape: cut density in kit films rises in bursts (clusters of 3-6 cuts in under 2 s at about 6-9 s and the last
  4-6 s) with 2-3.5 s holds between them. Rain or Shine opens slow (first cut 2.84 s) and finishes densest.
- Template for 30 s: 0-2 s hook (cut every 0.5 s) / 2-8 s build (0.8-1 s) / 8-12 s breath (one 2-3 s hold on
  the UI hero, so the viewer can read it) / 12-24 s montage (0.5-1 s, accelerating) / 24-27 s drop
  burst (4-6 cuts in 2 s) / 27-30 s CTA hold 1.5-2.5 s (house rule).
- Every fast run needs a breath after it. Constant maximum speed reads as noise.
- Reserve the shortest shots (under 8 frames) for the peak. Do not spend them early.

### Beat-sync
- Measured: pros land 52-74% of cuts within 100 ms of an audio onset, 10-20 points above chance. They do not
  cut every beat. Cut on the beat for the hits that matter; follow picture action for the rest.
- Cuts land ON the beat, or 1-2 frames BEFORE it (picture slightly ahead of sound reads as tight).
  A cut after the beat reads as late.
- Hierarchy: kick/downbeat = cut or hard transition; snare = text pop, UI element lands; hi-hat/offbeat =
  micro motion (zoom, shake), not cuts. Drop = biggest visual event (reveal, flash, speed release).
- Quantise shot lengths to beat multiples (1/2, 1, 2, 4 beats). Cut a 4-beat phrase into 4 shots
  or 2 shots, never 3 uneven ones.
- Change something at every phrase boundary (8 or 16 beats): new location, new graphic style, new colour.

### Transitions pros use (and when)
| Use | When |
|---|---|
| Hard cut | Default. 80-90% of cuts [unverified share]. Cut on action: end shot A mid-motion, start B mid-motion (match on action). |
| Whip-pan / blur-wipe | Between shots with the same screen direction and speed. Cut at peak blur. Seen in Definitely City at about 3.0 s. |
| Flash frame (white/colour, 2-4 frames) | On a hit/drop. Seen in Manchester Calling at 0.4 s and 1.8 s. |
| Match cut | Shared shape/motion/position across the cut: ball arc to a UI progress arc, crest circle to radar ring, camera push into a screen to the same screen filling the next shot. |
| Speed ramp | Into/out of the hero moment: ease into slow, hold, ease out on the beat. S-curve, never linear. |
| Zoom-through / mask transition | For UI-to-world jumps (Cascade uses zoom tunnel and road wipes between scenes). |
| J / L cut | Pre-lap the next shot's sound (crowd, impact, whoosh) 4-12 frames before its picture [house range, unverified], or let the previous sound ring over the new picture. Makes a cut feel inevitable, not mechanical. |

**Amateur tells (do not use):** spinning/cube/page-turn wipes, star wipes, random preset transitions per cut,
cross-dissolve between fast shots, a different transition style every cut, fade-to-black mid-reel,
transitions longer than 8 frames on 0.5 s shots, whip-pans with mismatched direction. Keep one
transition vocabulary (hard cut + whip + flash) and repeat it so it reads as style.

### Text and UI on screen
- Reading time (house default, [unverified]): 0.25 s per word + 0.4 s minimum, 6 words max per card, 2 lines max.
  Example: a 4-word card = 1.4 s on screen. Reels viewers re-read nothing; if it does not read at first glance, cut words.
- Text lands on a beat and leaves before or on the next hit. Stagger by word only if the word itself carries the beat.
- UI is built up, not shown (Cascade builds an org chart node by node at about 1 s steps). Do not cut to a finished
  screen when you can animate it assembling.
- One idea per UI shot. The thumb-sized thing (button, number, score) fills at least a third of frame width.
- Highlight the one element the viewer should read: scale it, glow it, dim the rest.
- Contrast beats colour. Check white on every stadium background; add shadow/scrim.
- Hold CTA about 1.5-2.5 s (Cascade holds its end card about 6.5 s in 16:9 explainer form; too long for Reels).

### Sound design
- Layers: music bed (full-band), impact hits (every hard transition), whooshes (every whip/zoom, starting
  4-8 frames before the cut and peaking on it), UI ticks (on every UI element landing), crowd swell
  (ramps up into the drop, ducks after), riser (last 1-2 bars before the drop).
- Sidechain the music about 3-6 dB under the crowd/impact moments [house range, unverified].
- Silence is a tool: 3-6 frames of near-silence right before the drop makes the hit land.
- Hits/whooshes must be synced to the frame. If a sound sits 2 frames late it feels like a bug.
- Final loudness for social: about -14 LUFS integrated, true peak below -1 dBTP [platform norm, unverified;
  check current platform guidance].

## C. Review checklist for a finished cut (what a pro flags)

Watch it 3 times: muted, with sound only (eyes closed), then on a phone at arm's length.

1. **Frame 1:** is something moving? Does the first second show the payoff or product? Black frames at the start/end?
2. **Hook by 1.0 s and 2.0 s:** subject + motion + text present, or would you scroll?
3. **Dead air:** any shot where nothing changes for over 1 s? Any hold longer than the measured medians (about 1 s) without a reason?
4. **Rhythm:** plot shot lengths. Is there a fast / slow / fast shape, or is it one flat speed? Is there a real breath?
5. **Beat:** mark the top 5 hits in the track. Does each land a cut, flash or UI event within 1-2 frames?
6. **Cut quality:** any jump between two near-identical framings (jump cut)? Any screen-direction flip with no reason?
   Any action cut mid-motion on one side and static on the other?
7. **Transitions:** one vocabulary only? None longer than 8 frames? No template wipes?
8. **Text:** every card readable at its on-screen time? Inside the safe zone? Typos? Contrast on every background? No text on frame 1 that
   covers the hook subject?
9. **UI:** can you tell what the app does from the muted version alone? Is the single hero feature shown
   assembling, with its key number legible?
10. **Sound:** every transition has a sound; nothing is late; no clipping; crowd and music do not mask each other; silence before drop.
11. **CTA:** present, readable, 1.5-2.5 s hold, nothing animating that distracts.
12. **Loop/ending:** does the last frame cut back to the first cleanly (Reels autoloop)? A tidy loop earns re-watches [unverified claim].
13. **Length:** can any 4 shots be removed without the story breaking? If yes, remove them.
14. **Rule of Six pass:** for every cut that feels wrong, ask in order: emotion, story, rhythm, eye-trace, plane, 3D space. Fix the highest-ranked failure first.
15. **Render check:** 9:16, 30 fps, no stutter on three.js camera moves, no aliasing on thin UI lines, banding in dark gradients.

## D. Applying it in Remotion (30 fps)

Frame math: 30 fps. 1 s = 30 f, 0.5 s = 15 f, 0.25 s = 7.5 f (use 8 or 7, never fractions: Sequence frames
must be integers; round once, at plan time, so the error does not accumulate).

```ts
const FPS = 30;
const framesPerBeat = (bpm: number) => (FPS * 60) / bpm;      // 120 BPM = 15 f, 128 BPM = 14.0625 f
const beatFrame = (bpm: number, beat: number, offsetS = 0) =>  // absolute frame of beat N
  Math.round(offsetS * FPS + beat * framesPerBeat(bpm));
```

- **Cut on beat from a BPM:** compute each cut's absolute frame with `beatFrame` (rounding the absolute
  position, not the duration), then derive durations as differences. This stops drift on non-integer BPMs
  (128 BPM = 14.0625 f per beat; after 32 beats naive rounding is off by 2 f).
  Get `offsetS` (time of beat 0 in the audio) by ear or from a waveform; put the audio in with `<Audio src startFrom>`.
- **Layout:** use `<Sequence from={cut[i]} durationInFrames={cut[i+1]-cut[i]}>` with absolute frames from
  one cuts array (single source of truth), or `<Series>` + `<Series.Sequence durationInFrames>` when lengths
  are simple. Inside a Sequence `useCurrentFrame()` restarts at 0, so author each clip to its own time.
- **Handles:** give each clip comp extra duration and pass the cut in as `startFrom`/`endAt` (newer Remotion:
  `trimBefore`/`trimAfter` on `<OffthreadVideo>`; check installed version) so you can slide a cut by a few frames to hit the beat.
- **Transitions that overlap:** `@remotion/transitions` `TransitionSeries` overlaps clips, so total
  length shrinks by each transition's duration. Subtract it when counting frames. Hard cut = no transition.
  Whip/flash: usually easier as a 4-8 frame overlay layer (motion-blur slide + flash div) on top of a hard cut at the peak.
- **Flash/impact frames:** a full-frame `<AbsoluteFill>` white div, opacity `interpolate(f, [0,2,6],[0,1,0])`
  on the beat frame.
- **Speed ramps = frame remapping.** Do not use `playbackRate` for ramps (it is constant). Remap the output frame
  to a source frame with an eased speed curve:
  ```ts
  // out frames 0..N -> source frame; speed eases 1.0 -> 0.25 -> 1.0 around the hero hit
  const srcFrame = (f: number) => {
    let t = 0;
    for (let i = 0; i < f; i++) t += speedAt(i); // speedAt: S-curve between 1 and 0.25, peak slow on the beat
    return t;                                    // fractional source frame
  };
  ```
  For three.js: drive the scene by a time `t = srcFrame(f)/FPS` (deterministic render). For a video file use
  `<OffthreadVideo>` with source time derived from `srcFrame`, or pre-render the ramp. Fractional
  frames on rendered clips will blur or stutter: prefer rendering the three.js source at 60 fps and sampling.
- **Camera move for a cut-on-action:** drive the camera from the same `srcFrame` so the move continues
  across the cut; the next Sequence starts with the same velocity.
- **Text on beat:** precompute `textInFrame = beatFrame(...)`, animate with `spring` or `interpolate` starting
  that frame, with an exit at `+ wordCount*7.5 + 12` frames (0.25 s/word + 0.4 s, rounded).
- **Preview and verify:** render one still at every cut frame (`remotion still`) and at cut-1, cut+1, to check continuity.
  Render the whole reel to MP4 and run section C on the MP4, not on the Studio preview.

## E. Quick defaults (copy into a plan)

| Item | Default |
|---|---|
| Format / fps | 9:16, 1080x1920, 30 fps |
| Reel length | 24-30 s |
| First motion | Frame 1 |
| Face or product in frame | By 1.0 s |
| Average shot length | 0.8-1.3 s (measured pro median under 1 s) |
| Breath | One 2-3 s hold at about 30-40% of runtime |
| Last 3 s | Drop burst then CTA hold 1.5-2.5 s |
| Transitions | Hard cut, whip, flash only |
| Raw take length | At least 3 s per planned 1 s shot, plus 0.5 s handles |
| Text | Max 6 words, 0.25 s/word + 0.4 s |
