import json
u = json.load(open("ru_unscored.json"))
n = 2
parts = [u[i::n] for i in range(n)]
for i, p in enumerate(parts, 1):
    json.dump(p, open(f"ru_b{i}.json", "w"))
print([len(p) for p in parts])
