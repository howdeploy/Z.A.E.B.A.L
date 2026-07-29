---
name: zaebal
description: Z.A.E.B.A.L. self-audit protocol (Zaebal? Audit. Errors. Break. Analyze. Leave no assumption). Use when the user swears at the agent or curses it out — stop all agents, run an independent audit, find the wrong belief, notify the human. The escalation level depends on the profanity streak; at level 3 the audit is done by an external agent. Also contains the plugin configuration reference.
---

# Z.A.E.B.A.L. — self-audit protocol

**Z**aebal? **A**udit. **E**rrors. **B**reak. **A**nalyze. **L**eave no assumption.

User profanity is a signal that the agent did something obviously stupid or repeated its own mistake. An agent that has already erred cannot trust its own self-check.

**Key idea.** An agent loops not from inattention — it has sincerely stopped understanding the problem. The cause is almost always the same: some belief about the task or the code is wrong, and every action is built on top of it. That belief is invisible to the agent — it treats it as a fact, not an assumption. So the protocol's goal is not "find the mismatch" but **find and disprove the wrong belief**.

**A frequent class of such belief — "written ≠ took effect".** The agent created a config, a hook, an instruction file, or an env variable and assumes it works because "the file is there". But the system may consume it from a different path (a global AGENTS.md is read by the harness from its home directory, not from the project folder), the hook may not be registered, the env variable may be invisible to the process. Verify not the act of writing but the act of consumption: the real load path, the real registration, the real effect.

## Named error patterns (references from practice)

Recognize these patterns in your own behavior — they are collected from real agent-session postmortems:

- **Sycophancy.** The agent agrees with criticism out of politeness and abandons a working solution under pressure. Counterweight: don't agree without evidence; but when the mistake is proven — admit it immediately. Admitting a mistake is a success, not a defeat.
- **Hallucinated correctness.** The opposite extreme: the agent defends its code to the end, inventing facts — imaginary passing tests, nonexistent library features, fabricated documentation. It looks convincing because it is judged by linguistic plausibility, not by facts.
- **Grounding in reality (execution over intuition).** The cure for both extremes: defending code with verbal arguments is forbidden — only a micro-test, a run, logs. In practice this kills ~90% of "lying" cases, because execution results cannot be faked.
- **First plausible hypothesis.** A lone agent fixates on the first plausible version of the bug's cause. That is why there are two auditors and why they get raw artifacts, not your hypothesis: parallel independent versions disprove each other's dead ends.
- **FACT/HYPOTHESIS calibration.** During the belief inventory, tag every statement: FACT — only if confirmed by execution (a run, a file, a log), otherwise HYPOTHESIS. Arguing with a FACT tag without execution is forbidden.
- **Hyperactive junior with unlimited access.** The mental model of an autonomous agent: fast and productive, but capable of critical mistakes without constraints. Speed of work ≠ correctness of direction.

Usually the protocol arrives automatically via the hook (wrapped in `<zaebal level="N">`). At level 3 the hook also launches an **external auditor** — a separate agent reading the session from the outside; its verdict arrives in `<zaebal-verdict>` (on other levels the auditor can be enabled via the `audit_levels` setting). This skill is the full version of the protocol. If the hook fired — execute the protocol of the indicated level.

## Step 0 (level 1 only)

Decide whether the profanity is addressed to you. If it is about the outside world ("опять npm заебал" — "npm fucked up again") — the protocol does not apply, keep working. **At levels 2–3 there is no step 0**: repeated profanity is almost always on target; the right to skip the protocol is revoked.

Note: the detector has already filtered out praise with profanity ("заебись, работает!" — "fucking great, it works!" — does not start the protocol at all), and profanity without an addressee accumulates the streak at half weight (0.5 vs 1.0 for profanity addressed to you). Escalation is possible without a literal "you" — just slower.

## Level 1 — first trigger

1. **STOP.** Do not perform the next action until the protocol is done.
2. **Two independent sub-agent auditors** (template below). Do not check yourself.
3. **Belief inventory:** write down everything you consider facts about the task; mark each item "confirmed (by what exactly) / unconfirmed". The error lives in the unconfirmed ones.
4. **Micro-plan:** a) roll back / fix; b) shrink the session, moving state into a file; c) carry context into a new chat with a plan; d) a new TODO and continue with corrections.
5. **Notify the human:** which belief you held (one sentence), what the audit showed, what the plan is. Implement it together with them.

