---
description: Fetch the latest upstream versions of vendored agent skills and audit the diff
---

Refresh the vendored external agent skills in `.opencode/skills/`:

1. Run `bash .opencode/skills/update-skills.sh` to pull the latest upstream revisions for `freecad-scripts`, `mechanical-ai-skill`, and `kicad-skills`, and update `.opencode/skills/SOURCE.md`.
2. Check `git status --short .opencode/skills/` and `git diff -- .opencode/skills/` to see if anything changed.
3. Audit any changed `SKILL.md` files, `LICENSE` files, or scripts under `.opencode/skills/` for license changes or security concerns.
4. Summarize the upstream changes and ask before creating any git commit.
