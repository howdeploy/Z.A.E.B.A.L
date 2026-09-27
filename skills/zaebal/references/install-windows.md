# Native Windows hook setup

Read this only for an installation/update/removal request targeting a native
Windows agent. WSL is a separate Linux environment: use its reference only when
the agent itself runs there. Do not install WSL, Bash, or Linux packages.

## Select and install

1. Use the full `howdeploy/Z.A.E.B.A.L` checkout matching this skill's revision.
   A skill-only download lacks `core/` and `scripts/`. Obtain the corresponding
   repository revision, inspect it, and run the helper from that checkout. Do not
   mix a newer instruction with an older runtime. If no revision is recorded,
   use one fresh checkout as the source of both the skill and runtime.
2. Find an existing Python 3.10+ (`py -3`, `python`, or an absolute executable).
   Confirm its version and `os.name == 'nt'`. Use it throughout setup; do not add
   another Python when a working one exists. There are no pip dependencies.
3. For **Codex**, from that checkout run:

   ```powershell
   py -3 scripts/install_codex_hook.py --platform windows --host codex
   ```

   For **Claude Code**, run:

   ```powershell
   py -3 scripts/install_codex_hook.py --platform windows --host claude
   ```

   Substitute the discovered Python if needed. The helper registers only the
   selected host, honors `CODEX_HOME` (Codex) or `CLAUDE_CONFIG_DIR` (Claude
   Code), and stores an absolute command for that interpreter and runtime in
   `hooks.json` (Codex) or `settings.json` (Claude Code). The Windows launcher
   explicitly uses built-in PowerShell with `-NoProfile`; paths are literal and
   JSON stays on stdin. No Linux launcher is installed. `--config` and `--dest`
   select explicit paths for isolated checks or non-default installations.
   Existing unrelated hooks, user configuration and incident history are
   preserved. A unique config backup path is printed. Repeating installation
   replaces this hook, not duplicates it. Close editors changing the config
   file during setup. Concurrent helper runs are serialized; outside edits
   detected before replacement abort the update, but uncoordinated external
   editors do not share its lock. For Claude Code, the helper also copies
   `skills/zaebal` next to the config file so `/zaebal` works; removal deletes
   that copy.
4. Native Windows registration for Kimi/OpenCode is **not established by this
   helper**. Do not write a Codex/Claude hook into their configuration or
   silently switch to WSL. Inspect the selected host's current Windows hook
   contract before extending its adapter. The existing Linux adapters remain
   available on Linux.

## Verify and activate

Run `py -3 -X utf8 -m unittest discover -s tests -p test_cross_platform.py` from
the checkout. This short smoke suite uses temporary config/state directories,
executes the registered Windows command, and does not start a paid auditor.

After a requested live installation, use Codex `/hooks` (or Claude Code
`/hooks`) to review/trust the registered source if the installed version
requires it, then start a fresh session and verify that a controlled
complaint injects `<zaebal level="1">`.
An ordinary message must stay silent. Do not automatically run an audit protocol
because a test fixture contains a complaint. Do not equate a standalone core run
with proof that the user's host loaded the hook. If a live check is unavailable,
say "command smoke passed; host activation unverified".

External audit uses an existing CLI. Missing/incompatible auditors must degrade
visibly. Prefer a native executable; for a custom command with Windows paths use
an `auditor_command` JSON array of arguments (prompt is appended), not shell text.
For a Python-based wrapper, use `["C:\\path\\python.exe", "C:\\path\\audit.py"]`.
Do not enable unsafe auditors to make a smoke check pass.

## Update or remove

Update from one matching checkout by repeating the selected install command.
To unregister only this hook:

```powershell
py -3 scripts/install_codex_hook.py --platform windows --host <codex|claude> --remove
```

Repeat any custom `--config`/`--dest` arguments used at installation. Removal
preserves runtime, settings and history for other hosts and recovery. Remove
those separately only when explicitly requested and no remaining hook uses them.
