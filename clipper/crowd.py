"""Crowd proof: for every clip, the Twitch clips viewers made of the same moment, and their views.
   python crowd.py        -> crowd.json + a table (best first)"""
import datetime as dt
import json
import sys

import autoclip as a
import export_clips as ex


def viewer_clips(login: str) -> list:
    """Top viewer-made clips of the last day (up to 100), with the wall-clock time each was made."""
    q = ("query($l:String!){ user(login:$l){ clips(first:100, criteria:{period:LAST_DAY, sort:VIEWS_DESC}){ edges{ node{"
         " title viewCount createdAt durationSeconds } } } } }")
    for attempt in range(3):
        try:
            d = a.gql(q, {"l": login})
            return [dict(e["node"], t=a.iso_epoch(e["node"]["createdAt"])) for e in d["user"]["clips"]["edges"]]
        except Exception:  # noqa: BLE001
            pass
    return []


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ours = []
    for root in ex.SOURCES:
        for meta in root.glob("*/*/*.json"):
            d = json.loads(meta.read_text("utf-8"))
            if not ex.rejected(d.get("file_base", "")):
                ours.append(d)
    cache, out = {}, {}
    for d in ours:
        ch = d["channel"]
        if ch not in cache:
            cache[ch] = viewer_clips(ch)
        start = dt.datetime.fromisoformat(d["clip_start"]).timestamp()
        end = start + d["duration"]
        # a viewer presses "clip" during or shortly after the moment
        hits = [c for c in cache[ch] if start - 5 <= c["t"] <= end + 90]
        out[d["file_base"]] = {"views": sum(c["viewCount"] for c in hits), "clips": len(hits),
                               "titles": [f"{c['title']} ({c['viewCount']})" for c in hits][:4]}
    (a.HERE / "crowd.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
    for base, v in sorted(out.items(), key=lambda kv: -kv[1]["views"]):
        print(f"{v['views']:6d} views  {v['clips']} clips  {base:30s} {'; '.join(v['titles'])[:90]}")


if __name__ == "__main__":
    main()
