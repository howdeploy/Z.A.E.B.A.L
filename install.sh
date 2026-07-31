#!/usr/bin/env bash
# Z.A.E.B.A.L. installer — wires profanity-triggered self-audit hooks into
# Claude Code, Codex CLI, Kimi CLI and OpenCode (whichever are present).
# Idempotent and upgrade-safe: existing zaebal hook entries are replaced.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.zaebal"

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 not found in PATH" >&2
  exit 1
fi

# 1. Core (user config ~/.zaebal/config.json is preserved)
mkdir -p "$DEST"
rm -rf "$DEST/core"
cp -r "$SRC/core" "$DEST/core"
echo "[core]      installed to $DEST/core"

# 2. Hook adapters (JSON hosts share one merge script; $1 = file, $2 = host)
merge_json_hook() {
  python3 - "$1" "$2" <<'PYEOF'
import json, pathlib, sys

path, host = pathlib.Path(sys.argv[1]), sys.argv[2]
try:
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
except json.JSONDecodeError:
    sys.exit(f"skip: {path} is not valid JSON, edit it manually")

hooks = data.setdefault("hooks", {})
# drop old zaebal entries from every event (idempotent reinstall)
for event, groups in list(hooks.items()):
    if not isinstance(groups, list):
        continue
    for group in list(groups):
        group["hooks"] = [h for h in group.get("hooks", [])
                          if "zaebal.py" not in h.get("command", "")]
    groups[:] = [g for g in groups if g.get("hooks")]

groups = hooks.setdefault("UserPromptSubmit", [])
groups.append({
    "hooks": [{
        "type": "command",
        "command": f"python3 ~/.zaebal/core/zaebal.py --host {host}",
        "timeout": 180,
    }]
})

path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PYEOF
}

backup() {  # $1 = config file about to be modified
  if [ -f "$1" ]; then
    cp "$1" "$1.bak"
    echo "[backup]    $1 -> $1.bak"
  fi
}

if [ -d "$HOME/.claude" ]; then
  backup "$HOME/.claude/settings.json"
  # a skipped (invalid JSON) file must not abort the whole install (set -e)
  if merge_json_hook "$HOME/.claude/settings.json" claude; then
    echo "[claude]    hooks wired into ~/.claude/settings.json"
  fi
fi

if [ -d "$HOME/.codex" ]; then
  backup "$HOME/.codex/hooks.json"
  if merge_json_hook "$HOME/.codex/hooks.json" codex; then
    echo "[codex]     hooks wired into ~/.codex/hooks.json"
  fi
fi

if [ -d "$HOME/.kimi-code" ]; then
  KIMI_CFG="$HOME/.kimi-code/config.toml"
  touch "$KIMI_CFG"
  backup "$KIMI_CFG"
  if grep -q ">>> Z.A.E.B.A.L. hook" "$KIMI_CFG"; then
    # replace old block (upgrade path)
    python3 - "$KIMI_CFG" <<'PYEOF'
import pathlib, re, sys
path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = re.sub(
    r"\n?# >>> Z\.A\.E\.B\.A\.L\. hook.*?# <<< Z\.A\.E\.B\.A\.L\. hook <<<\n?",
    "\n", text, flags=re.DOTALL)
path.write_text(text, encoding="utf-8")
PYEOF
  fi
  printf '\n' >> "$KIMI_CFG"
  cat "$SRC/adapters/kimi-cli/hooks-snippet.toml" >> "$KIMI_CFG"
  echo "[kimi]      hooks wired into ~/.kimi-code/config.toml"
fi

if [ -d "$HOME/.config/opencode" ]; then
  mkdir -p "$HOME/.config/opencode/plugins"
  cp "$SRC/adapters/opencode/zaebal.ts" "$HOME/.config/opencode/plugins/zaebal.ts"
  echo "[opencode]  plugin installed to ~/.config/opencode/plugins/zaebal.ts"
fi

# 3. Skill (shared agents-skills path + Claude's native skills dir)
mkdir -p "$HOME/.agents/skills"
rm -rf "$HOME/.agents/skills/zaebal"
cp -r "$SRC/skills/zaebal" "$HOME/.agents/skills/zaebal"
echo "[skill]     installed to ~/.agents/skills/zaebal"
if [ -d "$HOME/.claude" ]; then
  mkdir -p "$HOME/.claude/skills"
  rm -rf "$HOME/.claude/skills/zaebal"
  cp -r "$SRC/skills/zaebal" "$HOME/.claude/skills/zaebal"
  echo "[skill]     installed to ~/.claude/skills/zaebal"
fi

echo
echo "Z.A.E.B.A.L. installed. Restart your agent sessions to pick up the hooks."
echo "Verify with:  echo '{\"session_id\":\"test\",\"prompt\":\"ты меня заебал\"}' | python3 ~/.zaebal/core/zaebal.py --host kimi"
