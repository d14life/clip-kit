# Pro examples: measured breakdowns

Method (so you can repeat it): `yt-dlp -f 18` 360p download, then ffmpeg scene detection
(`select='gt(scene,T)'`, cuts closer than 0.4 s merged into one), T = 0.3 and 0.4.
Avg shot length = duration / (cuts + 1). Scratch scripts: `~/scratch/2026-11-15/director/cluster.py`, `beat.py`.

**Accuracy caveats (read before quoting a number):**
- Scene detection is threshold-dependent. I checked two films by eye at 5 frames/s
  (Definitely City 0-8 s, Manchester Calling 0-6 s). The detector undercounts soft cuts, dissolves
  and whip-pans by roughly 15-50%, so the true average is likely SHORTER than the tables.
- Whip-pans and white/blue flashes register as cuts; a few UI-motion changes register as extra cuts.
- Beat figures are audio-onset proximity, not true beat tracking. BPM estimates are unreliable
  (octave errors), so none are given as facts. "BPM" below is [unverified].
- Videos are public YouTube uploads. Frames/footage were NOT copied into the skill or any project.
  Download folder is scratch only and is deleted after 14 days.

## Table 1: sports / kit promos (16:9 uploads)

| Video | URL | Dur | Shots (T=0.3 / 0.4) | Avg shot (T=0.3 / 0.4) | Median (T=0.3 / 0.4) | First cut |
|---|---|---|---|---|---|---|
| PUMA x Man City, 24/25 Definitely City kit (Noel Gallagher) | youtube.com/watch?v=Zwa47D9vlRs | 30.5 s | 24 / 20 | 1.27 / 1.53 s | 1.00 / 1.29 s | 0.04 s |
| PUMA x Man City, 24/25 third kit "Never Not Moving" | youtube.com/watch?v=ebfFvjn6x-M | 30.2 s | 30 / 23 | 1.01 / 1.31 s | 0.72 / 1.00 s | 1.20 s |
| PUMA x Man City, 25/26 third kit "Rain or Shine" | youtube.com/watch?v=8HlMegKUKas | 32.0 s | 41 / 36 | 0.78 / 0.89 s | 0.68 / 0.76 s | 2.84 s |
| PUMA x Man City, 24/25 home kit "Manchester Calling" | youtube.com/watch?v=WnVsbyBaL_Y | 54.2 s | 44 / 35 | 1.23 / 1.55 s | 1.00 / 1.08 s | 0.48 s |
| Real Madrid x adidas 25/26 home jersey (behind the scenes; uploader not confirmed official) | youtube.com/watch?v=OXZ45SRe21Y | 60.0 s | 57 / 46 | 1.05 / 1.31 s | 0.80 / 0.84 s | 6.12 s |
| Nike Football "Winner Stays" (2014 film; third-party upload) | youtube.com/watch?v=WiHzyF3Bj7s | 252.1 s | 202 / 143 | 1.25 / 1.76 s | 0.96 / 1.16 s | 1.04 s |

**Measured range, 6 sports films: avg shot 0.78-1.76 s; median 0.68-1.29 s.** The 30 s kit
films (the Reels-length ones) sit at 0.78-1.53 s avg, 0.68-1.29 s median.

Not analysed: EA SPORTS FC 25 Official Reveal Trailer (youtube.com/watch?v=pBM2xyco_Kg, 126 s,
metadata verified) and PUMA x City 25/26 home kit (z3wP2EDnGF0, 140 s). Download returned HTTP 403
on every attempt, so shot count, hook and beats are [unverified]. A 7.1 s vertical City
25/26 home-kit clip (KTtwjd-a_l8) downloaded but showed zero detector cuts at T=0.3, so it is
single-shot or soft-cut; [unverified] which.

## Table 2: notable techniques seen (by eye, contact sheets)

| Video | Hook (0-2 s) | Notable techniques |
|---|---|---|
| Definitely City | 0.0-0.8 s dark studio, boom mic + lit sign, then shirt-on-player at 0.8 s. Face + product inside 1 s. | Motion-blur whip-pan at about 3.0 s into a new subject (cut at peak blur). Macro insert of brand badge/emblem as rhythm punctuation. Subtitle line burned in low-third. Scale change wide-to-tight on the same subject between cuts. |
| Manchester Calling | 0.0-0.4 s feet/ground action (cut on movement), white flash at 0.4 s, hand pasting poster by 0.6-1.0 s (hand motion = hook). | Flash frames as transitions. Long hold (about 2-3.5 s) on a talking subject between dense micro-cut runs, so a fast-slow-fast curve. Insert of kit number graphic. Ends on the product worn, centre frame. |
| Rain or Shine | First cut only at 2.84 s: slower opening that establishes mood, then cuts accelerate (detector shows cut clusters at 8-9 s and 24-28 s). | Cut density rises towards the end (fast-slow-fast with fast finish). Several clusters of sub-0.3 s cuts register as one beat. |
| Never Not Moving | First cut at 1.2 s. | Cut clusters at 6.4-7.6 s and 26.5-29.8 s = rapid-fire bursts at the start of the middle act and the finish. |
| Real Madrid home jersey (BTS) | 6.1 s before the first cut: slow reveal, not a Reels-style hook. | Longer BTS holds, then density rises from about 15 s. Treat as a counter-example for hook timing: 6 s of nothing would die on Reels. [unverified] retention. |
| Nike Winner Stays | First cut 1.04 s. Cut-clusters through the film, with long quiet beats (gaps up to about 11 s, e.g. 239.5 s to 250.6 s) before the end card. | Cutting on action (kick/tackle continuity). Dialogue-less montage chunks. Sound-led structure; shots cut within about 1 s in action runs. Quiet hold before the end title = pacing contrast. |

