# Nobody can land this plane: scenario (for approval)

Story option 1 in STORY-OPTIONS.md. 1080x1920, **44.6 s, 23 shots** (1.2-2.55 s each).
Mix: gameplay 24.0 s, streamer pops 13.6 s (6 pops), **TRAILER 7.0 s (16 %)**, 3 memes.
Narrator: Fish "Vaibhav Natural Story Voice", Drama 3; the script is in FISH-SCRIPT.txt. VO times assume 2.8 words/s, and the narration is silent during every pop.
Contact sheet (the cropped result, one tile per shot): `sixstars-shorts/out/preview/planes-scenario.png`. Crop boxes drawn on the full frames: `<scratch>/planes2/cropcheck.jpg` (not included).

Gameplay files: `autoclipper/clips_ready/<streamer>/2026-11-18/<file>_horizontal.mp4`; Clix 113920 is in `clips_crowd`. These folders are read-only. Trailer files are in `sixstars-shorts/media/`. All times are seconds in the source file.

**Layout**
- `crop`: full-screen 9:16 cut from the 16:9 frame. The crop is 0.316 of the frame width; its left edge = clamp(focus x - 0.158, 0, 0.684).
- `desktop`: the whole 16:9 frame centred on a blurred copy of itself (layout A). Used only for wide shots and full-width GTA cards.

**Pops**
- Each pop plays the streamer's own audio. The facecam is cut from the **horizontal** file and placed as an inset at the top, over the cropped gameplay from the same file and time.
- Facecam boxes, as fractions of the 16:9 frame:

| Streamer | x | y |
|---|---|---|
| Clix | 0-0.25 | 0-0.25 |
| Lacy | 0-0.25 | 0-0.25 |
| recrent | 0-0.23 | 0.39-0.61 |
| ohnePixel | 0.05-0.43 | 0.6-1.0 |

- Do not use the `_vertical` files for insets: they have emoji (ohnePixel, Peanut) and captions burned over the camera box.
- Peanut has no facecam, so his pop is his audio plus a name tag, with no inset.

