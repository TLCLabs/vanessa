# External Agent Skills Snapshots

These skills are vendored from upstream open-source repositories so they work out of the box in every checkout of Vanessa while remaining pinned to reviewed revisions.

*(Note: `tlc-labs-compass/` is tracked separately in [`tlc-labs-compass/references/SOURCE.md`](tlc-labs-compass/references/SOURCE.md)).*

## Tracked Upstream Sources

### 1. FreeCAD Scripts (`github/awesome-copilot`)
- Repository: [`https://github.com/github/awesome-copilot`](https://github.com/github/awesome-copilot)
- Source revision: [`7e408815ddcb64889a3683799a85399331cfd4ef`](https://github.com/github/awesome-copilot/tree/7e408815ddcb64889a3683799a85399331cfd4ef/skills/freecad-scripts)
- Installed directory: `freecad-scripts/`
- License: MIT (reproduced in `freecad-scripts/LICENSE`)

### 2. Mechanical AI Skill — Community Edition (`almightyshui/Mechanical-AI-Skill`)
- Repository: [`https://github.com/almightyshui/Mechanical-AI-Skill`](https://github.com/almightyshui/Mechanical-AI-Skill)
- Source revision: [`f15480dc5a50f3c583cb43965dc99ad944ee6f2c`](https://github.com/almightyshui/Mechanical-AI-Skill/tree/f15480dc5a50f3c583cb43965dc99ad944ee6f2c)
- Installed directory: `mechanical-ai-skill/`
- License: MIT (reproduced in `mechanical-ai-skill/LICENSE`)

### 3. Agentic KiCad Skills (`IxTechCrypto/kicad-skills`)
- Repository: [`https://github.com/IxTechCrypto/kicad-skills`](https://github.com/IxTechCrypto/kicad-skills)
- Source revision: [`0a6f948efb4c861b10f9f3103db21a4460c3f1b8`](https://github.com/IxTechCrypto/kicad-skills/tree/0a6f948efb4c861b10f9f3103db21a4460c3f1b8)
- Installed directories: `grill-me/`, `kicad-10-workflow/`, `kicad-core/`, `kicad-highcurrent/`, `kicad-highspeed/`, `kicad-newpart/`, `kicad-rf-lowpower/`, `pcb-routing-best-practices/`
- License: MIT (reproduced in each skill directory's `LICENSE` and `ATTRIBUTION.md`)

## Refreshing the Snapshots

Run the updater script from the repository root (or run `/update-skills` in OpenCode):

```bash
bash .opencode/skills/update-skills.sh
```

Then review the diff (`git diff .opencode/skills/`) to verify that no incompatible licenses or unsafe script changes were introduced before committing.
