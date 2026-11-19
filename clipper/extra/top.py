import sys, json, glob, datetime as dt, re, time, collections
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
import autoclip as a
AC = str(__import__("pathlib").Path(__file__).resolve().parents[1])
OUT = __import__("os").environ.get("CLIP_WORK", "work")
EN = "kaicenat lacy clix xqc caseoh_ ishowspeed jynxzi theburntpeanut ohnepixel zackrawrr jasontheween stableronaldo yourragegaming joe_bartolozzi".split()
RU = "buster evelone2004 strogo recrent t2x2 mokrivskyi gagik gensyxa stintik frametamer666".split()
GAME = "Grand Theft Auto VI"
F = "title viewCount createdAt durationSeconds thumbnailURL videoOffsetSeconds url slug game{name} broadcaster{login} video{id createdAt}"
errors, clips = [], {}

def run(q, v, label):
    for i in range(3):
        try: return a.gql(q, v)
        except Exception as e:
            err = f"{label}: {str(e)[:160]}"; time.sleep(1)
    errors.append(err); return None

def add(n, region):
    if (n.get("game") or {}).get("name") != GAME: return False
    clips[n["slug"]] = dict(n, region=region); return True

stats = collections.Counter()
for region, lst in (("EN", EN), ("RU", RU)):
    for l in lst:
        d = run("query($l:String!){ user(login:$l){ clips(first:100, criteria:{period:LAST_DAY, sort:VIEWS_DESC}){ edges{ node{ %s } } } } }" % F, {"l": l}, l)
        if not d or not d.get("user"):
            if d is not None: errors.append(f"{l}: user not found")
            continue
        for e in d["user"]["clips"]["edges"]:
            stats[l, "seen"] += 1
            if not add(e["node"], region): stats[l, "other_game"] += 1
d = run('query{ game(name:"%s"){ clips(first:100, criteria:{period:LAST_DAY, sort:VIEWS_DESC}){ edges{ node{ %s } } } } }' % (GAME, F), {}, "game")
game_n = 0
if d:
    for e in d["game"]["clips"]["edges"]:
        n = e["node"]; n["slug"] in clips or add(n, "GAME")
        game_n += 1

# ours: (channel, local-epoch start) and (channel, seconds-of-day)
ours = []
for root in ("clips_crowd", "clips_fresh"):
    for p in glob.glob(f"{AC}/{root}/*/*/*.json"):
        try: m = json.load(open(p, encoding="utf-8"))
        except Exception: continue
        if not isinstance(m, dict): continue
        for k in ("moment", "clip_start"):
            if m.get(k):
                try: ours.append((m["channel"], dt.datetime.fromisoformat(m[k]).timestamp(), root))
                except Exception: pass
sc = json.load(open(f"{AC}/scores.json", encoding="utf-8"))["scores"]
sod = []
for k in sc:
    ch, hms = k.rsplit("_", 1)
    if re.fullmatch(r"\d{6}", hms): sod.append((ch, int(hms[:2])*3600+int(hms[2:4])*60+int(hms[4:]), "scores.json"))

def have(c):
    ch = c["broadcaster"]["login"]
    if c.get("video") and c.get("videoOffsetSeconds") is not None:
        t = dt.datetime.fromisoformat(c["video"]["createdAt"].replace("Z", "+00:00")).timestamp() + c["videoOffsetSeconds"]
        basis = "vod_offset"
    else:
        t = dt.datetime.fromisoformat(c["createdAt"].replace("Z", "+00:00")).timestamp(); basis = "created_at"
    lt = dt.datetime.fromtimestamp(t)
    s = lt.hour*3600+lt.minute*60+lt.second
    hits = [f"{r}" for (o, ot, r) in ours if o == ch and abs(ot-t) <= 60]
    hits += [f"{r}" for (o, os_, r) in sod if o == ch and min(abs(os_-s), 86400-abs(os_-s)) <= 60]
    return sorted(set(hits)), basis, lt.isoformat(timespec="seconds")

rows = []
for c in clips.values():
    h, basis, lt = have(c)
    rows.append(dict(streamer=c["broadcaster"]["login"], region=c["region"], title=c["title"], views=c["viewCount"],
        created_at=c["createdAt"], moment_local=lt, match_basis=basis, duration=c["durationSeconds"], url=c["url"],
        thumbnail=c["thumbnailURL"], have=bool(h), have_in=h))
rows.sort(key=lambda r: -r["views"])
json.dump(rows, open(f"{OUT}/top24h.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
by = collections.defaultdict(list)
for r in rows: by[r["streamer"]].append(r)
md = [f"# GTA VI top clips, last 24h ({dt.datetime.now():%Y-%m-%d %H:%M})\n", f"Total {len(rows)}, new {sum(not r['have'] for r in rows)}. Only clips tagged Grand Theft Auto VI.\n",
      "## Per streamer\n", "| streamer | clips | new |", "|---|---|---|"]
for s, v in sorted(by.items(), key=lambda kv: -sum(r["views"] for r in kv[1])):
    md.append(f"| {s} | {len(v)} | {sum(not r['have'] for r in v)} |")
for s, v in sorted(by.items(), key=lambda kv: -sum(r["views"] for r in kv[1])):
    md += [f"\n### {s}\n", "| views | have | title | created (UTC) | dur | clip | thumb |", "|---|---|---|---|---|---|---|"]
    for r in v:
        md.append(f"| {r['views']} | {'yes' if r['have'] else 'NEW'} | {r['title'].replace('|','/')} | {r['created_at']} | {r['duration']}s | {r['url']} | {r['thumbnail']} |")
open(f"{OUT}/top24h.md", "w", encoding="utf-8").write("\n".join(md))
print("total", len(rows), "new", sum(not r["have"] for r in rows), "game_query_edges", game_n)
print("tz", time.tzname)
print("errors", errors)
print("excluded other-game:", {k[0]: v for k, v in stats.items() if k[1] == "other_game"})
for r in [r for r in rows if not r["have"]][:10]: print(r["streamer"], "|", r["title"], "|", r["views"])
