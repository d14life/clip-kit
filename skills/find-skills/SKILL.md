---
name: find-skills
description: "Use at the start of any non-trivial task to check whether an installed skill covers it. Lists all available skills and matches them to the task. Triggers: find a skill, is there a skill for this, what skills do I have, or when unsure which skill applies."
---

# Find Skills

Discover the right skill for the task at hand, then use it.

## Steps

1. **Check the in-context catalog first.** Every session already lists "available skills"
   (names + descriptions) in a system reminder — that list is the **authoritative,
   complete** catalog and is the ONLY place built-in skills (code-review, verify, run,
   security-review, loop, schedule, claude-api, simplify, update-config, …) appear. Scan
   it for anything whose description fits the task.

2. **Keyword-search on-disk skills** when the list is long or you want to grep descriptions
   (covers plugins, your user skills, `~/.agents`, and this project — but NOT the bundled
   built-ins from step 1):
   ```bash
   bash ~/.claude/skills/find-skills/list-skills.sh [keywords]
   ```
   Examples:
   - `bash ~/.claude/skills/find-skills/list-skills.sh pdf` → skills mentioning "pdf"
   - `bash ~/.claude/skills/find-skills/list-skills.sh deploy vercel` → matches either word
   - `bash ~/.claude/skills/find-skills/list-skills.sh` → everything on disk

3. Pick the skill whose **description** best fits (match on what it does, not just its name).

4. Invoke it with the **Skill** tool, e.g. `Skill(skill: "pdf")`. For plugin-namespaced
   skills use the full `plugin:skill` name exactly as printed (e.g. `anthropic-skills:xlsx`).

5. If nothing genuinely fits, proceed normally — not every task needs a skill. Don't
   force-fit an unrelated one.