| # | time | narration line (exact words) | on screen (file, in-out s, what is visible) | pop (streamer, file, in-out, line) | SFX / meme | caption header | layout | focus x |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.0-1.6 | [shocked, fast] He jumped out. _(VO 0.0-1.1)_ | `theburntpeanut_182531_x7.9` 15.40-17.00: Jason leaps out of the seaplane mid-air over open sea and falls (body at x 0.25-0.47). Crop 0.23-0.55 keeps Peanut's avatar (x 0.17-0.23) out. In-game subtitle 'What are you f***ing thinking, man?' appears at 16.2 at the bottom: MASK it. | - | - | CAN ANYONE LAND IT? | crop | 0.39 |
| 2 **TRAILER** | 1.6-3.2 | [curious, quick] Can anyone land one? _(VO 1.6-3.0)_ | `Launch trailer rz1B4B2yBZY.mp4` 54.50-56.10: TRAILER Launch #25: biplane trailing pink smoke low over a crowded beach, high-rises behind. | - | - | CAN ANYONE LAND IT? | desktop | - |
| 3 | 3.2-5.2 | [teasing, fast] Clix takes off. Into the trees. _(VO 3.2-5.3)_ | `clix_113610_x4.7` 17.40-19.40: Clix's seaplane skims the swamp and ploughs into the mangrove bank (plane at x ~0.45). Facecam top-left (x 0.05-0.22) outside the crop. | - | - | 1. CLIX | crop | 0.45 |
| 4 | 5.2-6.8 | [deadpan] The plane was destroyed. _(VO 5.3-6.8)_ | `clix_113610_x4.7` 22.90-24.50: Red close-up of the wrecked fuselage ('Lapwing') in the trees; the red FAILED card lands at 24.0. Cut at 24.5, before the burned caption 'TO ME F*CKING' (~25 s). | - | - | 1. CLIX | crop | 0.50 |
| 5 | 6.8-8.4 | - | `clix_113610_x4.7` 26.60-28.25: Black FAILED / THE PLANE WAS DESTROYED card under the cam inset. Swear 'fucking long' ends 26.24 (outside); next 'I fucking hate' starts 29.08 (outside). | **Clix**, same file 26.60-28.25: "I hate the chat." | - | 1. CLIX | crop | 0.50 |
| 6 **TRAILER** | 8.4-10.3 | [storytelling] Lacy tries a water landing. _(VO 8.4-10.2)_ | `Trailer 2 VQRLujxTm3c.mp4` 141.80-143.70: TRAILER T2 #57: man in sunglasses rides a red chopper, a seaplane flies overhead. | - | - | 2. LACY | desktop | - |
| 7 | 10.3-12.2 | [hushed, fast] Then... a bird. _(VO 10.3-11.4)_ | `lacy_114351_x2.8` 14.20-16.00: Seaplane descending over grey water toward the city; a dark bird flaps beside the left wing at 15.0-15.8 (x ~0.36, inside the crop 0.29-0.61). Facecam top-left and chat top-right outside the crop. | - | - | 2. LACY | crop | 0.45 |
| 8 | 12.2-14.2 | - | `lacy_114351_x2.8` 16.00-18.06: Plane still descending under the cam inset. Swear 'I said fucking easy' ends 13.98 (outside). | **Lacy**, same file 16.00-18.06: "Did I just kill a bird in the air?" | - | 2. LACY | crop | 0.45 |
| 9 | 14.2-15.4 | - | `lacy_114351_x2.8` 19.10-20.30: The seaplane hits the water in a burst of spray (19.4), the screen goes red. | - | - | 2. LACY: BIRD STRIKE? | crop | 0.50 |
| 10 | 15.4-17.5 | - | `lacy_114351_x2.8` 21.60-23.70: Red 'wasted' card. Desktop because the word spans ~0.35 of the frame width and would be cut by a 9:16 crop. | - | snd_gta_2_wasted.mp3 (full, 2.1 s) on the card ~22.0 src, voice ducked 5 dB. Not GTA V wasted: that file is audible ~7.0 s and would run into recrent's segment. | 2. LACY: BIRD STRIKE? | desktop | - |
| 11 | 17.5-19.7 | [teasing] recrent tries one trick. _(VO 17.5-18.9)_ | `recrent_190205_x4.9` 11.60-13.80: Seaplane banking low over the sea, wing clips the bridge (12.8), then red cockpit close-up (13.6). Facecam (x 0.02-0.19, mid-left) outside the crop. | - | - | 3. RECRENT | crop | 0.58 |
| 12 | 19.7-22.1 | - | `recrent_190205_x4.9` 15.40-17.80: Red ПРОВАЛ (FAILED) card over the water under the bridge. Words 15.52-17.80 (хотел 15.52, один ends 17.80); cut before 'маневр' and the swear 'бля' at 18.74. EN subtitle required. | **recrent [RU]**, same file 15.40-17.80: "Хотел попробовать один… (EN sub: "Wanted to try one…")" | - | 3. RECRENT: FAILED | crop | 0.50 |
| 13 **TRAILER** | 22.1-23.7 | [amused, fast] ohnePixel takes a jet. _(VO 22.1-23.5)_ | `Trailer 2 VQRLujxTm3c.mp4` 36.80-38.40: TRAILER T2 #12: an airliner passes low over a Vice City highway under the green 'VCI Airport' signs, high-rises right. | - | - | 4. OHNEPIXEL | desktop | - |
| 14 | 23.7-26.2 | - | `ohnepixel_170420_x1.1` 33.60-36.05: Jet still rolling on the runway under the cam inset. | **ohnePixel**, same file 33.60-36.05: "Up, up, up! How the [BLEEP] am I gonna land this?" **BLEEP 35.16-35.26 (src)** | - | 4. OHNEPIXEL: NO LIFTOFF? | crop | 0.60 |
| 15 **TRAILER** | 26.2-28.1 | [building] Clix tries Lacy's landing. _(VO 26.2-27.6)_ | `Launch trailer rz1B4B2yBZY.mp4` 4.40-6.30: TRAILER Launch #3: aerial of BRIAN'S MARINA, seaplanes on the water. | - | - | 5. CLIX AGAIN | desktop | - |
| 16 | 28.1-29.7 | [teasing] Clix calls it easy. _(VO 28.1-29.5)_ | `clix_113920_x0.0 (clips_crowd)` 13.60-15.20: Same storm, same HUD 'Land near the docks' as Lacy; the seaplane drops toward the water. Clix's own 'Easy!' at 14.66 plays (natural audio). Cut 15.2, before 'I say it fuckin' easy' (15.66). | - | - | 5. CLIX AGAIN | crop | 0.50 |
| 17 | 29.7-32.2 | - | `clix_113920_x0.0 (clips_crowd)` 18.00-20.55: The plane banks hard in the storm under the cam inset. | **Clix**, same file 18.00-20.55: "A smooth as butter." | - | 5. CLIX AGAIN | crop | 0.50 |
| 18 | 32.2-33.8 | [tense, fast] Sideways... still sideways... _(VO 32.2-33.3)_ | `clix_113920_x0.0 (clips_crowd)` 21.60-23.20: Near-vertical bank a few metres over the water, storm clouds. Desktop so the tilt and the horizon read. | - | - | 5. CLIX AGAIN | desktop | - |
| 19 | 33.8-36.3 | - | `clix_113920_x0.0 (clips_crowd)` 23.40-25.90: Plane levels out upright on the water; Clix's own 'Okay! Nice!' (23.66-24.94) plays. Burned caption 'LOOKIN' GOOD!' / 'NICE!'. | - | ovl_gta_san_andreas_respect_mission_passed_g.mp4 (GTA SA 'Mission passed! Respect +' text card, catalog start 0.3 len 2.5, keyed) at 23.7 src | 5. CLIX: LANDED! | crop | 0.50 |
| 20 | 36.3-38.1 | [storytelling] Then Peanut. _(VO 36.3-37.0)_ | `theburntpeanut_182531_x7.9` 14.60-16.40: Seaplane over the sea chasing Pilot Pete's plane (HUD 'Catch up to Pilot Pete's plane' at 0-2 s); Jason leaps out at ~15.4 and falls beside the plane. | - | snd_wilhelm_scream.mp3 (full, 1.0 s) on the jump ~15.4 src | 6. PEANUT | crop | 0.55 |
| 21 | 38.1-40.1 | [deadpan, one beat] Jason abandoned the plane. _(VO 38.1-39.5)_ | `theburntpeanut_182531_x7.9` 22.20-24.20: FAILED card, then the black card 'FAILED / JASON ABANDONED THE PLANE.' (~23.5). Desktop so the full line reads. | - | - | 6. PEANUT: FAILED | desktop | - |
| 22 | 40.1-42.6 | - | `theburntpeanut_182531_x7.9` 35.45-37.95: Retry flight: seaplane over the sea, avatar inset. Words: 'pressed' runs 34.76-36.48 (drawn out), 'two buttons … right there.' 36.48-37.92. Clean, no swear in window. Peanut has no facecam: pop = his audio + name tag over full-screen gameplay, no inset. Sub alert 'Gifted 5 subs' sits at the bottom of the crop: mask. | **TheBurntPeanut**, same file 35.45-37.95: "…pressed two buttons at the same time right there." | - | 6. PEANUT: FAILED | crop | 0.50 |
| 23 | 42.6-44.6 | [direct, friendly] Bird, trees, or the button? _(VO 42.6-44.4)_ | `clix_182903_x5.1` 22.00-24.00: Clix's seaplane rolls sideways over the coast on a later flight; his own 'no no no no' (22.6-24.9, clean) under the line, ducked. Ends on a plane still in trouble. | - | - | WHAT GETS YOU FIRST? | desktop | - |

