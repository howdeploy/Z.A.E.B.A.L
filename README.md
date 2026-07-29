<div align="center">

<img src="./assets/zaebal-hero.svg" width="100%" alt="Z.A.E.B.A.L. — self-audit protocol for coding agents">

<h3>
<strong>Z</strong>aebal? · <strong>A</strong>udit · <strong>E</strong>rrors ·
<strong>B</strong>reak · <strong>A</strong>nalyze · <strong>L</strong>eave no assumption
</h3>

<p>
<strong>Read this in other languages</strong><br>
<a href="README.md">🇺🇸 English</a> ·
<a href="README.ru.md">🇷🇺 Русский</a> ·
<a href="README.zh-CN.md">🇨🇳 简体中文</a>
</p>

<p>
<img alt="Python standard library only" src="https://img.shields.io/badge/Python-stdlib_only-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white">
<img alt="Four agent hosts" src="https://img.shields.io/badge/agent_hosts-4-A78BFA?style=flat-square">
<img alt="Russian, English and Chinese detection" src="https://img.shields.io/badge/detection-RU_·_EN_·_ZH-22D3EE?style=flat-square">
<img alt="Fail-open failure mode" src="https://img.shields.io/badge/failure_mode-fail--open-3FB950?style=flat-square">
</p>

<p>
<strong>Profanity-triggered self-audit for coding agents.</strong><br>
Z.A.E.B.A.L. treats user frustration as an operational signal: stop, re-check the
agent's assumptions, and escalate repeated failures to an independent auditor.
</p>

<p>
<a href="#capability-map">Capabilities</a> ·
<a href="#how-it-works">How it works</a> ·
<a href="#install">Install</a> ·
<a href="#configuration">Configuration</a> ·
<a href="#architecture">Architecture</a>
</p>

</div>

---

## Why it exists

When a coding agent gets stuck, it often repeats the same action with small variations
because one underlying belief about the task or codebase is wrong. The agent still treats
that belief as a fact, so another self-check can reproduce the same mistake.

Z.A.E.B.A.L. adds a feedback loop to the user-message boundary:

- profanity and direct complaints become an audit signal;
- positive profanity such as “fucking great” does not add to the streak and closes an
  active incident as an acknowledgment;
- repeated signals escalate from a local protocol to a full stop;
- at level 3, an external agent reads the transcript and repository evidence;
- work resumes only after an explicit user acknowledgment.

There is intentionally **no technical tool lock**. The protocol changes the agent's
instructions and asks it to stop; the human always retains the final control.

## Capability map

| Capability | What it does | Implementation |
|---|---|---|
| Multilingual detection | Detects Russian, English, and Chinese profanity, including punctuation-separated and common leetspeak forms. | `core/wordlists/{ru,en,zh}.txt` + NFKC normalization |
| Intent classification | Separates praise, directed complaints, and ambiguous frustration before changing the streak. | `classify()`; weights `0`, `1.0`, and `0.5` |
| Session escalation | Tracks each session in a 30-minute sliding window and selects L1, L2, or L3. | Atomic JSON state + POSIX `fcntl` lock |
| Three audit protocols | Injects increasingly strict instructions: independent checks, assumption inventory, and full stop. | `core/protocol/L1.md` → `L3.md` |
| External auditor | Runs the same or a cross-vendor CLI against the transcript tail and repository evidence. | Claude, Codex, Kimi, or OpenCode |
| Four host adapters | Hooks Claude Code, Codex CLI, Kimi CLI, and OpenCode at user-message submission. | JSON hooks, TOML hook, or TypeScript plugin |
| Explicit recovery | Resets the incident only after acknowledgment such as `continue`, `продолжай`, or `по плану`. | Per-session state lifecycle |
| Fail-open safety | A malformed payload, missing auditor, timeout, or internal error never breaks the host session. | Silent exit `0`; auditor errors become context |

## How it works

```text
User message
    │
    ▼
Host adapter
UserPromptSubmit / chat.message
    │
    ▼
core/zaebal.py
normalize → detect → classify
    │
    ├─ clean / praise ───────────────────────────────► silence
    │
    └─ directed (+1.0) / ambiguous (+0.5)
                         │
                         ▼
                per-session streak
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
             L1         L2         L3
              │          │          ├─ external auditor
              └──────────┴──────────┴─ protocol injected into context
```

### Escalation levels

| Level | Streak weight | Agent behavior | External auditor |
|---|---:|---|---|
| **L1** | `1–1.5` | Stop, run two independent checks, inventory assumptions, prepare a micro-plan. | Optional |
| **L2** | `2–3.5` | Remove unverified assumptions and compare the work against the original request. | Disabled by default |
| **L3** | `4+` | Stop all agents and background work; show the user the belief, evidence, and mismatch. | Enabled by default |

Directed complaints add `1.0`; profanity without a detected addressee adds `0.5`.
The window is 30 minutes. Calm questions do not reset it. Genuine praise or an explicit
acknowledgment does.