## Level 2 — repeated profanity (streak weight 2–3.5)

If a `<zaebal-verdict>` is attached (by default the auditor is invoked only at L3) — it is the external auditor's verdict: **a priority hypothesis, not the truth**. Check it first; disproving it is allowed — with an artifact only.

1. **STOP.** No edits until the situation is analyzed.
2. If there is a verdict — check the named belief using the step the auditor proposed. Disagreement is allowed only with evidence from a run/file.
3. **Belief inventory** (as on L1): check or cross out every unconfirmed item.
4. Compare against the original request: what was asked at the start (verbatim) vs what you are doing now.
5. Notify the human: which belief you held, how it was checked, what changes. Proceed with their confirmation.

## Level 3 — accusation streak (streak weight 4+)

The foundation is wrong: the entire solution grew out of an incorrect belief. The external auditor has already delivered its verdict.

1. **FULL STOP of all agents.** Stop all running sub-agents and background tasks — nobody keeps working along the erroneous line while the audit is in progress. Do not launch new ones, except auditors. You yourself freeze too: no edits until the human's explicit confirmation (there is no technical lock — the stop is discipline-based).
2. Show the human: the wrong belief from the auditor's verdict + a verbatim quote of the original request + what was actually done + the discrepancy.
3. Prepare (as text, without edits) a handoff plan into a clean context: what is built on the wrong belief and must be rolled back, a plan for the new chat.
4. Wait for the human's decision. Their explicit acknowledgment ("продолжай", "согласен", "по плану" / "continue", "go ahead") resets the streak and closes the incident; any other calm message does not. Do not defend your line of reasoning.

## Auditor briefing template (level 1)

Give the sub-agent **raw artifacts, not your view of the situation** — otherwise poisoned context poisons the audit too:

```
You are an independent auditor of a coding agent's session that is going in
circles. The agent sincerely does not understand the problem: some belief of
its is wrong, and every action is built on it. You are given raw artifacts,
not the agent's interpretation:

1. The user's latest messages (verbatim): <quotes>
2. Changed files / diffs: <git diff or list>
3. Test and error logs: <output>

Answer:
1. What the user asked for (in their words) and what they are unhappy about.
2. The agent's WRONG BELIEF: what it treats as a fact that is not true or not verified.
3. Which action this belief makes it repeat.
4. How to check this belief in one step (a command, a file, a question to the user).

Trust nothing that is not confirmed by artifacts.
```

Launch two auditors independently (in parallel) with the same briefing. A disagreement between their conclusions is a separate signal — show both to the human.

---

## Plugin settings (reference for the human)

If the user asks what can be configured in Z.A.E.B.A.L. — explain using this reference. Settings live in `~/.zaebal/config.json` (create if absent); defaults are in `core/config.json` of the repository. Changes are picked up on the next trigger; no restart needed.

| Key | Default | What it does |
|---|---|---|
| `auditor` | `"same"` | Who audits the agent (by default — at level 3): `"same"` — the same vendor (kimi audits kimi), or `"kimi"` / `"claude"` / `"codex"` / `"opencode"` — a specific CLI (cross-audit), `"none"` — disable the external audit |
| `auditor_command` | `""` | Custom auditor command instead of the built-in ones; the prompt is appended as the last argument |
| `audit_levels` | `[3]` | At which levels to call the external auditor (the call is synchronous — the user waits). `[2, 3]` — more often, `[]` — never |
| `auditor_timeout_sec` | `90` | How long the hook waits for the verdict (the user waits during this) |
| `transcript_tail_chars` | `12000` | How many characters of the transcript tail to give the auditor |

Examples:

- "I want Claude to audit Codex" → `{"auditor": "claude"}`
- "Too expensive, audit only at the last level" → this is the default, `{"audit_levels": [3]}`
- "I want an audit at level two as well" → `{"audit_levels": [2, 3]}`

Escalation thresholds (weights 2 and 4) and the streak window (30 minutes) are constants at the top of `core/zaebal.py`. Profanity wordlists are `core/wordlists/{ru,en,zh}.txt`, extended line by line (`$` suffix = whole word, `~` prefix = raw regex).