## Must-fix in the edit (seen in the frames)
1. **The `_horizontal` files are not raw.** They carry burned captions at about 85-92 % of the height, some of them starred swears:
   - Lacy, ~12.5-14: "I SAID F*CKING"
   - Clix 113610, ~25: "TO ME F*CKING"
   - Clix 113920, ~16-17.5: "F*CKIN' EASY"
   - Clix 182903, ~16.5: "KILL A F*CKING"
   - ohnePixel, ~35: "HOW THE F*CK" (inside shot 14)

   **Put a blur or cover strip over that bottom band on every gameplay shot**, and set our own captions on top.
2. Peanut's in-game NPC subtitle "What are you f***ing thinking, man?" is on screen from 16.2 in shots 1 and 20: mask it.
3. Shot 1: the edge of Peanut's avatar (x 0.17-0.23) touches the left of the crop. Mask it, or move focus x to 0.42.
4. Shot 22: a "Gifted 5 subs" alert sits at the bottom of the crop: mask it.
5. ohnePixel's jet has "America's #1 Porn Site" livery with a woman's image in the first 20 s of that clip. Only 33.6-36.05 is used (the jet rolling on the runway). Check at full resolution that the livery does not show there.
6. recrent's pop is in Russian: burn in the EN subtitle.
7. In shot 17, whisper hears Clix say "A smooth **ass** butter" ("ass" 18.72-19.68); the burned caption reads "AS". It is mild, and bleeping it would kill the line. Keep it unless the channel is strict.

