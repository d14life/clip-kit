# autoclipper — acceptance ledger

Written before the build; status filled in only from evidence gathered on this machine (2026-11-18).

| # | Condition for "done" | Evidence | Status |
|---|---|---|---|
| 1 | Offline channel is polled, not crashed on; recording starts when live | `riotgames` (offline) polled every 10 s, logged once; non-existent channel reported and dropped. The offline→live transition itself was not observed (no channel went live during testing); live start was tested by starting on live channels | pass (transition not observed) |
| 2 | Recording segments appear within ~20 s | first segment closed 11 s after start; ffprobe: h264 1080p60 + aac | pass |
| 3 | Chat read anonymously and logged | justinfan IRC over TLS, 148 msgs/20 s on kaicenat; `chat.jsonl` written; stats line shows 6–15 msg/s | pass |
| 4 | Detector: injected spikes found, flat/noisy chat quiet, sustained hype fires once, spam/bots ignored | `test_detector.py` 8/8 pass; onsets 1–2 s early (harmless, inside the 20 s pre-roll) | pass |
| 5 | Defaults set from real chat | 6 live GTA VI chats logged 7 min each; fixed 2.0x never fired on big chats (max 1.64x at 11.6 msg/s) → size-adaptive ratio; at default 9–17 clips/h on 5 of 6 chats | pass (7-min samples are short) |
| 6 | Every clip = configured length with video + audio | all clips ffprobe 30.000 s (live) / 30.0 s (VOD), 1080x1920 + 1920x1080 @60, aac | pass |
| 7 | Cut covers the right moment | live: chat "No hat / Keep the cap / L fits" ↔ transcript "baseball cap… no hat"; VOD #1: viewer clips "kai bank", "Kai robbing a store" ↔ transcript "Oh shit!", chat "3 star where's the helicopter"; HLS latency measured 2.2–3.5 s | pass |
| 8 | Captions match speech and are legible | **first build FAILED: captions ~8 s early** (subtitles burned before the seek). Fixed with input-side seek; re-verified: frames at 5.95/7.8/9.95/21.95 s show the word whisper timed at 5.9/7.5/9.9/21.9 s, none in silences | pass after fix |
| 9 | Vertical 1080x1920, full frame, no stretch, text in safe zone | frames inspected; automatic QC renders the text layer and scans 120 frames/clip: 0 frames outside x120–960 / y210–1480 on all 10 VOD clips; text bbox x126–948, y270–1384 | pass |
| 10 | Rolling buffer deletes old segments, never needed ones | 2-min buffer held at 0.12 GB across a recorder restart; clips still rendered. **Bug found: leftover buffer not cleared at shutdown** (daemon thread killed) → fixed, re-verified "cleared 7 buffer segments", 0 .ts left | pass after fix |
| 11 | Recorder death / stream end handled | streamlink killed mid-run → restarted as part 2 within 1 s; `--max-minutes` shutdown finished queued clips and exited 0. A real end-of-stream was not observed | pass (stream end not observed) |
| 12 | Index record per clip | `clips/index.jsonl` + per-clip `.json` with times, score, chat sample, transcript, hook, qc, files | pass |
| 13 | Auto mode picks top live streams in a game | `--game "Grand Theft Auto VI" --top 2 --lang en` started alanzoka + kaicenat, 5 clips. `--lang` trusts the channel's declared language (alanzoka is Portuguese, tagged EN) | pass |
| 14 | Past-stream mode finds the fun parts of an earlier stream | `--vod kaicenat`: 146k-message chat replay (no login) + 33 viewer clips → 90 moments → top 10; top 2 are where chat AND viewers agree | pass |
| 15 | Audio -14 LUFS / under -1 dBTP | first build peaked at -0.3 dBFS → limiter added; now -12.2…-14.5 LUFS, peaks -1.4…-3.9 dBFS (sample peak; true peak not measured) | pass after fix |
| 16 | Hook: human headline, lands 1.2–1.6 s, all words shown | weak chat reactions ("LMAO", "YOO") now give no hook; unprintable emoji stripped. **Bug: 9-word hook lost its last word** (8-word cap) → fixed in code, **not yet re-rendered** | fix pending re-render |
