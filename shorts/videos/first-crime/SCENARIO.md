# First crime, instant fail: scenario (for approval, no voice generated)

Story option 3 in STORY-OPTIONS.md. 1080x1920, **48.2 s, 24 shots** (1.4-2.9 s each).
Mix: gameplay 30.5 s (63 %), streamer pops 9.3 s (5 pops, 19 %), trailer 8.4 s (17 %, 4 shots), 6 memes, 4 beat SFX.
Narrator: Fish voice, same settings as Planes v2. Script: `FISH-SCRIPT.txt` (12 lines, hook in line 1, closing question in line 12). VO times assume 2.8 words/s; the narration is silent during every pop and no line runs into a pop (checked). **Not rendered, no paid voice.**
Contact sheet (the cropped result, one tile per shot, pops show the facecam inset): `sixstars-shorts/out/preview/first-crime-scenario.png`.
Sources, rejected candidates and gaps: `SOURCES.md`.

Gameplay files: `autoclipper/<clips_ready|clips_crowd>/<streamer>/<date>/<file>_horizontal.mp4` (read-only). Trailers and the longplay are in `sixstars-shorts/media/`. All times are seconds in the source file.

**Layout** (same contract as Drivers/Planes)
- `crop`: full-screen 9:16 cut from the 16:9 frame, 0.316 of the frame width; left edge = clamp(focus x - 0.158, 0, 0.684).
- `desktop`: the whole 16:9 frame centred on a blurred copy of itself. Used for the 4 trailer shots and for shot 16 (the real WASTED card, so the title is not cropped).
- Pops: the streamer's own audio, facecam cut from the **horizontal** file as an inset at the top over the cropped gameplay from the same file and time. Never use `_vertical` files for insets.
- Facecam boxes (fractions of the 16:9 frame): Speed 0.02-0.205 x 0.44-0.64; Asmon (Z190) 0-0.256 x 0-0.455; Asmon (Z180) 0-0.235 x 0.62-0.95; Lacy 0-0.185 x 0-0.20; xQc 0-0.185 x 0-0.20.