## Swear check on the pops (whisper word timestamps)

| Pop | Window (s) | Line | Check |
|---|---|---|---|
| #5 Clix | 26.6-28.25 | "I hate the chat." (27.04-28.20) | Swears at ≤26.24 and from 29.08 are outside. The burned caption says "THIS CHAT". |
| #8 Lacy | 16.0-18.06 | "Did I just kill a bird in the air?" | Clean. "I said fucking easy" ends at 13.98. |
| #12 recrent | 15.4-17.8 | "хотел попробовать один" (15.52-17.80) | The swear "бля" at 18.74 is outside. |
| #14 ohnePixel | 33.6-36.05 | "Up, up... How the [BLEEP] am I gonna land this?" | **BLEEP 35.16-35.26.** |
| #17 Clix | 18.0-20.55 | "A smooth as(s) butter." | See note 7. |
| #22 Peanut | 35.45-37.95 | "...pressed two buttons at the same time right there." | Clean. His swear is at 16.64-17.44. |

Natural audio in non-pop shots is clean too:
- Shot 16: "Easy." 14.66-15.10. The cut at 15.2 lands before "I say it fuckin' easy" at 15.66.
- Shot 19: "Okay! ... Nice!" 23.66-24.94.
- Shot 23: "no no no".

## Unproven (worded as questions or flagged)
- **Did a bird cause Lacy's crash?** A bird is visible beside her left wing at 15.0-15.8, and she asks "Did I just kill a bird?" The impact is not seen, so the header carries a question mark ("BIRD STRIKE?").
- **Did Clix pass the mission?** He lands upright on the water at 24.6-25.6 ("NICE!"), but no result screen is in the clip. The mission-passed card in shot 19 is a joke overlay, not evidence. Swap it for a sound-only meme if that reads too strong.
- **Is it the same mission for Lacy and Clix?** Same HUD ("Land near the docks"), same storm, same NPC line. Strongly supported, but the game never says it.
- **Did Peanut skydive?** No parachute is seen. The game says "JASON ABANDONED THE PLANE." and he says he pressed two buttons. The narration only says "He jumped out."
- **ohnePixel never gets airborne** within the clip, so his header is "NO LIFTOFF?"
- Clix's "kill a bird" line in 182903 is not used, because no bird is visible.
- VO timings are an estimate at 2.8 words/s until the Fish render exists.

## Memes (3; each plays in full with the voice ducked 5 dB)
- Shot 10: `snd_gta_2_wasted.mp3` (2.1 s) on Lacy's wasted card. The GTA V wasted sounds stay audible for about 7 s and would bleed into the recrent shots.
- Shot 19: `ovl_gta_san_andreas_respect_mission_passed_g.mp4`, the GTA text card (start 0.3, length 2.5, green key), on Clix's landing.
- Shot 20: `snd_wilhelm_scream.mp3` (1.0 s) on Peanut's jump.

## Virality score (virality-predictor, TikTok / YouTube Shorts)

## Virality Score: 81/100

| Dimension | Score | Why |
|---|---|---|
| Hook | 21/25 | Cold open on the payoff: a man jumps out of a flying plane, then "Can anyone land one?". The open loop is set by second 3. |
| Value | 15/20 | Pure entertainment, with a clear running tally of who fails how. |
| Emotion | 17/20 | Five failures, then a real landing, then the Peanut twist. Seven genuine reactions. |
| Platform fit | 13/15 | 44.6 s, a cut every 1.2-2.5 s, full-screen 9:16. Burned captions must be covered first. |
| Share / CTA | 8/10 | "Bird, trees, or the button?" asks for a one-word comment pick. |
| Trend | 7/10 | GTA 6 is hot, and Clix, Lacy and ohnePixel are recognisable names. |

**What's working**
- Payoff-first open.
- Escalating list structure (1-6).
- The twist: Clix lands the same mission Lacy crashed.
- Ending on a fresh failure, not on the weak jet (the old draft's fix).

**What's holding it back**
- Six streamers in 45 s means less time to care about any one of them.
- The recrent pop needs reading (RU subtitle).
- The ohnePixel segment shows no flight.

**Fixes if it underperforms**
- Drop ohnePixel (shots 13-14) and give the 4 s to a longer Clix landing.
- Test "Nobody can land this plane" as the on-screen hook text at 0.0 s.
