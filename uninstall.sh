#!/usr/bin/env bash
# Z.A.E.B.A.L. uninstaller — removes hooks, plugin, skill and core.
set -euo pipefail

DEST="$HOME/.zaebal"

remove_json_hook() {  # $1 = settings file
  [ -f "$1" ] || return 0
  python3 - "$1" <<'PYEOF'
import json, pathlib, sys

path = pathlib.Path(sys.argv[1])
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except (json.JSONDecodeError, OSError):
    sys.exit(0)
changed = False
for event, groups in list(data.get("hooks", {}).items()):
    if not isinstance(groups, list):
        continue
    for group in list(groups):
        before = len(group.get("hooks", []))
        group["hooks"] = [h for h in group.get("hooks", [])
                          if "zaebal.py" not in h.get("command", "")]
        if len(group["hooks"]) != before:
            changed = True
    groups[:] = [g for g in groups if g.get("hooks")]
if changed:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PYEOF
}

[ -f "$HOME/.claude/settings.json" ] && remove_json_hook "$HOME/.claude/settings.json" && echo "[claude]    hooks removed"
[ -f "$HOME/.codex/hooks.json" ] && remove_json_hook "$HOME/.codex/hooks.json" && echo "[codex]     hooks removed"

KIMI_CFG="$HOME/.kimi-code/config.toml"
if [ -f "$KIMI_CFG" ] && grep -q ">>> Z.A.E.B.A.L. hook" "$KIMI_CFG"; then
  python3 - "$KIMI_CFG" <<'PYEOF'
import pathlib, re, sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = re.sub(
    r"\n?# >>> Z\.A\.E\.B\.A\.L\. hook.*?# <<< Z\.A\.E\.B\.A\.L\. hook <<<\n?",
    "\n", text, flags=re.DOTALL,
)
path.write_text(text, encoding="utf-8")
PYEOF
  echo "[kimi]      hooks removed"
fi

if [ -f "$HOME/.config/opencode/plugins/zaebal.ts" ]; then
  rm -f "$HOME/.config/opencode/plugins/zaebal.ts" && echo "[opencode]  plugin removed"
fi
if [ -d "$HOME/.agents/skills/zaebal" ]; then
  rm -rf "$HOME/.agents/skills/zaebal" && echo "[skill]     removed from ~/.agents/skills"
fi
if [ -d "$HOME/.claude/skills/zaebal" ]; then
  rm -rf "$HOME/.claude/skills/zaebal" && echo "[skill]     removed from ~/.claude/skills"
fi

if [ -f "$DEST/config.json" ]; then
  cp "$DEST/config.json" "$HOME/zaebal-config.backup.json"
  echo "[core]      user config backed up to ~/zaebal-config.backup.json"
fi
if [ -e "$DEST" ]; then
  rm -rf "$DEST" && echo "[core]      $DEST removed"
fi

echo
echo "Z.A.E.B.A.L. uninstalled."
