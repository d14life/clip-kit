"""Google Trends rising/top related queries via pytrends, with backoff on HTTP 429.

Usage:
  python gtrends.py "GTA 6" [--timeframe "now 7-d"] [--gprop youtube] [--geo ""] [--out file.json]

--gprop youtube = YouTube search interest (closest to what shorts viewers type). web = Google web search.
"Breakout" in rising means growth > 5000%.
pytrends is archived upstream; if it keeps failing, trendspyg (MIT, maintained) has a
drop-in `from trendspyg.compat.request import TrendReq`. Not installed here: vet before use.
"""
import argparse, json, sys, time
from datetime import datetime, timezone

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keyword")
    ap.add_argument("--timeframe", default="now 7-d")
    # "web" stands for pytrends' "" (PowerShell 5.1 drops empty-string arguments)
    ap.add_argument("--gprop", default="youtube", choices=["web", "youtube", "news", "images", "froogle"])
    ap.add_argument("--geo", default="")
    ap.add_argument("--tries", type=int, default=5)
    ap.add_argument("--out")
    a = ap.parse_args()
    a.gprop = "" if a.gprop == "web" else a.gprop

    from pytrends.request import TrendReq
    out = {"source": "google-trends", "keyword": a.keyword, "timeframe": a.timeframe, "gprop": a.gprop or "web",
           "fetched": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    for i in range(a.tries):
        try:
            pt = TrendReq(hl="en-US", tz=0)
            pt.build_payload([a.keyword], timeframe=a.timeframe, geo=a.geo, gprop=a.gprop)
            rq = pt.related_queries().get(a.keyword) or {}
            for kind in ("rising", "top"):
                df = rq.get(kind)
                out[kind] = [] if df is None else [{"query": q, "value": str(v)} for q, v in zip(df["query"], df["value"])]
            break
        except Exception as e:
            wait = 20 * 2 ** i  # 429s clear after a minute or two; hammering makes it worse
            print(f"[trends] try {i+1}/{a.tries} failed: {str(e)[:150]}; waiting {wait}s", file=sys.stderr)
            if i == a.tries - 1:
                out["error"] = str(e)[:300]
            else:
                time.sleep(wait)

    text = json.dumps(out, ensure_ascii=False, indent=1)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
    for kind in ("rising", "top"):
        print(f"--- {kind}: {len(out.get(kind) or [])}")
        for r in out.get(kind) or []:
            print(f"  {r['value']:>8}  {r['query']}")
    if not a.out:
        print(text)
    sys.exit(1 if "error" in out else 0)

if __name__ == "__main__":
    main()
