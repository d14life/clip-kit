"""Reddit via the Arctic Shift archive API (reddit.com itself is never contacted).

Usage:
  python reddit_arctic.py [--subs GTA6,GTA,GTAonline] [--days 7] [--title "glitch"] [--top 25] [--out file.json]

Arctic Shift snapshots each post when it ingests it, so `score` is usually ~1.
num_comments is the best signal there is, so rank by that. --title filters on a title word.
Pages back in time with `before=` until --days is covered or --max posts are read.
"""
import argparse, json, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace"); sys.stderr.reconfigure(encoding="utf-8", errors="replace")

API = "https://arctic-shift.photon-reddit.com/api/posts/search"

def get(params, tries=4):
    url = API + "?" + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "trend-hunt/1.0"})
            return json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8")).get("data") or []
        except Exception as e:
            if (isinstance(e, urllib.error.HTTPError) and e.code == 422) or i == tries - 1:  # 422: caller shrinks the query
                raise
            print(f"[reddit] retry {i+1}: {e}", file=sys.stderr); time.sleep(15 * (i + 1))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subs", default="GTA6,GTA,GTAonline")
    ap.add_argument("--days", type=float, default=7)
    ap.add_argument("--title")
    # r/GTA6 posts >1000/day around a launch, so 1000 covered only ~1 day of a 7-day window
    ap.add_argument("--max", type=int, default=4000, help="posts to read per subreddit")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--tries", type=int, default=6, help="max consecutive HTTP 422 before giving up on a subreddit")
    ap.add_argument("--budget", type=int, default=300, help="stop a subreddit after N seconds and return what was read")
    ap.add_argument("--out")
    a = ap.parse_args()

    after = int(time.time() - a.days * 86400)
    rows = []
    for sub in a.subs.split(","):
        before, n, fails, limit, span, now = None, 0, 0, 100, a.days * 86400, int(time.time())
        t0 = time.time()
        while n < a.max:
            if time.time() - t0 > a.budget:
                print(f"[reddit] r/{sub}: --budget {a.budget}s reached; returning partial results", file=sys.stderr); break
            lo = max(after, (before or now) - span)
            p = {"subreddit": sub, "after": int(lo), "limit": limit, "sort": "desc"}
            if before: p["before"] = before
            try:
                batch = get(p)
                fails = 0
            except urllib.error.HTTPError as e:
                if e.code != 422:
                    print(f"[reddit] r/{sub} failed: {e}", file=sys.stderr); break
                fails += 1  # 422 = server timeout: ask for less (smaller page, then narrower time window)
                if fails > a.tries:
                    print(f"[reddit] r/{sub}: gave up after {a.tries} HTTP 422; returning partial results", file=sys.stderr); break
                limit, span = max(10, limit // 2), max(3600, span / 2)
                print(f"[reddit] 422: limit={limit}, window={span/3600:.1f}h, try {fails}/{a.tries}", file=sys.stderr); time.sleep(3); continue
            except Exception as e:
                print(f"[reddit] r/{sub} failed: {e}", file=sys.stderr); break
            # title filter runs locally: the server-side title search times out (422) on big subs
            keep = [x for x in batch if not a.title or a.title.lower() in (x.get("title") or "").lower()]
            rows += [{"sub": sub, "num_comments": x.get("num_comments") or 0, "score": x.get("score"),
                      "title": x.get("title"), "created": datetime.fromtimestamp(x["created_utc"], timezone.utc).strftime("%Y-%m-%d %H:%M"),
                      "link": x.get("url"), "permalink": "https://www.reddit.com" + (x.get("permalink") or "")} for x in keep]
            n += len(batch)
            if len(batch) >= limit:
                before = batch[-1]["created_utc"]
            else:  # this window is exhausted: step to the one below it
                before = int(lo)
                if lo <= after: break
            time.sleep(1)
        oldest = datetime.fromtimestamp(before, timezone.utc).strftime("%Y-%m-%d %H:%M") if before else "-"
        capped = " (hit --max: window NOT fully covered)" if n >= a.max else (" (stopped early: window NOT fully covered)" if before and before > after + 60 else "")
        print(f"[reddit] r/{sub}: {n} posts read, back to {oldest} UTC{capped}", file=sys.stderr)

    rows.sort(key=lambda r: r["num_comments"], reverse=True)
    top = rows[:a.top]
    out = {"source": "reddit/arctic-shift", "fetched": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "posts_read": len(rows), "ranked": top,
           "note": "permalinks are for the record only; reddit.com may be blocked on the user's network and must not be circumvented"}
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
    for r in top:
        print(f"{r['num_comments']:>5} comments  r/{r['sub']:<10} {r['created']}  {r['title'][:80]}")
    if not a.out:
        print(text)
    sys.exit(0 if rows else 1)

if __name__ == "__main__":
    main()
