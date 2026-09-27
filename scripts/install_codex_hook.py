#!/usr/bin/env python3
"""Register the hook for Codex or Claude Code, sharing one JSON-merge helper.

The agent reads the OS-specific skill reference first. This helper performs
the fragile JSON merge; it does not discover hosts or install dependencies.
File name kept as install_codex_hook.py (tests and skill docs reference it);
--host selects the target (default codex, so existing invocations are unchanged).
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
from platform_runtime import shell_command, state_lock

MARKER = "Z.A.E.B.A.L. self-audit"


def is_ours(handler, host):
    if handler.get("statusMessage") == MARKER:
        return True
    # Migrate the exact legacy template for this host, not any command mentioning zaebal.
    return handler.get("command") == f"python3 ~/.zaebal/core/zaebal.py --host {host}"


def write_json(path, data, expected=Ellipsis):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        if expected is not Ellipsis:
            current = path.read_bytes() if path.exists() else None
            if current != expected:
                raise RuntimeError("hook config changed during installation; retry after review")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def install(config, dest, remove=False, host="codex"):
    # Other setup runs share this lock; external editors must stay closed.
    with state_lock(config.with_name(config.name + ".zaebal.lock")):
        return _install(config, dest, remove, host)


def _install(config, dest, remove, host):
    original = config.read_bytes() if config.exists() else None
    if remove and original is None:
        return {"config": str(config), "backup": None, "command": None, "removed": True}
    data = json.loads(original.decode("utf-8-sig")) if original else {}
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("hooks must be an object; config was not changed")
    for event, groups in hooks.items():
        if not isinstance(groups, list):
            raise ValueError(f"{event} must be a list; config was not changed")
        retained = []
        for group in groups:
            handlers = group.get("hooks", [])
            filtered = [h for h in handlers if not is_ours(h, host)]
            if len(filtered) == len(handlers):
                retained.append(group)
            elif filtered:
                group["hooks"] = filtered
                retained.append(group)
        groups[:] = retained
    command = None
    if not remove:
        command = shell_command([
            sys.executable, "-X", "utf8", str(dest / "core" / "zaebal.py"),
            "--host", host,
        ])
        hooks.setdefault("UserPromptSubmit", []).append({"hooks": [{
            "type": "command", "command": command,
            "statusMessage": MARKER, "timeout": 180,
        }]})
    # Validate first, then copy only shared runtime files; no other OS adapters.
    # Preserve config.json, state and incident history at the runtime root.
    if not remove:
        if (dest / "core").resolve() == (ROOT / "core").resolve():
            raise ValueError("runtime destination must differ from source checkout")
        shutil.copytree(ROOT / "core", dest / "core", dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    backup = None
    if original is not None:
        fd, backup_name = tempfile.mkstemp(prefix=config.name + ".zaebal-",
                                           suffix=".bak", dir=config.parent)
        backup = Path(backup_name)
        with os.fdopen(fd, "wb") as handle:
            handle.write(original)
    write_json(config, data, expected=original)
    # Skill copy/removal happens only after the hook write is confirmed, so a
    # rejected write (outside edit detected) never desyncs skill from hook.
    if host == "claude":
        skill_dest = config.parent / "skills" / "zaebal"
        shutil.rmtree(skill_dest, ignore_errors=True)
        if not remove:
            shutil.copytree(ROOT / "skills" / "zaebal", skill_dest)
    return {"config": str(config), "backup": str(backup) if backup else None,
            "command": command, "removed": remove}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=("windows", "linux"), required=True)
    parser.add_argument("--host", choices=("codex", "claude"), default="codex")
    parser.add_argument("--config", type=Path, default=None,
                        help="defaults to the selected host's own config path")
    parser.add_argument("--dest", type=Path, default=Path.home() / ".zaebal")
    parser.add_argument("--remove", action="store_true",
                        help="unregister only this hook; preserve runtime and user data")
    args = parser.parse_args()
    actual = "windows" if os.name == "nt" else "linux" if sys.platform.startswith("linux") else None
    if args.platform != actual:
        parser.error("selected instruction does not match this Python runtime OS")
    config = args.config
    if config is None:
        if args.host == "claude":
            config = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))) / "settings.json"
        else:
            config = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "hooks.json"
    result = install(config.expanduser().resolve(), args.dest.expanduser().resolve(),
                     args.remove, host=args.host)
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