| # | time | narration line (exact words) | on screen (file, in-out s, what is visible) | pop | SFX / meme | caption header | layout | focus x |
|---|---|---|---|---|---|---|---|---|
| 1 **TRAILER** | 0.00-1.60 | [shocked, fast] Your first robbery in GTA 6 ends in an arrest. _(L1, VO 0.00-3.57)_ | `QdBZY2fkU-0.mp4 (Trailer 1)` 68.75-70.35: Lucia, bandana, convenience-store hold-up (SHOTLOG T1 #44) | - | - | FIRST CRIME | desktop | - |
| 2 | 1.60-3.20 | - | `shirrako_BGUTv2K_SWs (longplay)` 920.80-922.40: hooded Lucia held by cops, "Suspect's in custody" | - | **meme `snd_vine_boom` (1.25 s) at 1.70** | FIRST CRIME | crop | 0.50 |
| 3 **TRAILER** | 3.20-5.65 | [curious] So how do the streamers handle it? _(L2, VO 3.20-5.70)_ | `QdBZY2fkU-0.mp4 (Trailer 1)` 47.50-49.95: security-cam flash then bodycam gunman, POLICE vest (#28-29) | - | - | FIRST CRIME | desktop | - |
| 4 | 5.65-7.45 | [teasing, fast] Speed masks up and asks chat if he can rob it. _(L3, VO 5.65-9.58)_ | `ishowspeed_005620_x2.6` 33.50-35.30: Lucia in bandana outside a garage, gun low | - | - | SPEED | crop | 0.34 |
| 5 | 7.45-10.05 | - | `ishowspeed_005620_x2.6` 29.80-32.40: same spot, still masked, chat says "don't rob it" | - | sfx `whoosh_short` at 9.83 | SPEED | crop | 0.33 |
| 6 | 10.05-11.48 | - | `ishowspeed_005620_x2.6` 28.12-29.55: Speed: "Can I rob it or no?" | **Speed**: "Can I rob it or no?" | - | SPEED | crop | 0.50 |
| 7 | 11.48-13.68 | [storytelling] Asmon finds a shop that's closed for a robbery. _(L4, VO 11.48-14.69)_ | `zackrawrr_190010_x1.4` 20.00-22.20: Asmon walks up to Ammu-Nation doors | - | - | ASMON | crop | 0.47 |
| 8 | 13.68-15.78 | - | `zackrawrr_190010_x1.4` 24.00-26.10: at the door; "closed to a robbery" 25.3-27.1 | - | **meme `snd_sus_sound_effect` (1.14 s) at 13.88** | ASMON | crop | 0.50 |
| 9 | 15.78-17.03 | - | `zackrawrr_190010_x1.4` 28.30-29.55: Asmon: "Wait, what?" | **Asmon**: "Wait, what?" | - | ASMON | crop | 0.45 |
| 10 | 17.03-18.93 | [amused] So he holds up a cashier, and someone jumps him. _(L5, VO 17.03-20.60)_ | `zackrawrr_180841_x2.3` 6.00-7.90: Lucia at the CASH HERE counter, cashier hands up | - | **meme `snd_record_scratch` (0.65 s) at 17.08** | ASMON | crop | 0.45 |
| 11 | 18.93-21.03 | - | `zackrawrr_180841_x2.3` 17.80-19.90: customer grabs Lucia, gun on the floor | - | **meme `snd_bruh` (0.82 s) at 19.13** | ASMON | crop | 0.55 |
| 12 | 21.03-22.63 | [teasing, fast] Lacy grabs the bag and runs from the cops. _(L6, VO 21.03-24.24)_ | `lacy_111339_x0.0` 11.40-13.00: two cops at the door (cutscene) | - | - | LACY | crop | 0.45 |
| 13 | 22.63-24.23 | - | `lacy_111339_x0.0` 20.00-21.60: Lucia runs along the roof with the bag | - | - | LACY | crop | 0.50 |
| 14 | 24.23-26.73 | [deadpan] He can't shake them. _(L7, VO 24.23-25.66)_ | `lacy_111339_x0.0` 31.00-33.50: running, HUD "Lose the cops" | - | sfx `whoosh_short` at 26.51 | LACY | crop | 0.50 |
| 15 | 26.73-28.83 | - | `lacy_111339_x0.0` 41.75-43.85: Lacy: "do I lose the cops on foot, son?" | **Lacy**: "...do I lose the cops on foot, son?" | - | LACY | crop | 0.42 |
| 16 | 28.83-31.33 | [building] One playthrough ends on a wasted screen. _(L8, VO 28.83-31.33)_ | `shirrako_BGUTv2K_SWs (longplay)` 855.00-857.50: crash, then the real WASTED card (856.3+) | - | sfx `impact_hit` at 29.13; **meme `snd_gta_2_wasted` (2.10 s) at 30.13** | WASTED | desktop | - |
| 17 | 31.33-34.23 | [hushed] Asmon gets arrested too, and he's weirdly calm. _(L9, VO 31.33-34.19)_ | `zackrawrr_180841_x2.3` 40.00-42.90: cop car and an officer outside the store | - | - | ASMON | crop | 0.55 |
| 18 | 34.23-36.63 | - | `zackrawrr_180841_x2.3` 43.55-45.95: Asmon: "I know I got arrested anyway" | **Asmon**: "I know I got arrested anyway. Does it matter?" | - | ASMON | crop | 0.55 |
| 19 | 36.63-38.23 | [storytelling] xQc skips the robbery and just drives a box truck through town. _(L10, VO 36.63-39.49)_ | `xqc_111750_x1.1` 8.00-9.60: box truck leaves the alley, HUD route arrow | - | **meme `snd_aughhh_tiktok` (1.84 s) at 36.73** | XQC | crop | 0.60 |
| 20 | 38.23-39.63 | - | `xqc_111750_x1.1` 12.20-13.60: truck turns a corner, low sun | - | - | XQC | crop | 0.50 |
| 21 | 39.63-41.73 | [amused] Says it's a little janky. _(L11, VO 39.63-41.42)_ | `xqc_111750_x1.1` 16.00-18.10: truck under the overpass | - | sfx `whoosh_short` at 41.51 | XQC | crop | 0.50 |
| 22 | 41.73-43.88 | - | `xqc_111750_x1.1` 20.10-22.25: xQc: "a little bit janky, but..." | **xQc**: "That's a little bit janky, but..." | - | XQC | crop | 0.35 |
| 23 **TRAILER** | 43.88-45.88 | [direct, friendly] If your first robbery goes wrong, do you run or give up? _(L12, VO 43.88-48.17)_ | `VQRLujxTm3c.mp4 (Trailer 2)` 45.50-47.50: POV car, police car, running person (#15) | - | - | RUN OR GIVE UP? | desktop | - |
| 24 **TRAILER** | 45.88-48.23 | - | `QdBZY2fkU-0.mp4 (Trailer 1)` 63.35-65.70: news: COPS ARREST MAN; man in jumpsuit (#39-40) | - | - | RUN OR GIVE UP? | desktop | - |

(Planned timeline, 48.23 s. Pop starts come from whisper word timestamps, accurate to about 0.1 s.)

## Must-fix in the edit (seen in the sheet frames)
1. **Burned captions on the `_horizontal` files.** The Lacy pop (15) has "THE F*CK DO I" burned in until about 41.7 s of the source and the pop starts at 41.75. Cover the bottom band on every gameplay and pop shot and use our own captions.
2. **Shots 2 and 16 (Shirrako longplay):** mask the SHIRRAKO watermark and any in-game subtitle line (the watermark is visible bottom-right in the WASTED frame).
3. Shot 12 (Lacy): the first window (12.0-13.6) showed Lucia's face, not the cops. It was moved to 11.4-13.0 and the sheet now shows a cop at the door.
4. Pop 15 (Lacy): the facecam inset is small in the sheet. Enlarge it a little if it reads weak.
5. Pop 22 (xQc): his facecam has chat text under it. Crop the inset to the face only.

## Unproven (worded safely or flagged)
- **"Ends in an arrest"**: the footage shows the hold-up (Trailer 1 #44), then Lucia held by cops with "Suspect's in custody" (Shirrako, ~923 s). Handcuffs are **not** visible, so the script says arrest, never handcuffed.
- **xQc "gets away"**: rests on a tiny burned interview caption. The script says only that he drives a box truck through town (shown).
- **Asmon's shop**: the sign is not fully legible. The narration says "closed for a robbery", which is the game text shown 25.3-27.1 in that source window, not a named shop.
- **"Someone jumps him"** (shot 11): a customer grapples Lucia and the gun is on the floor. His role is not stated, so the script does not call him a hero or a clerk.
- **Lacy and the cops**: the HUD shows "Lose the cops" and a cutscene shows two cops at the door. The script says he runs from the cops, not that they chase him on screen.
- **"One playthrough ends on a wasted screen"**: the WASTED card is from the Shirrako longplay, not a streamer.
- **Time claim dropped**: "about three minutes" from hold-up to custody is unconfirmed (there is a retry in the longplay).
- VO times are estimates; re-time after the voice exists. Check pop 18 ("Does it matter?", ends 45.95) does not cut mid-word.

## Memes (6, none overlapping, ducked under voice)
| meme | length | onset | where |
|---|---|---|---|
| `snd_vine_boom` | 1.25 s | 1.70 | shot 2 |
| `snd_sus_sound_effect` | 1.14 s | 13.88 | shot 8 |
| `snd_record_scratch` | 0.65 s | 17.08 | after pop 9 |
| `snd_bruh` | 0.82 s | 19.13 | shot 11 |
| `snd_gta_2_wasted` | 2.10 s | 30.13 | shot 16 |
| `snd_aughhh_tiktok` | 1.84 s | 36.73 | after pop 18 |

At most 5 memes start in any 30 s window (checked). `snd_gta_v_busted` (7.84 s) was not used: it does not fit without overlapping. `snd_gta_2_wasted` is Rockstar audio (Content ID risk accepted in SOUND-RULES.md); the claim-free fallback is `wasted_hit.wav`.

## Beat SFX (4)
| sfx | time | where |
|---|---|---|
| `whoosh_short` | 9.83 | peak on the pop join |
| `whoosh_short` | 26.51 | peak on the pop join |
| `whoosh_short` | 41.51 | peak on the pop join |
| `impact_hit` | 29.13 | the crash at the start of the WASTED shot (source ~855.3) |

No SFX within 0.5 s of another onset (checked). No riser.
