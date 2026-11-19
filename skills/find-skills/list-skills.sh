#!/usr/bin/env bash
# Lists every available skill (name + description) so the right one can be chosen.
# Optional args = keywords; only skills whose name/description match any keyword are shown.
python3 - "$@" <<'PY'
import os, glob, re, sys

roots = [
    os.path.expanduser("~/.claude/plugins/cache"),  # installed plugin skills
    os.path.expanduser("~/.claude/skills"),         # your user skills
    os.path.expanduser("~/.agents/skills"),         # shared agent skills (supabase, etc.)
    os.path.join(os.getcwd(), ".claude", "skills"), # this project's skills
]
paths = []
for r in roots:
    paths += glob.glob(os.path.join(r, "**", "SKILL.md"), recursive=True)

seen, rows = set(), []
for p in sorted(paths):
    try:
        txt = open(p, encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    m = re.match(r"^---\s*\n(.*?)\n---", txt, re.S)
    fm = m.group(1) if m else txt[:600]
    nm = re.search(r"^name:\s*(.+)$", fm, re.M)
    ds = re.search(r"^description:\s*(.+(?:\n[ \t]+.+)*)$", fm, re.M)
    name = (nm.group(1).strip().strip('"\'') if nm else os.path.basename(os.path.dirname(p)))
    desc = (re.sub(r"\s+", " ", ds.group(1)).strip().strip('"\'') if ds else "")
    if name in seen:
        continue
    seen.add(name)
    rows.append((name, desc))

rows.sort(key=lambda r: r[0].lower())
q = " ".join(sys.argv[1:]).lower().strip()
if q:
    toks = q.split()
    rows = [(n, d) for (n, d) in rows if any(t in (n + " " + d).lower() for t in toks)]
    print(f"# skills matching: {q}  ({len(rows)} found)\n")
else:
    print(f"# all available skills ({len(rows)})\n")

for n, d in rows:
    print(f"- {n}: {d[:220]}")

print("\n# NOTE: built-in skills (code-review, verify, run, security-review, loop, "
      "schedule, claude-api, simplify, update-config, init, review, etc.) are bundled "
      "in the CLI and NOT on disk — they appear in the 'available skills' list already "
      "in your session context. Check that list too; it is the authoritative catalog.")
PY
