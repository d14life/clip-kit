import export_clips as e, json, pathlib
RU = "strogo buster evelone2004 mokrivskyi t2x2 gagik gensyxa stintik frametamer666 recrent".split()
u = [x for x in e.unscored() if pathlib.Path(x).parent.parent.name in RU]
print(len(u))
for x in u:
    d = json.load(open(x, encoding="utf8"))
    print(pathlib.Path(x).name, d.get("duration"), d.get("game"), (d.get("transcript") or "")[:70].replace("\n", " "))
json.dump(u, open("ru_unscored.json", "w"))
