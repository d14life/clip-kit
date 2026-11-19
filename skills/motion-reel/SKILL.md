---
name: motion-reel
description: End-to-end production playbook for a short 9:16 motion-graphics promo reel with NO characters (kinetic type + 3D objects + UI screens) built with Remotion (edit, type, sound) + Blender via MCP (3D shots) + cheap generated stills, AI video only where it earns it. Use when Damir says "make a motion reel", "motion ad", "motion graphics reel", "3D type reel", "reel like 24FRAME", "Blender + Remotion promo", or pastes a motion-video brief (ТЗ) for a client with text, numbers and objects but no mascot. Not for mascot/character cartoons or AI-keyframe films (use cartoon-ad-film). For only a shot list, beat grid or cut review, use director (this skill calls it). Covers pipeline, review loop with Damir, his hard rules, cost/time traps and a first-hour checklist.
---

# Motion reel (9:16, Remotion + Blender + generated stills)

Distilled from the 24FRAME reel (2026-11-15 → 11-18, cuts v1 → v16f, 32 context compactions).
Diary and numbers: `~/video-vault/Motion reel - 24FRAME/`. Other skills: see **Skills to chain** below
(use them, don't copy them). Real snippets: `references/`.

## Skills to chain
Counted from the 24FRAME transcripts (Skill calls / sessions, de-duplicated; tally `~/scratch/2026-11-18/skill-usage.txt`).
Most of the work ran outside skills: Blender via `bl.py` / CLI (1,692 Bash calls) + Blender MCP, ffmpeg (1,180),
`remotion render` (438), Playwright capture (79), whisper (49).

| Stage | Skill | When to use | What it gave us on 24FRAME |
|---|---|---|---|
| Align | `grill-me` (recommended, not used) | Day one: length with voice, AI video yes/no, budget, open shot splits | Named for the shot-2 split but never run; the 20-22 s brief became 42 s |
| Shots | `director` (3 calls / 2 sessions) | Shot list, beat grid, a planned transition on every seam, cut review | `docs/shotlist.md`; the "hand-off on every seam" fix for random hard cuts |
| Refs | `higgsfield-generate` (1 call + 21 MCP + 20 CLI) | 3x3 storyboard grids and chroma-green hard objects | Storyboard grids (gpt_image, ~0.25 credits each) he picked cells from |
| Refs | `watch-video` (recommended, not used) | When he sends a reference reel to copy | Not needed on 24FRAME; worked on mult-ad |
| Refs | `refero-design` (recommended, not used) | Real UI references for in-reel app/site screens | Not used; the screens came from the brief |
| UI screens | `high-end-visual-design` + `emil-design-eng` (3 calls, 1 agent) | Building a Remotion UI screen shot | Scene2Build clinic-site screen v1 → v2 |
| 3D | `blender-toolkit` (recommended, not used) | First Blender setup / scripting help | Copied into the project, never invoked; `references/blender.md` + `bl.py` did the job |
| 3D moves | `slow-zoom`, `dolly-rotate`, `crane-shot`, `turntable`, `perfect-loop`, `dynamic-full-loop` (recommended, not used) | A shot needs that exact camera move, or the loop comp | Never invoked; moves were hand-keyed. Start from these next time |
| 3D look | `product-polish`, `polyhaven-studio-setup` (recommended, not used) | One hero object needs studio light / materials | Not used. Keep world colour = bg (section 1.4), so no HDRI background |
| Edit | `remotion`: **skip** | - | Tried twice; it is a Stitch-walkthrough skill. Use `references/remotion-edit.md`. The researched upgrade `remotion-dev/skills` is not installed (needs his yes) |
| Voice / SFX | `anthropic-skills:chrome-browser` (4 calls / 2 sessions) | Before Fish Audio / Pixabay in his signed-in Chrome | All voice takes |
| Parallel | `superpowers:dispatching-parallel-agents` (1 call) | One agent per shot, or the second PC | Shot work split across agents and machines |
| Review page | `artifact-capabilities` (1 call) | A review board that saves his picks | The morning review board |
| Check pages | `drive-demo` (recommended, not used) | Before sending the anim-picker or demo link | Pages were clicked by hand (~730 browser calls) |
| Check done | `superpowers:verification-before-completion` (recommended, not used) | Before "rendered" / "done" | The phantom "final-v6 rendered" claim (section 4) is what it stops |
| Publish | `virality-predictor` (recommended, not used here) | On the hook and the cut before publish | Not run on 24FRAME; on mult-ad it scored the plan 56/100 and drove the rewrite |

**Source code.** The local `~/24frame-reel` folder is deleted. Code: `gh repo clone YOUR_GITHUB_USER/24frame-reel -- -b hooks`
(branch `hooks` is the latest; `main` is older; private). Repo paths used below: `src/Final.tsx`, `src/Root.tsx`,
`scripts/grade_all.py`, `scripts/bl.py`, `docs/review/anim-picker/` (`index.html` + `capture.py`), `docs/BLENDER_FRIEND.md`,
`docs/brief.md`, `docs/review/REQUESTS.md`. Rendered clips are gitignored: `gh release download assets-final -R YOUR_GITHUB_USER/24frame-reel`.
Copies that work without the repo: `references/scripts/` (`grade_all.py`, `bl.py`, `splice2.sh`, `anim-picker-index.html`,
`anim-picker-capture.py`, `atlas_gen.py`). Final cut: `~/ARCHIVE/24frame-reel-final/final-v16f.mp4` (+ `-loop`, music wav).

## 0. The shape that worked
- **Remotion = the edit.** One `src/Final.tsx` assembles pre-rendered clips, type layers, voice, music, SFX.
- **Blender (MCP) = every 3D shot.** House style locked from the first approved shot.
- **Generated stills (≈$0.02 each)** = storyboard refs, screen content, "hard objects" on chroma green.
- **AI video (Seedance i2v)** = only for details too costly to build; never trusted with text.
- **Type** = real type, never AI letters. The final type lines came from a web "anim-picker" page
  rendered to transparent PNG sequences with Playwright, because Damir said the picker "was perfect".
- **Review** = one gallery/demo link + numbered frames, never a wall of chat images.

## 1. Pipeline, in order

### 1.1 Lock the brief (before any pixel)
1. Save the client brief verbatim to `docs/brief.md` ("source of truth, wording never changes").
2. Under it keep a **Decisions log**: one dated line per pick, in his words, e.g.
   `- 2026-11-17 (Damir): line exits = whole line fades, replaces the gravity fall`.
   Append, never overwrite. Check it before every render (rule 3.4).
3. Pull the real numbers out of the brief. Numbers on AI boards (+167 %, ×2.4) are invented: never use them.
4. Spec block in the project `CLAUDE.md`: 1080×1920, 30 fps, BPM (120 BPM → 1 beat = 15 f), bg colour,
   ONE accent, ONE font, text-safe zone (24FRAME: x 120–960, y 260–1250), clear of the Instagram notch.
5. Ask about length on day one: the brief said 20–22 s; the voiced final ran 42 s (1260 f).
   The voice lines set the length.

### 1.2 References and shot list
1. Generate 3×3 storyboard grids (24FRAME: Higgsfield gpt_image via `higgsfield-generate`, ~0.25 credits/image; or Atlas
   `google/nano-banana-2.1-developer/text-to-image`, ~$0.026, via `references/scripts/atlas_gen.py`), crop the cells to `docs/refs/`, publish ONE page
   with every cell numbered. Damir picks cells. Numbers are permanent IDs: never renumber.
2. Run the `director` skill → `docs/shotlist.md` (ID, time, beat, size, content, camera, text, sound,
   and the transition into the next shot).
3. Build the cells he picked, in his order. Don't re-plan them ("You should go as they were planned in AI grid", 2026-11-15).
4. For each picked cell write a **detail checklist** (labels, numerals, icons, reflections, buttons) and
   tick it during QA. Damir: "It's about details… Why are you forgetting those little things?" (2026-11-15).

### 1.3 Skeleton cut first
In hour one, build a rough Remotion cut on the beat grid with placeholders, so timing shows early.
Label it a draft. Never send a "real" preview with stand-in text in it: he called one "trash" (2026-11-17).

### 1.4 Blender shots (one Blender per machine, ever)
1. Shot 1 sets the house style: EEVEE, view transform Standard, world colour = the bg colour
   (#F6F6F3 → linear 0.92158, 0.92158, 0.89627), accent material with roughness ~0.28.
   Never overwrite that `.blend`.
2. For each shot, render **START / impact-MID / END keyframes**, scale them to ≤800 px, inspect each
   yourself, name the defects, push, and **wait for his OK**.
3. Seams: shot N's END must equal shot N+1's START. Report the pixel diff (`references/qa-publish.md`).
4. After his OK: PNG sequence → `ffmpeg -framerate 30 -i out/bNN/%04d.png -c:v libx264 -crf 16 -pix_fmt yuv420p -movflags +faststart public/final/<clip>.mp4`.
5. Drive Blender through the MCP, or `python3 references/scripts/bl.py file.py` (a raw socket to the running
   Blender on localhost:9876, so no second Blender is needed). See `references/blender.md`.
6. Hard objects (phone, stopwatch, keycap): generate each one alone on chroma green, key it to a PNG,
   and place it on planes. Blender keeps the layout, light and exact type.

### 1.5 AI video (only if he allows it for this job: ask)
- Seedance 2.0 fast i2v on Atlas Cloud (`bytedance/seedance-2.0-fast/image-to-video`, base
  `https://api.atlascloud.ai/api/v1/model/`, `generateVideo` then poll `prediction/<id>`), from **approved** keyframes.
  Client: `references/scripts/atlas_gen.py` (`call`, `upload`, `balance`, `run`; needs a non-default User-Agent or
  Atlas 403s). Its `_key()` reads the key at runtime (this kit: env `ATLAS_API_KEY`); never print it. One submit per clip, **never retried** (a resend is a second charge). Read the
  balance before and after (free `/public/v1/balance`). Other sessions share the key, so a balance
  drop is not proof of one job's price.
- The real price on 24FRAME was ~$0.63 per clip (4 s, 720p/24 fps, upscaled), not the $0.027/s estimate.
- Writing in AI clips is always bad, so cover it with real type. AI clips come out grey/"clay", so grade them (1.6).
- Keep the raw AI file untouched and edit copies. Damir later wanted "the original ai… this one has been edited so many times".

### 1.6 One common grade
Every clip becomes `<clip>-g.mp4` with one shared white: `python3 references/scripts/grade_all.py [clip ...]`
(edit its bg/accent constants for a new palette): a per-channel
gain so the top and bottom rows hit the bg colour, applied to neutral pixels only (accent untouched),
with a soft highlight roll-off (nothing clips). Damir: "make sure all things are the same gradient white" (2026-11-16).

### 1.7 Type
- Real font, real type, inside the safe zone and below the notch.
- Build an **anim-picker page**: each line × several entries (slam / swing left / swing right / spin),
  colour options and exits. He clicks a pick per line, and the pick goes into the Decisions log.
- Template: `references/scripts/anim-picker-index.html`. Capture that same page to transparent 1080×1920 PNG
  sequences (`references/scripts/anim-picker-capture.py`, Playwright, bundled Chromium only) and use
  one layer per line in `Final.tsx`. What he approved is exactly what ships.
- Voiced lines: each word appears on the frame where it is spoken (word start times from `whisper-cli`
  (whisper.cpp) on the chosen take, refined on the 10 ms envelope); check every word against its frame in QA.

### 1.8 Voice, music, SFX
- Voice: Fish Audio TTS (fish.audio web app) in **his** Chrome (the built-in browser pane is not signed in; the API
  key on disk returned 401 on 2026-11-17). The character counter is the cost: a plain line ~62, tags add 6–13. Send the takes
  as raw audio files in chat, labelled, and he picks by ear. One generation cost ~61–62 credits (later ~120–134 for 2 variants).
- Music: flat under the voice ("dont make music quieter when they speak", 2026-11-17), but watch the
  overall level ("Musics a bit too loud", same day). Used: ≈ −21 LUFS, true peak ≤ −1 dBFS.
- SFX: free ready-made sounds (Pixabay) first. A Fish SFX cost 5,000 credits. No synthetic code-made
  SFX: "remove any ai sound u made in code they sound bad" (2026-11-16).

### 1.9 Edit (`src/Final.tsx`)
- `SCENE_STARTS` on the beat grid, and a `CLIPS` table `{f, s, r, a, b, n, t: 'cut'|'zoom'|'whip', sc}`
  (file, src start frame, playback rate, global in/out, src length, transition, scene).
  See `references/remotion-edit.md` (full file: repo `src/Final.tsx`).
- Comps: `Final` (music only), `FinalVO` (voice), `FinalLoop` (the end flows back into frame 0).
- **The loop version is a deliverable, not an extra.** He asked "where is the endless loop" at least 4 times.

### 1.10 Render, QA, publish
1. Render in muted chunks (`--frames=a-b`, 180 f each) plus one audio render, then concat with `-c copy`.
   A one-piece render died with ENOSPC. For a small fix, splice the frame range into the last good
   MP4 instead of re-rendering everything (`references/scripts/splice2.sh`, usage in `references/qa-publish.md`).
2. Check, with output pasted: `df -h` first; ffprobe frames / fps / 1080×1920 / aac; loudness; a
   contact sheet; motion strips (every 2nd–3rd frame) around every move; seam diffs; each voiced word
   against its frame.
3. Publish to the public `<name>-demo` repo (GitHub Pages: `index.html` + mp4). Keep the previous
   version as `<name>-vN.mp4`. curl every file: 200, and content-length = local size. Links into
   private repos 404 for him.
4. Run `open -a "QuickTime Player" <file>.mp4` on his Mac for every video you send.

## 2. Review loop with Damir
- **One page with the current state, in play order.** For each shot: a numbered thumbnail, the
  machine that owns it, and its status (planned / keyframes / approved / rendered / in cut).
  His most frequent complaint was confusion: "in fucking html page not here", "Just give me one clean thing".
- Numbered frames labelled `shot + START/MID/END`, ≤800 px. Inspect them first and list the defects.
- Every visual question comes with a picture of each option (current + A/B/C, same camera).
- `docs/review/REQUESTS.md`: his requests in his words, newest first, marked OPEN / IN vN / DONE + proof.
  Agents tick a row only with evidence. Re-read it before every cut.
- Before showing a cut, say in 3 lines what changed since the last version he saw.
- What he checks: flow (no random switches), reading time per line, whole transitions, detail density,
  the same white everywhere, letters 3D but readable, words landing on the voice, the loop seam.
- When he is away: decide, keep the queue moving, leave FYI pictures. Still no paid call without his yes.

## 3. Hard rules (his words, with dates)
1. Frames before video, and inspect them yourself first (2026-08-06; held on this job).
2. "we need transition never cut them" (2026-11-17). To shorten a shot, cut only its static hold.
3. "remember my choices we made bro" (2026-11-17): a new "go" on one aspect never resets another pick.
4. Before every render, a test still per shot, checked against the Decisions log (2026-11-17).
5. 3D-first: show off that it is Blender. Flat motion graphics read as cheap, "After Effects level" (2026-11-15).
6. Type: deep extrusion with dark sides "looks bent… not premium enough" (2026-11-15); CSS-shadow
   type "look like Instagram" (2026-11-16); "too dark and thick" (2026-11-17). What shipped:
   half-depth, dark-grey ink, lighter sides, straight to the camera.
7. "Should not look like it's been pasted over the top. It should be like a part of the scene" (2026-11-16).
8. AI never draws letters or digits; real type only (2026-11-15).
9. Never invent numbers; only the brief's.
10. One Blender per machine.
11. Money: price per unit + budget in every paid brief; read the price on the page before the first
    click; stop if one unit costs more than what is left (2026-11-17).
12. "like before we had nice motion keep to the full dont cut please i decide" (2026-11-16): never
    trim a shot he liked on your own.
13. Nothing frozen on holds. The end card needed a "slight camera move" plus a drifting «О»; a static
    zoom "looks very AI" (2026-11-17).
14. Physics must read: popped pieces "should stay and then by gravity just go down", never shrink or
    vanish (2026-11-17), and keep flying at the same speed (2026-11-18).
15. Hold time scales with the amount of text; shots without text can stay fast (2026-11-16).

## 4. Top mistakes → fixes
| Mistake (24FRAME) | Fix |
|---|---|
| Overnight shots finished, the wake-up check never fired: 4 h lost, the morning cut lacked them | Chain render → assemble → publish in one background job; check `ls`/ffprobe before saying done |
| Picks lost when a new look was applied; typewriter lines rendered on both Macs | Decisions log + a test still per shot against it before every render |
| Trim 37.5 → 34 s on the beat grid clipped transitions ("u droped so much") | Trim only the holds of the shots he named; diff seams against the last approved cut |
| Disk at 100 % (85 MiB free) → ENOSPC; an agent claimed "final-v6 rendered" with no file (exit code hidden by a trailing `tail`) | `df -h` before renders; `set -o pipefail`; never accept "done" without `ls` + ffprobe |
| Fish SFX: one sound ~5,100 credits against a 3,000 cap | Price in the brief; work out how many units fit; stop before the click |
| Seedance: $3.13 for 5 clips against a "<$1" estimate | Quote from the first real clip; read the balance before and after |
| Re-timed the current wall when he meant an earlier render | Ask "which version" and show a frame of each |
| Draft of hard cuts between unrelated objects: "why switch of them shot are so random" | Plan a hand-off (zoom-through, match cut, whip) for every seam in the shot list |
| Line-exit style flip-flopped (fall → fade); each switch was a re-render | Show both options side by side on the picker before rendering |
| Second PC could not push to the demo repo (403, pull-only) | Check write access on every repo for every machine in the first hour |

## 5. Time and cost sinks
- **Context:** 32 compactions over two chats. Keep a STATE file and REQUESTS.md, use one agent per
  shot, and start a fresh chat past ~250k.
- **Idle agents:** render agents sent dozens of "waiting on its own background work" notices.
  Give each one a single job and a clear stop condition.
- **Two machines:** the second PC builds from repo `docs/BLENDER_FRIEND.md` (setup part copied in `references/blender.md`) (setup check, house style,
  shot list, report format), on its own branch, committing only its own paths. Big media goes in a
  GitHub release (`gh release download assets-final ...`), not in git. Damir relays prompts by hand:
  give him one paste-ready block and say plainly what each machine does.
- **Disk:** the repo reached 8.2 GB. Keep the current render plus one previous; Trash, never `rm`.
- **Tiny fixes:** splice frame ranges into the last MP4 instead of a full re-render.

## 6. First-hour checklist
- [ ] `git init` in `~/<client>-reel` (never /tmp) and push to a private repo; create the public `<client>-reel-demo` Pages repo now.
- [ ] Brief verbatim in `docs/brief.md` + an empty Decisions log; spec block in `CLAUDE.md`.
- [ ] Ask once: final length with voice? Voice or music-only? Is AI video allowed? Budget per service?
- [ ] Read the balances (Atlas, Fish, Higgsfield) and write the price per unit next to each.
- [ ] `df -h` (tens of GB free); `pgrep -x Blender` (one only); the Blender MCP `get_scene_info` answers.
- [ ] `npx create-video@latest` (blank), then `remotion`, `@remotion/cli`, `@remotion/transitions`, `@remotion/motion-blur` all on one pinned version (24FRAME: 4.0.543).
- [ ] Copy `references/scripts/atlas_gen.py` (Atlas client) and `grade_all.py` into the new repo `scripts/`.
- [ ] Storyboard grids → numbered refs page → he picks cells.
- [ ] `director` → shot list with a planned transition on every seam.
- [ ] Rough cut on the beat grid, shown as a draft.
- [ ] Shot 1 keyframes in Blender → his OK → that `.blend` becomes the house style.
- [ ] Review page + REQUESTS.md live; `FinalLoop` comp stubbed from day one.

## Score gate (added 2026-11-18, from scoring the finals)
Both finals scored badly on virality-predictor: cartoon 56/100, 24FRAME 49/100 on Reels. The process scored 5 and 4.6 out of 10. Both lost points the same way, so:
- **Length is locked in the brief and checked with ffprobe before every render.** Both films ran ~2x their brief (44.7 s vs 25-30 s; 42 s vs 22 s).
- **Make a timed animatic first, then score it** with virality-predictor before any paid clip or full render. Fix structure there; better visuals never raised the score.
- **Every final needs a text hook readable in frame 1, burned-in captions, and a 2 s CTA card.** Both had none, which cost Hook/CTA points.
- Run virality-predictor on the FINAL before handoff and record it in the vault Score.md. watch-video fails on local files, so use ffmpeg frames + whisper-cli instead.
