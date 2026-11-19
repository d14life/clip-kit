# Leonida's worst drivers: scenario (for approval, no voice generated)

Story option 2 in STORY-OPTIONS.md, rebuilt around the clips that actually show driving. 1080x1920, **50.1 s, 27 shots** (1.5-2.9 s each, most 1.6-2.0).
Mix: gameplay 31.7 s (63 %), streamer pops 10.5 s (6 pops, 21 %), **TRAILER 8.0 s (16 %, 4 shots)**, 6 memes, 4 beat SFX.
Narrator: Fish voice, same settings as Planes v2. Script: `FISH-SCRIPT.txt` (12 lines, hook in line 1, closing question in line 12). VO times assume 2.8 words/s; the narration is silent during every pop. **Not rendered, no paid voice.**
Contact sheet (the cropped result, one tile per shot, pops show the facecam inset): `sixstars-shorts/out/preview/drivers-scenario.png`.
Sources, rejected candidates and gaps: `SOURCES.md`.

Gameplay files: `autoclipper/clips_ready/<streamer>/2026-11-18/<file>_horizontal.mp4` (read-only). Trailer files are in `sixstars-shorts/media/`. All times are seconds in the source file.

**Layout** (same contract as Planes)
- `crop`: full-screen 9:16 cut from the 16:9 frame, 0.316 of the frame width; left edge = clamp(focus x - 0.158, 0, 0.684).
- `desktop`: the whole 16:9 frame centred on a blurred copy of itself. Used only for the four trailer shots.
- Pops: the streamer's own audio, facecam cut from the **horizontal** file as an inset at the top over the cropped gameplay from the same file and time. Never use `_vertical` files for insets.
- Facecam boxes (fractions of the 16:9 frame): Lacy 0-0.25 x 0-0.25; xQc 0-0.22 x 0-0.25; Clix 0-0.25 x 0-0.25; Jynxzi 0-0.22 x 0.30-0.78. Peanut has no facecam: his pop is his audio plus a name tag, no inset.
- All the facecams sit at the left edge, outside every crop used (focus x >= 0.45 puts the left edge at 0.29).

