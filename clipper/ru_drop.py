"""Drop exact clip bases (a recut replaced them). Usage: python ru_drop.py <base> [...]"""
import json, sys
d = json.load(open("drops.json", encoding="utf8"))
for b in sys.argv[1:]:
    if b not in d["drop_exact"]:
        d["drop_exact"].append(b)
json.dump(d, open("drops.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(d["drop_exact"][-3:])