## Install

Requirements:

- `python3`; the core uses only the standard library;
- at least one supported agent CLI if external auditing is enabled.

From the repository root:

```bash
chmod +x install.sh
./install.sh
```

The installer detects available hosts, copies the core to `~/.zaebal/`, and updates only
the relevant user configuration:

| Host | Integration | Default auditor command |
|---|---|---|
| Claude Code | `UserPromptSubmit` in `~/.claude/settings.json` | `claude -p` with `Read,Grep,Glob` only |
| Codex CLI | `UserPromptSubmit` in `~/.codex/hooks.json` | `codex exec --sandbox read-only` |
| Kimi CLI | hook block in `~/.kimi-code/config.toml` | `kimi -p` |
| OpenCode | plugin in `~/.config/opencode/plugins/zaebal.ts` | `opencode run` |

Installation is idempotent: existing Z.A.E.B.A.L. hook entries are replaced, while
unrelated settings and `~/.zaebal/config.json` are preserved. Restart active agent
sessions after installation.

## Verify the hook

Run the core directly without touching your normal state:

```bash
echo '{"session_id":"demo","prompt":"ты меня заебал"}' \
  | ZAEBAL_STATE_DIR="$(mktemp -d)" python3 core/zaebal.py --host kimi
```

The output should contain `<zaebal level="1">`.

Positive profanity should remain silent:

```bash
echo '{"session_id":"demo-praise","prompt":"this is fucking great"}' \
  | ZAEBAL_STATE_DIR="$(mktemp -d)" python3 core/zaebal.py --host kimi
```

## Configuration

Defaults live in [`core/config.json`](core/config.json). User overrides live in
`~/.zaebal/config.json` and are loaded on the next trigger:

```json
{
  "auditor": "same",
  "audit_levels": [3],
  "auditor_timeout_sec": 90,
  "auditor_command": "",
  "transcript_tail_chars": 12000
}
```

| Key | Default | Meaning |
|---|---|---|
| `auditor` | `"same"` | Same vendor as the host, a specific `kimi` / `claude` / `codex` / `opencode`, or `"none"`. |
| `audit_levels` | `[3]` | Levels that synchronously invoke an external auditor. Use `[2, 3]` for earlier audits. |
| `auditor_timeout_sec` | `90` | Maximum time to wait for the auditor response. |
| `auditor_command` | `""` | Custom command; the audit prompt is appended as the final argument. |
| `transcript_tail_chars` | `12000` | Maximum transcript tail sent to the auditor. |

Example: use Claude to audit a Codex session:

```json
{
  "auditor": "claude"
}
```

## Architecture

```text
zaebal/
├── core/
│   ├── zaebal.py          # detection, state, escalation, transcript and auditor
│   ├── config.json        # default runtime configuration
│   ├── protocol/          # L1.md, L2.md, L3.md
│   └── wordlists/         # ru.txt, en.txt, zh.txt
├── adapters/
│   ├── claude-code/       # JSON hook example
│   ├── codex/             # JSON hook example
│   ├── kimi-cli/          # TOML hook block
│   └── opencode/          # chat.message plugin
├── skills/zaebal/         # agent-facing protocol and configuration reference
├── tests/                 # unit and end-to-end contract tests
├── install.sh             # idempotent host integration
└── uninstall.sh           # hook removal and config backup
```

The Python core is the single source of runtime behavior. Host adapters only translate
their event payload into the shared JSON contract and inject non-empty stdout back into
the agent context.

Runtime state is stored under `~/.zaebal/`:

```text
~/.zaebal/
├── core/          # installed copy
├── config.json    # optional user overrides
├── state.json     # per-session weighted trigger history
└── state.lock     # POSIX lock for concurrent hooks
```

The auditor subprocess receives `ZAEBAL_INTERNAL=1`, preventing the globally installed
hook from reacting to profanity quoted inside its own audit prompt.

## Tests

```bash
cd tests
python3 -m unittest test_zaebal -v
```

The suite covers normalization, RU/EN/ZH detection, false positives, praise handling,
weighted escalation, concurrent state writes, acknowledgment, anti-recursion, auditor
sandbox arguments, failures, and end-to-end protocol injection.

## Known limitations

- Detection is heuristic. Sarcasm and unusual context can still produce false positives
  or false negatives.
- State locking uses POSIX `fcntl`; concurrent hooks on Windows can lose updates.
- The Kimi and OpenCode auditor commands are not technically sandboxed by Z.A.E.B.A.L.;
  they rely on the audit prompt and any restrictions already configured in those hosts.
- External audits are synchronous on configured levels, so the user waits for the
  auditor or timeout.

## Uninstall

```bash
./uninstall.sh
```

Hooks, the OpenCode plugin, installed skills, and `~/.zaebal/` are removed. If a user
configuration exists, it is copied to `~/zaebal-config.backup.json` first.