| # | time | narration line (exact words) | on screen (file, in-out s, what is visible) | pop | SFX / meme | caption header | layout | focus x |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.0-1.6 | [shocked, fast] Nobody in Leonida should ever be allowed behind a wheel. _(L1, VO 0.0-3.4)_ | `jynxzi_230429_x4.7` 14.10-15.70: first-person on a motorbike, phone in hand; the bike hits a brown pickup at ~14.8 and Jynxzi's body is thrown onto the road. Cold open on the payoff. | - | **meme `snd_vine_boom` (1.25 s) at 0.7** on the impact | NOBODY CAN DRIVE | crop | 0.55 |
| 2 **TRAILER** | 1.6-3.6 | _(L1 continues)_ | `QdBZY2fkU-0.mp4` (Trailer 1) 70.30-72.30: red 70s muscle car driving past a "PAWN" sign (SHOTLOG T1 #45). | - | - | NOBODY CAN DRIVE | desktop | - |
| 3 **TRAILER** | 3.6-5.6 | [curious] So who is the worst driver in GTA 6? _(L2, VO 3.6-6.8)_ | `VQRLujxTm3c.mp4` (Trailer 2) 28.00-30.00: man in cap and sunglasses driving, seen from the passenger side (SHOTLOG T2 #9). | - | - | WHO DRIVES WORST? | desktop | - |
| 4 | 5.6-7.2 | _(L2 continues)_ | `lacy_172620_x4.4` 1.60-3.20: Lacy's blue pickup (damaged body) swings across the road with tyre smoke. | - | - | 1. LACY | crop | 0.50 |
| 5 | 7.2-9.1 | [teasing, fast] Lacy spins his pickup out. _(L3, VO 7.2-9.0)_ | `lacy_172620_x4.4` 4.40-6.30: the pickup slides sideways, a lorry ahead; the car faces the camera at ~6. | - | - | 1. LACY | crop | 0.45 |
| 6 | 9.1-10.7 | - | `lacy_172620_x4.4` 6.30-7.90: pickup close up, HUD turn arrow. Words "My car is cooked" 6.54-7.78 (clean; the next line, the giveaway, starts at 11.64, outside). | **Lacy**: "My car is cooked." | sfx `whoosh_short` (peak on the join 9.1); **meme `snd_bruh` (0.82 s) at 10.45** | 1. LACY | crop | 0.50 |
| 7 | 10.7-12.3 | [storytelling] xQc drives a box truck through downtown. _(L4, VO 10.7-13.2)_ | `xqc_111750_x1.1` 8.00-9.60: white box truck from behind on a downtown street, shop fronts. | - | - | 2. XQC | crop | 0.50 |
| 8 | 12.3-13.9 | _(L4 continues)_ | `xqc_111750_x1.1` 12.20-13.80: the truck turns a corner under the low sun. | - | - | 2. XQC | crop | 0.50 |
| 9 | 13.9-15.55 | - | `xqc_111750_x1.1` 2.50-4.15: box truck in a dark alley. Words "I mean, I had to" ends ~2.55, "Cops were everywhere" 3.21-4.11. "Shit" is at 4.87, outside. | **xQc**: "...I had to. Cops were everywhere." | **meme `snd_sus_sound_effect` (1.14 s) at 14.75** on "Cops were everywhere" | 2. XQC | crop | 0.50 |
| 10 | 15.55-18.45 | [amused] Jynxzi blames his bad driving on stick drift. _(L5, VO 15.55-18.4)_ | `jynxzi_211433_x3.7` 16.00-18.90: two men in a pickup cab (the in-game scene around his line). **Jynxzi's own character is not shown driving here.** | - | - | 3. JYNXZI | crop | 0.62 |
| 11 | 18.45-20.24 | - | `jynxzi_211433_x3.7` 9.40-11.19: the game is paused (blurred menu behind the cam). Segment 7.41-11.19 "Wait chat, I think I know why my driving is bad. It's cuz of stick drift, bro": **pop start 9.40 is an estimate, needs word timestamps** so the cut does not land mid-word. | **Jynxzi**: "It's cuz of stick drift, bro." | **meme `snd_aughhh_tiktok` (1.84 s) at 19.75** on "bro" | 3. JYNXZI | crop | 0.62 |
| 12 | 20.24-22.94 | [teasing, fast] Then he texts while riding a motorbike. _(L6, VO 20.24-22.74)_ | `jynxzi_230429_x4.7` 4.00-6.70: first-person on the bike, a phone with app icons held over the handlebars. | - | - | 3. JYNXZI | crop | 0.50 |
| 13 | 22.94-24.74 | [deadpan] He crashes into a pickup. _(L7, VO 22.94-24.7)_ | `jynxzi_230429_x4.7` 15.60-17.40: aftermath, Jynxzi's character kneeling beside the fallen bike next to the pickup. | - | - | 3. JYNXZI | crop | 0.55 |
| 14 | 24.74-26.74 | - | `jynxzi_230429_x4.7` 20.55-22.55: Jynxzi's character on the road beside the bike. Words "That is why you don't text and drive" (segment starts 20.52). Next words "cheese it, I've got a bloody eye" are outside. | **Jynxzi**: "That is why you don't text and drive." | sfx `whoosh_short` at the join 24.74 | 3. JYNXZI: TEXT + DRIVE | crop | 0.55 |
| 15 **TRAILER** | 26.74-28.74 | [building] Then Clix's pickup goes flying. _(L8, VO 26.74-28.84)_ | `rz1B4B2yBZY.mp4` (Launch) 46.20-48.20: white police car driving on a Miami-style street (SHOTLOG Launch #22). | - | - | 4. CLIX | desktop | - |
| 16 | 28.74-30.44 | _(L8 continues)_ | `clix_151257_x5.4` 16.90-18.60: Clix's grey Vapid pickup in mid-air over the sea, sky behind (airborne 17.0-19.3). | - | **meme `snd_gta_cheat_activated_sound` (2.14 s) at 28.85** (runs 0.5 s into the pop, ducked) | 4. CLIX | crop | 0.60 |
| 17 | 30.44-31.94 | - | `clix_151257_x5.4` 21.35-22.85: the pickup back on the bridge road, caption "OH MY GOSH". "Yo, oh my gosh" is 21.37-22.85. | **Clix**: "Yo, oh my gosh." | sfx `whoosh_short` at the join 30.44 | 4. CLIX | crop | 0.50 |
| 18 | 31.94-33.74 | [hushed] recrent slides under a bridge and gets stuck. _(L9, VO 31.94-35.1)_ | `recrent_182756_x4.5` 4.00-5.80: red pickup sliding sideways under a causeway bridge. Facecam (x 0-0.23, mid-left) is outside the crop. | - | - | 5. RECRENT | crop | 0.50 |
| 19 | 33.74-35.34 | _(L9 continues)_ | `recrent_182756_x4.5` 17.00-18.60: the pickup tilted on rocks at the roadside by a fence. | - | - | 5. RECRENT | crop | 0.55 |
| 20 **TRAILER** | 35.34-37.34 | [tense] Then Peanut says he's still got it. _(L10, VO 35.34-38.2)_ | `VQRLujxTm3c.mp4` (Trailer 2) 45.50-47.50: POV from inside a car at a mural wall with a white police car and a running person (SHOTLOG T2 #15). | - | - | 6. PEANUT | desktop | - |
| 21 | 37.34-38.94 | _(L10 continues)_ | `theburntpeanut_190028_x2.4` 3.00-4.60: orange sports car on a road with traffic cones. Natural line "boys wish we still got it" is on screen; he says "still got it" at 6-9. | - | - | 6. PEANUT | crop | 0.50 |
| 22 | 38.94-40.94 | - | `theburntpeanut_190028_x2.4` 10.10-12.10: the same car on an open road, caption "ALMOST SAW GOD". "Almost saw God right there" is 10-12 (segment-level time; check the start). | **TheBurntPeanut**: "Almost saw God right there." | - | 6. PEANUT | crop | 0.50 |
| 23 | 40.94-42.74 | [deadpan, one beat] Then his car drives straight into the river. _(L11, VO 40.94-44.1)_ | `theburntpeanut_190028_x2.4` 13.40-15.20: the car leaves the tarmac across grass towards the bank. | - | sfx `impact_hit` at the splash, 42.54 (src ~15.0) | 6. PEANUT | crop | 0.50 |
| 24 | 42.74-44.34 | _(L11 continues)_ | `theburntpeanut_190028_x2.4` 16.00-17.60: the car in the river, spray, nose down. His own "and it's gone" is audible (16-20). | - | - | 6. PEANUT: THE RIVER | crop | 0.50 |
| 25 | 44.34-45.94 | - | `theburntpeanut_190028_x2.4` 18.80-20.40: the car sinks, only the roof above the water. Silent beat for the meme. | - | **meme `snd_sewey` (1.49 s) at 44.40**, ends 45.89, before the closing line | 6. PEANUT: THE RIVER | crop | 0.50 |
| 26 | 45.94-48.14 | [direct, friendly] Who should lose their license first: xQc, Lacy, Jynxzi, or Peanut? _(L12, VO 45.94-49.9)_ | `theburntpeanut_190028_x2.4` 22.00-24.20: Peanut's character climbs out onto the bank. | - | - | WHO LOSES THEIR LICENSE? | crop | 0.50 |
| 27 | 48.14-50.24 | _(L12 continues)_ | `lacy_190439_x7.7` 26.00-28.10: Lacy's blue pickup on a dirt patch with police cars arriving at the left. | - | - | WHO LOSES THEIR LICENSE? | crop | 0.55 |

(All times are the planned timeline; total 50.1-50.2 s. The table's last row ends at 50.24 because shot 27 was lengthened by 0.1 s to fit the closing line.)

## Must-fix in the edit (seen in the sheet frames)
1. **The `_horizontal` files carry burned captions at the bottom.** Visible in the sheet: "MY CAR IS COOKED" (#6), "COPS WERE" (#9), "YOU DON'T" / "STICK" (#10, #11, #14), "OH MY GOSH" (#17), "BOYS WISH WE STILL" / "ALMOST SAW GOD" / "AND IT'S GONE" (Peanut). **Cover the bottom band on every gameplay shot** and put our own captions on top. Check the burned text for starred swears before the cover goes on (not checked frame by frame here).
2. Shots 11 and 14 (Jynxzi): the facecam box is tall (0.30-0.78 of the height). It reads fine in the sheet; if the inset looks too big, shrink it to the face only.
3. Shot 17 (Clix): the facecam box 0-0.25 cuts the top of his head slightly in the sheet. Widen the box by about 0.03.
4. Shot 11: the gameplay behind Jynxzi is a blurred pause menu. It is a weak pop picture (strong audio). Alternative: take the pop from 211433 at 16-20, when the cab scene is on screen, if a good line exists there (not checked).
5. Pop 11 start (9.40) and pop 22 start (10.10) are segment-level estimates; get whisper word timestamps like Planes before locking the cut.

## Unproven (worded as questions or flagged)
- **Jynxzi's bike crash**: the impact on the pickup is seen in the full clip (frames 14-15 of 230429); the pre-crash frame at 14.6 still shows the road. Shot 1 starts at 14.10 so the hit lands ~0.7 s in. Check it on the first render.
- **"Spins his pickup out"** (Lacy): the car slides and faces the camera in frames 2-6 s. No input is shown; the narration does not say why.
- **xQc and the box truck**: he drives it (HUD turn arrows, "Return to the coffee shop"). "Cops were everywhere" is NOT used (it is Lucia in-game line); xQc pop uses src 21.9-24.45 "It's a big truck, huh?" (his own). The truck is not shown crashing, so the narration only says he drives it.
- **Jynxzi in the cab (shot 10)** is a cutscene: his character is a passenger. The narration only uses his spoken excuse.
- **Clix's flight**: the pickup is airborne at 17.0-19.3 near a broken span. Why (jump, glitch, explosion) is not shown. The narration only says it "goes flying".
- **recrent "gets stuck"**: the pickup is tilted on rocks after the slide. Not proven that this is the end of the mission. The "$1,500 on me" line is not used.
- **Peanut "drives into the river"**: the car runs off the road across grass into the water on the same clip; the cause (his steering) is not stated in the narration. "Still got it" is his own line (6-9 s).
- **Peanut's pop** "Almost saw God right there" is at the moment he is still on the road (10-12): the river comes at 13-16.
- **Kai Cenat could not be used** (no driving in any of his 10 clips). The brief said to lead with xQc, Kai and Lacy. See SOURCES.md.
- VO timings are an estimate until the Fish render exists.

## Memes (6; none overlap, each plays in full, ducked under voice; all from `media/sfx/memes/`)
| t (s) | file | length | on | why |
|---|---|---|---|---|
| 0.7 | `snd_vine_boom.mp3` | 1.25 | shot 1 | the bike hits the pickup |
| 10.45 | `snd_bruh.mp3` | 0.82 | shot 6 | right after Lacy says "my car is cooked" |
| 14.75 | `snd_sus_sound_effect.mp3` | 1.14 | shot 9 | xQc says "Cops were everywhere" |
| 19.75 | `snd_aughhh_tiktok.mp3` | 1.84 | shot 11 | the "stick drift" excuse |
| 28.85 | `snd_gta_cheat_activated_sound.mp3` | 2.14 | shot 16 | Clix's pickup is airborne (GTA cheat joke) |
| 44.40 | `snd_sewey.mp3` | 1.49 | shot 25 | the car sinks, the payoff beat |
Checks: starts at 0.7, 10.45, 14.75, 19.75, 28.85 are five inside 0.7-30.7 (limit 5 in any 30 s); each ends before the next starts; the last ends 45.89 < 50.1. No streamer-specific meme (Kai's is not used). The GTA Wasted sounds are not used: no character dies in the footage.

## Beat SFX (4; none within 0.5 s of another SFX or meme onset)
| onset (s) | file | anchor |
|---|---|---|
| 8.88 | `whoosh_short.wav` (peak 0.22 s) | the Lacy pop join at 9.1 |
| 24.52 | `whoosh_short.wav` | the Jynxzi text+drive pop join at 24.74 |
| 30.22 | `whoosh_short.wav` | the Clix pop join at 30.44 |
| 42.54 | `impact_hit.wav` (peak 0.0 s) | Peanut's car hits the water |
No riser: the only place it could end on is inside narration or a pop, which SOUND-RULES forbids.
