"""Re-render every clip that is in the export folder with the current code (layout, length rules), keeping its
file name, and mark clips that were not during GTA VI (Twitch chapter markers) so the export drops them.
   python rerender.py"""
import collections
import datetime as dt
import json
import sys
from pathlib import Path

import autoclip as a
import export_clips as ex

GAME = "Grand Theft Auto VI"
LIVE_LAG = 5.0        # live wall-clock is ~4-6 s behind the broadcaster clock the VOD uses (measured HLS latency)
NON_GTA = a.HERE / "non_gta.json"


def iso_local(s: str) -> float:
    return dt.datetime.fromisoformat(s).timestamp()


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cfg, _ = a.parse_args(["x"])
    cfg.captions = True
    clips = []
    for root in ex.SOURCES:
        for meta in root.glob("*/*/*.json"):
            if meta.name.endswith(".fx.json"):
                continue                                      # per-clip meme plans live next to the meta
            d = json.loads(meta.read_text("utf-8"))
            if ex.rejected(d.get("file_base", "")):
                continue
            if len(sys.argv) > 1 and not any(d.get("file_base", "").startswith(x) for x in sys.argv[1:]):
                continue                                      # python rerender.py lacy_184519  -> just that clip
            clips.append((meta, d, root.name == "clips_live"))
    print(len(clips), "clips to check")
    factory = a.ClipFactory(cfg)
    factory.start()
    non_gta = set(json.loads(NON_GTA.read_text("utf-8"))) if NON_GTA.exists() else set()
    by_channel = collections.defaultdict(list)
    for item in clips:
        # the clip's OWN stream (vod_url), not the streamer's latest: a newer non-GTA stream made Speed/CaseOh
        # clips render as "NOT GTA"
        by_channel[(item[1]["channel"], item[1].get("vod_url") or "")].append(item)
    for (channel, vod_url), items in by_channel.items():
        video = a.resolve_vod(vod_url or channel)
        segs = a.vod_segments(video["id"], cfg.quality, video.get("createdAt"))
        chapters = a.vod_chapters(video["id"])
        vod_start = segs[0]["start"]
        sess = cfg.work / channel / f"vod_{video['id']}"
        sess.mkdir(parents=True, exist_ok=True)
        chat_file = sess / "chat.jsonl"
        per_sec = collections.Counter()
        if chat_file.exists():
            for line in chat_file.read_text("utf-8").splitlines():
                m = json.loads(line)
                per_sec[int(m["t"] - a.VOD_CHAT_LAG)] += a.chat_weight(m["m"])
        for meta, d, live in items:
            base = d["file_base"]
            lag = LIVE_LAG if live else 0.0
            onset = iso_local(d["moment"]) - lag
            clip_start = iso_local(d["clip_start"]) - lag
            game = a.game_at(chapters, onset - vod_start) if chapters else GAME
            if game != GAME:
                print(f"NOT GTA ({game}): {base}")
                non_gta.add(base)
                continue
            if onset < vod_start or onset > segs[-1]["start"] + segs[-1]["dur"]:
                print(f"not in the VOD (yet): {base}")
                continue
            sample = [(0.0, s.split(": ", 1)[0], s.split(": ", 1)[-1]) for s in d.get("chat_sample", [])]
            sp = a.Spike(onset=onset, bucket_start=onset, score=d.get("chat_score") or 0.0, baseline=d.get("baseline") or 0.0,
                         threshold=(d.get("baseline") or 0.0) * 1.6, ratio=d.get("ratio") or 0.0, sample=sample)
            fixed = d.get("found_by") == "manual range"
            if fixed:
                start, end, react_end = clip_start, clip_start + d["duration"], None
            else:
                react_end = onset + cfg.post
                if per_sec:
                    while react_end < onset + a.MAX_REACT and a.hot(per_sec, react_end - 3, react_end, a.react_level(sp)):
                        react_end += 4
                start, end = onset - a.WIDE_PRE, react_end + a.WIDE_POST
            job = a.ClipJob(channel, sp, start, end, {"title": video["title"], "game": video.get("game")}, sess)
            job.react_end = react_end
            keep = {k: d[k] for k in ("rank", "found_by", "stream_time", "vod_url", "viewer_clips", "rank_score") if k in d}
            job.extra = keep | {"file_base": base, "out_dir": str(meta.parent), "fixed": fixed}
            job.hook_sources = [v.rsplit(" (", 1)[0] for v in d.get("viewer_clips") or []]
            try:
                job.segments = a.download_window(segs, start, end, sess / "vod_segments")
            except OSError as e:
                print(f"download failed, kept old version: {base} ({e})")
                continue
            factory.submit(job)
            print(f"queued {base} ({'exact range' if fixed else 'length follows chat'})")
    NON_GTA.write_text(json.dumps(sorted(non_gta), indent=1), "utf-8")
    factory.q.join()
    print("done:", factory.done_count, "re-rendered;", len(non_gta), "marked not-GTA")


if __name__ == "__main__":
    main()
