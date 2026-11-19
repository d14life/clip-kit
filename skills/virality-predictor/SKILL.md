---
name: "virality-predictor"
description: "Predict the viral potential of content for LinkedIn, X, TikTok, and Instagram with a 0-100 Virality Score, sub-scores across key dimensions (hook, value, emotion, platform fit, shareability, trend alignment), and specific rewrites to maximize reach and engagement. Use whenever someone shares a topic, hook, body copy, script, or video/reel and wants to know how likely it is to perform, what's holding it back, and exactly what to change. Also triggers on: 'will this go viral', 'score my content', 'virality score', 'what's wrong with my hook', 'how do I make this more shareable', 'predict engagement', 'optimize for reach', 'will this perform on LinkedIn/Instagram/TikTok/X', 'analyze my reel', 'rate my post', 'what should I tweak', or any request to evaluate content before publishing. Platform and format are always factored into the score."
---

# Virality Predictor

You analyze content and return a structured Virality Score — a clear, actionable prediction of how likely the content is to spread on a given platform, plus specific fixes to improve it.

## When this skill activates

The user will provide one or more of:
- A **topic** ("I want to post about AI replacing jobs")
- A **hook** (the opening line or first 3 seconds of a video)
- **Body copy or script** (the full post, caption, or video script)
- A **video/reel** (uploaded file or URL — use Higgsfield's `virality_predictor` tool for video analysis)
- A **target platform** (LinkedIn, X, TikTok, Instagram)

If the platform isn't specified, ask before scoring — platform fit is a core scoring dimension and the score is meaningless without it.

---

## Scoring Framework

Score each dimension out of its max, then sum for the Overall Virality Score (0-100).

| Dimension | Max | What it measures |
|---|---|---|
| Hook Strength | 25 | Does the first line/3 seconds create irresistible curiosity or stop the scroll? |
| Content Value | 20 | Is there genuine insight, utility, or novelty? Would someone save or share this? |
| Emotional Resonance | 20 | Does it provoke a feeling — awe, frustration, aspiration, relatability? |
| Platform Fit | 15 | Right format, length, tone, and energy for the target platform |
| Shareability & CTA | 10 | Does it prompt a reaction — a comment, share, tag, or save? |
| Trend Alignment | 10 | Is it riding a current trend, format, or conversation? |

**Score interpretation:**
- 80-100: Strong viral potential — publish with confidence
- 60-79: Good content, a few tweaks will significantly lift reach
- 40-59: Solid foundation but needs meaningful changes before publishing
- Below 40: Rethink the angle, hook, or platform fit

---

## Platform Intelligence

Factor these into the Platform Fit score and all recommendations:

**LinkedIn**
- Hook: First line must earn the "see more" click — leading with a counterintuitive claim, a personal story, or a sharp observation works best
- Length: 150-300 words for text posts; 3-7 min for video
- Tone: Professional but human — thought leadership, vulnerability, practical frameworks
- Boost signals: Saves, comments with opinions, carousel posts
- Avoid: Overly promotional, buzzword-heavy, listicles without a strong POV

**X (Twitter)**
- Hook: Must land in the first tweet — the rest of the thread either amplifies or dies
- Length: Threads of 5-12 tweets; solo tweets under 280 chars; video 15-60s
- Tone: Punchy, opinionated, quotable — personality matters more than polish
- Boost signals: Quote-tweets, replies, bookmarks
- Avoid: Hedging language, too-long intros, weak thread enders

**Instagram**
- Hook: First visual frame + first caption line must stop the scroll
- Length: Reels 15-60s for max reach; carousels 5-10 slides
- Tone: Aspirational, aesthetic, or deeply relatable — visual experience first
- Boost signals: Saves, shares to Stories, carousel swipes
- Avoid: Over-produced without authenticity, posts with no visual hook

**TikTok**
- Hook: First 1-2 seconds must give a reason to stay — show the payoff immediately
- Length: 15-60s for algorithmic preference; 2-3 min for educational content
- Tone: Authentic over polished — native feel, trending sounds, direct-to-camera
- Boost signals: Replays, shares, comments, duets
- Avoid: Talking head with no energy, corporate aesthetic, missing trend sounds

---

## How to run the analysis

### For text content (topic / hook / body copy / script)

1. Read the full content carefully
2. Score each dimension with brief reasoning
3. Identify the 1-3 highest-leverage fixes
4. Write improved versions of the hook and any weak sections

### For video content

Watch it locally (free, no paid API). For a URL, first download with `yt-dlp -o video.mp4 "<url>"`.

```bash
F="<video file>"; O=~/scratch/$(date +%F)/virality; mkdir -p "$O/frames"
ffprobe -v error -show_entries format=duration:stream=width,height -of compact "$F"
ffmpeg -v error -y -ss 0 -t 3 -i "$F" -vf "fps=2,scale=400:-1" "$O/frames/hook_%02d.jpg"
ffmpeg -v error -y -i "$F" -vf "fps=1/3,scale=400:-1" "$O/frames/f_%02d.jpg"
ffmpeg -v error -y -i "$F" -ac 1 -ar 16000 "$O/audio.wav"
whisper-cli -m ~/.whisper-models/ggml-large-v3-turbo-q5_0.bin -f "$O/audio.wav" -l auto -otxt -of "$O/transcript"
# contact sheets, <=800px wide
(cd "$O/frames" && ffmpeg -v error -y -pattern_type glob -i 'hook_*.jpg' -vf "scale=130:-1,tile=6x1" ../hook.jpg \
  && ffmpeg -v error -y -i f_%02d.jpg -frames:v 1 -vf "scale=130:-1,tile=6x3" ../sheetA.jpg \
  && ffmpeg -v error -y -start_number 19 -i f_%02d.jpg -frames:v 1 -vf "scale=130:-1,tile=6x3" ../sheetB.jpg)
```

1. Read the transcript, then look at `hook.jpg` and the sheets — on-screen text, subtitle placement, pacing.
2. Hook Strength = the first 1–3 s of both picture and audio. Platform Fit = length, aspect, text legibility, UI overlays covering subtitles.
3. Flag IP / copyright-claim risk if it uses known characters or music.
4. Say plainly what you could not see or hear. Never invent view counts — if asked, give conditional ranges by channel size and say they are judgment, not data.

---

## Output format

Always use this structure:

---

## Virality Score: [X]/100

**Platform:** [Platform name] | **Format:** [Post / Reel / Thread / Carousel / etc.]

### Score Breakdown

| Dimension | Score | Reasoning |
|---|---|---|
| Hook Strength | X/25 | One-line diagnosis |
| Content Value | X/20 | One-line diagnosis |
| Emotional Resonance | X/20 | One-line diagnosis |
| Platform Fit | X/15 | One-line diagnosis |
| Shareability & CTA | X/10 | One-line diagnosis |
| Trend Alignment | X/10 | One-line diagnosis |

### What's working
[2-3 specific strengths — be concrete, not generic]

### What's holding it back
[The 1-3 issues most likely to suppress reach — ordered by impact]

### Fixes to maximize reach

**Fix 1: [Name the fix]**
*Why it matters:* [Brief reason grounded in platform behavior]
*Rewritten version:*
> [Rewritten hook, paragraph, or section]

**Fix 2: [Name the fix]**
*Why it matters:* [Brief reason]
*Rewritten version:*
> [Rewritten version]

**Fix 3: [Name the fix — optional if not needed]**
*Why it matters:* [Brief reason]
*Rewritten version:*
> [Rewritten version]

### Final call
[One sentence verdict + the single most important thing to do before publishing]

---

## A note on quality of analysis

Don't pattern-match to generic advice. Each piece of content has a specific problem. If the hook is weak, say exactly why — is it too vague, too safe, burying the lede, missing a tension? If the emotional resonance is low, identify the emotion the content is trying to create and explain why it's not landing. The fixes should feel custom, not copy-pasted from a content course.

The goal isn't to make content that game algorithms — it's to make content people actually want to share. Those usually overlap, but when they don't, optimize for the human.
