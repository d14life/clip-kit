"""YouTube: newest uploads for a query, ranked by views per day. Optional top comments.

Usage:
  python yt_search.py "GTA 6 money glitch" ["GTA 6 secret" ...] [--n 50] [--top 15 per query] [--days 7] [--comments 5] [--out file.json]

Uses `python -m yt_dlp` on the YouTube results URL sorted by upload date (newest first);
older yt-dlp also accepted "ytsearchdateN:<q>", removed by 2026.08. Flat search gives views but no date,
so the top --top by raw views are re-fetched in full to get upload_date, then ranked by views/day.
--comments K pulls the top 20 comments of the best K videos (slow: ~10 s per video).
"""
import argparse, json, subprocess, sys, time, urllib.parse
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace"); sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def ytdlp(args, timeout=300):
    r = subprocess.run([sys.executable, "-m", "yt_dlp", "--no-warnings", "-J", *args],
                       capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError((r.stderr or "no output").strip().splitlines()[-1][:300])
    return json.loads(r.stdout)

def views_per_day(views, upload_date):
    if not views or not upload_date:
        return 0.0
    age = (datetime.now(timezone.utc) - datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=timezone.utc)).days
    return views / max(age, 1)  # same-day uploads count as one day

def enrich(r):
    try:
        full = ytdlp(["--skip-download", r["url"]], timeout=120)
        r.update(upload_date=full.get("upload_date"), views=full.get("view_count") or r["views"],
                 likes=full.get("like_count"), comment_count=full.get("comment_count"),
                 is_short=(full.get("duration") or 999) <= 180)
    except Exception as e:
        r["error"] = str(e)
    ud = r.get("upload_date")
    r["age_days"] = (datetime.now(timezone.utc) - datetime.strptime(ud, "%Y%m%d").replace(tzinfo=timezone.utc)).days if ud else None
    r["views_per_day"] = round(views_per_day(r["views"], ud))
    time.sleep(1)  # be polite; YouTube rate-limits bursts

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("queries", nargs="+")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--top", type=int, default=15, help="videos kept per query")
    ap.add_argument("--days", type=float, default=7, help="drop videos older than N days when upload date is known (0 = off)")
    ap.add_argument("--comments", type=int, default=0)
    ap.add_argument("--out")
    a = ap.parse_args()

    seen, rows, top = set(), [], []
    for q in a.queries:
        try:
            # yt-dlp 2026.08 dropped the "ytsearchdateN:" prefix ("Unsupported url scheme");
            # the results URL with sp=CAI= (sort by upload date) is the same search.
            url = "https://www.youtube.com/results?" + urllib.parse.urlencode({"search_query": q, "sp": "CAI="})
            flat = ytdlp(["--flat-playlist", "--playlist-end", str(a.n), url])
        except Exception as e:
            print(f"[yt] search failed for {q!r}: {e}", file=sys.stderr); continue
        got = 0
        for e in flat.get("entries") or []:
            if e.get("id") and e["id"] not in seen:
                seen.add(e["id"]); got += 1
                rows.append({"id": e["id"], "title": e.get("title"), "channel": e.get("channel") or e.get("uploader"),
                             "views": e.get("view_count") or 0, "duration": e.get("duration"), "query": q,
                             "url": f"https://www.youtube.com/watch?v={e['id']}"})
        print(f"[yt] {q!r}: {got} new videos", file=sys.stderr)
        qrows = sorted((r for r in rows if r["query"] == q), key=lambda r: r["views"], reverse=True)[:a.top]
        for r in qrows:
            enrich(r)
        top += [r for r in qrows if not (a.days and r.get("upload_date") and r["age_days"] > a.days)]
    top.sort(key=lambda r: r["views_per_day"], reverse=True)

    for r in top[:a.comments]:
        try:
            full = ytdlp(["--skip-download", "--write-comments", "--extractor-args",
                          "youtube:max_comments=20,all,0,0;comment_sort=top", r["url"]], timeout=180)
            r["top_comments"] = [{"likes": c.get("like_count") or 0, "text": (c.get("text") or "")[:300]}
                                 for c in sorted(full.get("comments") or [], key=lambda c: c.get("like_count") or 0, reverse=True)[:10]]
        except Exception as e:
            r["comments_error"] = str(e)

    out = {"source": "youtube", "fetched": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "total_found": len(rows), "ranked": top}
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
    for r in top:
        print(f"{r['views_per_day']:>9,}/day {r['views']:>11,} views {r.get('upload_date') or '?':>8}  {r['title'][:70]}  {r['url']}")
    if not a.out:
        print(text)
    sys.exit(0 if rows else 1)

if __name__ == "__main__":
    main()
