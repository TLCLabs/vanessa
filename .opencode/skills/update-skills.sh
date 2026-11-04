#!/usr/bin/env bash
# Refresh vendored external agent skills in .opencode/skills/ from upstream
# repositories and update the recorded commit SHAs in .opencode/skills/SOURCE.md.
# Does not touch project-native skills such as tlc-labs-compass/.

set -euo pipefail

SKILLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_FILE="$SKILLS_DIR/SOURCE.md"
WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/vanessa-skills-update.XXXXXX")"
trap 'rm -rf "$WORKDIR"' EXIT

echo "==> Fetching upstream skill repositories into temporary workspace..."

# 1. github/awesome-copilot (skills/freecad-scripts)
git clone --quiet --depth 1 --filter=blob:none --sparse \
  https://github.com/github/awesome-copilot.git "$WORKDIR/awesome-copilot"
git -C "$WORKDIR/awesome-copilot" sparse-checkout set --no-cone '/LICENSE' '/skills/freecad-scripts'
FREECAD_SHA="$(git -C "$WORKDIR/awesome-copilot" rev-parse HEAD)"

# 2. almightyshui/Mechanical-AI-Skill
git clone --quiet --depth 1 \
  https://github.com/almightyshui/Mechanical-AI-Skill.git "$WORKDIR/Mechanical-AI-Skill"
MECH_SHA="$(git -C "$WORKDIR/Mechanical-AI-Skill" rev-parse HEAD)"

# 3. IxTechCrypto/kicad-skills
git clone --quiet --depth 1 \
  https://github.com/IxTechCrypto/kicad-skills.git "$WORKDIR/kicad-skills"
KICAD_SHA="$(git -C "$WORKDIR/kicad-skills" rev-parse HEAD)"

echo "==> Syncing freecad-scripts ($FREECAD_SHA)..."
mkdir -p "$WORKDIR/staged/freecad-scripts"
cp -r "$WORKDIR/awesome-copilot/skills/freecad-scripts/." "$WORKDIR/staged/freecad-scripts/"
cp "$WORKDIR/awesome-copilot/LICENSE" "$WORKDIR/staged/freecad-scripts/LICENSE"
mkdir -p "$SKILLS_DIR/freecad-scripts"
rsync -a --delete "$WORKDIR/staged/freecad-scripts/" "$SKILLS_DIR/freecad-scripts/"

echo "==> Syncing mechanical-ai-skill ($MECH_SHA)..."
mkdir -p "$WORKDIR/staged/mechanical-ai-skill"
for item in SKILL.md AGENT_README.md LICENSE README.md sdk connectors scripts references data examples; do
  if [ -e "$WORKDIR/Mechanical-AI-Skill/$item" ]; then
    cp -r "$WORKDIR/Mechanical-AI-Skill/$item" "$WORKDIR/staged/mechanical-ai-skill/"
  fi
done
find "$WORKDIR/staged/mechanical-ai-skill" -name '__pycache__' -type d -prune -exec rm -rf {} +
chmod +x "$WORKDIR/staged/mechanical-ai-skill/scripts/"*.py \
         "$WORKDIR/staged/mechanical-ai-skill/scripts/"*.sh \
         "$WORKDIR/staged/mechanical-ai-skill/examples/"*.sh 2>/dev/null || true
mkdir -p "$SKILLS_DIR/mechanical-ai-skill"
rsync -a --delete "$WORKDIR/staged/mechanical-ai-skill/" "$SKILLS_DIR/mechanical-ai-skill/"

echo "==> Syncing kicad-skills ($KICAD_SHA)..."
for skill_path in "$WORKDIR/kicad-skills/skills/"*; do
  [ -d "$skill_path" ] || continue
  skill_name="$(basename "$skill_path")"
  mkdir -p "$WORKDIR/staged/$skill_name"
  cp -r "$skill_path/." "$WORKDIR/staged/$skill_name/"
  cp "$WORKDIR/kicad-skills/LICENSE" "$WORKDIR/staged/$skill_name/LICENSE"
  if [ -f "$WORKDIR/kicad-skills/ATTRIBUTION.md" ]; then
    cp "$WORKDIR/kicad-skills/ATTRIBUTION.md" "$WORKDIR/staged/$skill_name/ATTRIBUTION.md"
  fi
  if [ "$skill_name" = "kicad-core" ] || [ "$skill_name" = "kicad-10-workflow" ]; then
    cp -r "$WORKDIR/kicad-skills/scripts" "$WORKDIR/staged/$skill_name/scripts"
    cp -r "$WORKDIR/kicad-skills/tools" "$WORKDIR/staged/$skill_name/tools"
    find "$WORKDIR/staged/$skill_name" -name '__pycache__' -type d -prune -exec rm -rf {} +
  fi
  mkdir -p "$SKILLS_DIR/$skill_name"
  rsync -a --delete "$WORKDIR/staged/$skill_name/" "$SKILLS_DIR/$skill_name/"
done

echo "==> Updating $SOURCE_FILE..."
python3 - "$SOURCE_FILE" "$FREECAD_SHA" "$MECH_SHA" "$KICAD_SHA" <<'PY'
import re
import sys
from pathlib import Path

source_path = Path(sys.argv[1])
freecad_sha, mech_sha, kicad_sha = sys.argv[2:5]
text = source_path.read_text(encoding="utf-8")

text = re.sub(
    r"https://github\.com/github/awesome-copilot/tree/[0-9a-f]{40}/skills/freecad-scripts",
    f"https://github.com/github/awesome-copilot/tree/{freecad_sha}/skills/freecad-scripts",
    text,
)
text = re.sub(
    r"(\[`)[0-9a-f]{40}(`\]\(https://github\.com/github/awesome-copilot/tree/)",
    rf"\g<1>{freecad_sha}\g<2>",
    text,
)

text = re.sub(
    r"https://github\.com/almightyshui/Mechanical-AI-Skill/tree/[0-9a-f]{40}",
    f"https://github.com/almightyshui/Mechanical-AI-Skill/tree/{mech_sha}",
    text,
)
text = re.sub(
    r"(\[`)[0-9a-f]{40}(`\]\(https://github\.com/almightyshui/Mechanical-AI-Skill/tree/)",
    rf"\g<1>{mech_sha}\g<2>",
    text,
)

text = re.sub(
    r"https://github\.com/IxTechCrypto/kicad-skills/tree/[0-9a-f]{40}",
    f"https://github.com/IxTechCrypto/kicad-skills/tree/{kicad_sha}",
    text,
)
text = re.sub(
    r"(\[`)[0-9a-f]{40}(`\]\(https://github\.com/IxTechCrypto/kicad-skills/tree/)",
    rf"\g<1>{kicad_sha}\g<2>",
    text,
)

source_path.write_text(text, encoding="utf-8")
PY

echo "==> Skills refresh complete."
