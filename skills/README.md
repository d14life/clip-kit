# Skills: machine-specific notes

Copy each folder to `~/.claude/skills/`. Logic is unchanged from the original; these are the spots that assume the original author's machine.

| Skill | Note |
|---|---|
| virality-predictor | Portable. Example commands use `~/scratch/...` as a work dir. |
| agent-reach | Portable (Chinese-language skill; needs the `agent-reach` CLI installed separately). |
| watch-video | Needs a whisper Python env: set env `WHISPER_PY` to its python (the original path was removed). Needs yt-dlp + ffmpeg. |
| director | Portable. Refers to `~/scratch/2026-11-15/director/` helper scripts that are not included. |
| motion-reel | Written around the author's own 24FRAME project: repo `YOUR_GITHUB_USER/24frame-reel` is a placeholder (not provided). `references/scripts/atlas_gen.py` needs env `ATLAS_API_KEY` (paid Atlas Cloud) and has Mac-style CA path `/etc/ssl/cert.pem`. Mentions Fish Audio / Higgsfield accounts you must own. Use as a reference, not a turnkey tool. |
| remotion | Portable. |
| find-skills | Portable (`list-skills.sh` needs bash + python3). |
| trend-hunt | Portable. Needs Python with `yt-dlp` and `pytrends`; X/TikTok/Instagram steps need the Claude in Chrome extension. Work dir `~/scratch/<date>/trend-hunt/`. |
