"""Merge a RU review round into scores.json / names.json / non_gta.json. Usage: python ru_merge.py <round.json>"""
import json, sys, pathlib
N = __import__("os").environ.get("CLIP_NOTES_DIR", ".")
rows = json.load(open(sys.argv[1], encoding="utf8"))
here = pathlib.Path(__file__).parent
def load(n):
    return json.load(open(here / n, encoding="utf8"))
def save(n, d):
    json.dump(d, open(here / n, "w", encoding="utf8"), ensure_ascii=False, indent=1)
sc, nm, ng = load("scores.json"), load("names.json"), load("non_gta.json")
sc.setdefault("virality_100", {})
for r in rows:
    b = r["base"]; key = b.rsplit("_x", 1)[0]
    if not r.get("gta", True):
        if b not in ng and key not in ng:
            ng.append(b)
        continue
    sc["scores"][key] = r["score10"]
    sc["virality_100"][key] = r["virality_100"]
    nm[b] = r["name"]
save("scores.json", sc); save("names.json", nm); save("non_gta.json", ng)
ok = [r for r in rows if r.get("gta", True)]
print(len(rows), "reviewed;", sum(r["score10"] >= 6 for r in ok), "at 6+; non-GTA:", len(rows) - len(ok))
for r in sorted(ok, key=lambda r: -r["score10"])[:3]:
    print(r["score10"], r["base"], r["name"])