## Table 3: app / UI motion-graphics promo (the nearest analogue to our Remotion UI clips)

| Video | URL | Dur | Format | Structure (by eye, 1 frame/s sheet) |
|---|---|---|---|---|
| Cascade app promo (motion graphics) | youtube.com/watch?v=aoYwK-1rl5I | 36.6 s | 16:9 360p | About 8 scenes, avg about 4.6 s per scene. |

Beat sheet (timings read off the 1 fps contact sheet, +/- 1 s):

| Time | What |
|---|---|
| 0-4 s | Illustrated problem scene (office/props) |
| 4-11 s | Chess-knight metaphor walking a yellow maze |
| 11-13.5 s | Logo sting (scene-detect cluster at 11.5-13.5 s) |
| 13.5-16 s | Plan/Do/Measure cycle graphic, zoom-through tunnel transition |
| 16-23 s | UI hero: dashboard appears, org-tree nodes added in about 1 s steps (UI builds up, never just appears) |
| 23-25.5 s | People-network graphic |
| 25.5-30 s | Perspective road wipe into logo |
| 30-36.6 s | End card "Get started for free" + URL, held about 6.5 s unchanged |

Lessons: UI is introduced piece by piece; every scene change is a motion transition (zoom tunnel,
road wipe, morph), not a hard cut, so scene detection sees only 4 cuts; the CTA card holds long. The
long hold suits a 16:9 explainer. For 9:16 Reels, cut the end hold to 1.5-2.5 s [house rule, not measured].

## Beat-sync evidence (audio onset proximity, T=0.3 cuts)

Share of cuts within 100 ms of a detected audio onset, versus the share expected if cuts were random
(200 random trials):

| Video | Cuts | Within 100 ms of onset | Random expectation |
|---|---|---|---|
| Definitely City | 23 | 17 (74%) | 12.1 (53%) |
| Never Not Moving | 29 | 15 (52%) | 10.4 (36%) |
| Rain or Shine | 40 | 28 (70%) | 21.0 (53%) |
| Manchester Calling | 43 | 30 (70%) | 26.1 (61%) |
| Real Madrid BTS | 56 | 33 (59%) | 26.5 (47%) |

Reading: pros cut on audio hits more than chance (+10 to +20 points), but not every cut is on a hit.
Not every cut is on-beat; some cuts follow picture action instead. Crude method, treat as directional only.

## Written sources used (summaries read via search results, not full-page reads)

| Topic | Source | Takeaway used |
|---|---|---|
| Rule of Six | UT Austin RTF 318 wiki "Murch's Rule of Six"; nofilmschool.com/2016/11/6-rules-good-cutting-according-oscar-winning-editor-walter-murch | Emotion 51, story 23, rhythm 10, eye-trace 7, 2D plane 5, 3D space 4. Sacrifice from the bottom up. |
| Rule of Six critique | nofilmschool.com/2018/08/editing-eye-trace-mind-rule-six-incorrect | Eye-trace may matter more in fast online video than 7%. |
| J/L cuts | soundstripe.com "a video editors guide to j cuts and l cuts"; invideo.io blog "types of cuts" | J = next audio starts before picture. L = picture changes, previous audio continues. |
| Match cut / cut on action | Brown MML video guide "cuts transitions"; editshare.com | Cut mid-action to hide the cut. Match on action is a match cut. |
| Hook window | dev.to "Hook Engineering ... first 3 seconds" | Platform-data claim: stay/scroll decision about 1.4 s Reels, 1.7 s TikTok, 2.3 s Shorts (vendor blog, [unverified] primary data). |
| Hook counter-view | autoclip.dev "Why 3-Second Hooks Are Overrated" | The 3 s rule comes from an old "video watched" metric; a buildup hook won on completion. |
| Cut frequency | spliceapp.com short-form editing guide; clipflip.io 44,000-clip analysis | Heuristics only: cut every 2-4 s, or 1-2 s for high energy. Vendor claims, [unverified]. Our measured sports films cut faster (0.7-1.3 s medians). |
| Coverage / shot list | wrapbook.com/blog/shot-list; howtofilmschool.com dictionary "coverage"; doc.surf camera coverage | Wide + medium + close of each key subject. Inserts/cutaways listed as their own shots. |
| Whip-pan | nofilmschool.com/2017/09/5-steps-create-perfect-whip-pan-transition; premiumbeat.com whip-pan | Match direction and speed. Cut at the peak of the blur. |
| Speed ramps / beat sync | motionarray.com FCP speed ramping; kapwing.com speed ramp; spliceapp.com fast transitions | Ease the curve (S-curve), ramp-in-hold-ramp-out, put the peak of the ramp on the strongest beat. Vendor blogs. |
| "Handles", "shoot long cut tight", reading speed | no source retrieved | [unverified]. Marked as house rules in SKILL.md. |
