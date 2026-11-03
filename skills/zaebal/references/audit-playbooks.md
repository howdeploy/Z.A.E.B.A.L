# Audit playbooks

Use one primary playbook and any secondary playbook that the failure crosses. Do not run every check mechanically. The common output is:

1. `CONTRACT` — the user's words, relevant later corrections, and the agent's added assumption. This interpretation is provisional; do not freeze it or treat a saved goal/auditor's paraphrase as authority.
2. `DIVERGENCE POINT` — earliest relevant conversation turn (quote plus timestamp/order), the mismatch introduced there, and the corresponding diff/commit evidence. If history is incomplete, use `not established`.
3. `FACTS` — each fact names a conversation or repository artifact.
4. `HYPOTHESES` — at least two competing causes unless direct evidence is conclusive.
5. `DISCRIMINATING CHECK` — smallest check that could disprove the explanation, its expected results, and the next action that changes because of the evidence. During a read-only stop, inspect existing evidence only; prescribe any new run/mutation as a post-ack next check.
6. `PREVIOUS AUDIT` — earlier claim → action actually taken → repeated symptom. Do this even without a new profanity trigger or after the streak resets/expires. Distinguish new requirements and work still in progress from a failed fix. Without new evidence, change approach instead of repeating the audit.
7. `WRONG BELIEF` — established only after that check; otherwise `not established`.
8. `STATUS` — `CONFIRMED`, `PARTIAL`, `UNVERIFIED`, or `DISPROVED` for the diagnosis only. Missing information, changed conditions, and environment limits need no invented wrong belief.
9. `OUTCOME GATE` — exact user-visible artifact; result separately verified, partial, or unverified. Explicitly check: did the actual file/option/asset delta change the requested aspect and preserve the working baseline? A proxy test is intermediate evidence. Deliver an available result or requested handoff without unrelated cleanup or further audits once relevant required checks pass. Respect permissions and UI-test restrictions.

For every playbook, inspect the session chronology before interpreting runtime artifacts. Map request/decision/action turns to working-tree and staged diffs and to timestamped commits. Context explains why an artifact exists; the artifact proves what actually changed. Neither evidence track may replace the other.

Before a repair, briefly separate `WORKING / BROKEN / UNKNOWN` with sources. Trace
each requirement to the intended aspect, actual diff/options/asset changes, and
outcome evidence. Read back the final delta, including generated data. Identify
any unrequested changed aspect and distinguish necessary dependencies from
accidental deviations; preserve unrelated user work. Keep this within the existing
audit output, not a separate project-management record.

## Code and runtime

Use for bugs, tests, services, containers, deploys, and “works locally but not for the user.”

- Reproduce the exact failing path, not a nearby unit or helper.
- Find callers of the function you would change and trace the shared path. Check that the proposed fix rejects the reported failure while preserving valid sibling behavior; do not delete a feature or add unrelated guards to satisfy the test.
- After one command failure, read a local wrapper's dispatch before invoking even `--help`, then consult installed-version help/documentation instead of guessing flags.
- Find the conversation turn that selected or justified the failing implementation, then match it to the diff/commit that introduced it.
- Map the request to the process that actually handles it. Enumerate duplicate local and in-scope server processes, containers, ports, routes, images, worktrees, and credentials.
- Compare source → built artifact → installed/deployed artifact by version or hash.
- Compare effective options before/after at the failing moment. Trace the last writer and any derived cache; initialization values can be overwritten by controllers or later events. Check whether the proposed change is already in effect.
- Treat a passing unit test, green healthcheck, or quiet log as intermediate evidence only.
- Outcome gate: the original failing request succeeds against the exact serving runtime.

Example: “the new code is deployed” is a hypothesis until the process receiving a traced request reports the intended commit/image and produces the corrected response.

## Config, hooks, instructions, and environment

Use for AGENTS.md, skills, hooks, config files, PATH, env variables, and startup settings.

- Find the active home/config root, including overrides such as `KIMI_CODE_HOME` or container env.
- Match the conversation's claimed target path and reload assumption to the actual config diff and commit chronology.
- Prove the host parsed and registered the entry with its own diagnostics/list command.
- Identify reload semantics: immediate, new process, new session, or full restart.
- Compare the config diff with effective values through the failing transition, including precedence, later writes and cached state. A parsed option can still be overridden or require a cache rebuild.
- Run a unique canary through the host boundary and find the corresponding hook/log/incident artifact.
- Outcome gate: the target process consumes the intended value and changes behavior.

Example: a TOML block existing under `~/.kimi-code` does not prove Kimi loaded it when `KIMI_CODE_HOME` points elsewhere.

## Git and remote state

Use for commits, pushes, branches, PRs, and “my changes disappeared.”

- Record worktree status, current branch, upstream, remotes, and ahead/behind state.
- Align commit timestamps and diffs with the session turn that requested or claimed each change; do not infer intent from Git alone.
- Distinguish working-tree content, index content, local commit, remote branch, and PR head.
- Verify the remote object after push (`ls-remote`, provider API, or fresh fetch), not only the local command's exit code.
- Check that ignored/untracked/generated files required by the contract are actually included.
- Outcome gate: the requested commit/content is reachable from the exact remote ref or PR the user named.

## Content and specification

Use for articles, prompts, plans, translations, summaries, structured output, and literal formatting constraints.

- Build a requirement → output-evidence table. Include voice, audience, length, format, forbidden material, and every literal constraint.
- Trace each requirement to the first session turn where it was accepted, changed, omitted, or contradicted.
- A later style change does not automatically cancel an earlier structural requirement. A genuine later clarification is not a retroactive violation. For geometry, identify what stays fixed, what moves, and the reference frame before judging the implementation.
- Separate source-backed claims from invented claims. Flag fabricated first-person experience, metrics, quotes, links, or product behavior.
- Compare action density with introductory/background “water”; ensure the deliverable starts where the user asked it to start.
- Verify physical formatting when relevant (one line, JSON schema, headings, character limit), not just semantic intent.
- Outcome gate: every requirement has a concrete location in the final artifact and no unsupported claims remain.

## Active context

Use when multiple workflows, models, branches, hosts, tabs, files, servers, or user personas are in play.

- Quote the last explicit selection and timestamp/order: workflow, model/checkpoint, branch/worktree, host, tab, target file, account, or environment.
- Start from the original request and find the earliest unapproved context switch, then match it to subsequent file or commit changes.
- Compare it with the target of every subsequent action. Do not infer a switch from convenience or recency.
- When UI and filesystem disagree, inspect both and identify which one the action actually mutated.
- Outcome gate: the final artifact comes from the explicitly selected context, or the user explicitly approves a switch.

## Graphics, 3D models, and motion

Use for image layers/masks, mesh and garment edits, rigs, materials, animation,
and asset conversion. Read the relevant [recovery examples](recovery-examples.md)
when local repairs keep damaging the result.

- Audit the construction method before adjusting more parameters. Identify which parts must stay rigid, deform, overlap or remain connected. Check that the chosen layers, topology, rig or simulation can express that behavior. Offsetting a garment from skin does not by itself construct its cut and folds; deforming one image does not by itself provide independent joints. Procedural work is valid when it preserves the required structure.
- Identify the accepted baseline and the exact region/property to change. Preserve its required geometry, UVs, materials, weights, shape keys and controllers. For recovery, compare component-level deltas and restore only affected data; an entire older scene can erase later work.
- Read the relevant target-format and application semantics. Distinguish raw mesh, evaluated deformation and exported/runtime state; inspect option precedence and cache rebuild requirements before copying parameters between them.
- Match each check to the claimed property. Vertex/bone counts, connected topology, no detected intersections, or a clean rest pose do not establish anatomy, silhouette, fabric construction, material appearance or motion quality.
- When inspection is authorized, inspect the assembled result in the relevant views and motion phases, including coupled regions and seams. Selected clean close-ups cannot establish that the whole assembly is clean. Use a representative part/pose to challenge the method before repeating a full rebuild. If visual inspection is unavailable or reserved for the user, leave that result unverified and hand over the exact artifact.
- Outcome gate: the requested defect is corrected in the reviewed artifact while the accepted form and required motion remain intact. Static and dynamic results need separate evidence when both matter.

## Stochastic and gen-media pipelines

Use for image, audio, video, LLM sampling, and any non-deterministic output.

- The user's bad output is a `FACT` about the symptom. Its cause remains a `HYPOTHESIS`.
- Capture the exact workflow file/hash, seed, input, checkpoint/model, VAE/encoder, LoRA stack and weights, sampler/scheduler, steps, CFG, dimensions, and post-processing.
- Confirm the workflow that executed, not merely the workflow open in the UI.
- Inspect existing same-seed A/B artifacts that change one variable at a time. If none exist, keep causality `UNVERIFIED` and prescribe the A/B as a post-ack next check. If determinism is unavailable, the later run needs a declared sample size and distribution comparison rather than cherry-picked outputs.
- Do not claim “LoRA caused it,” “CFG is too high,” or similar causality without A/B or direct artifact evidence.
- Outcome gate: a controlled comparison improves the named defect without regressing the user's other constraints.

## UI and external state

Use for browser/UI operations, dashboards, third-party APIs, messages, uploads, and settings changed outside the repository.

- Record the target identity (account, workspace, page/object ID) before mutation.
- After mutation, reload or read back through an independent path; stale local UI state is not proof.
- Capture a screenshot, API response, object version, delivery receipt, or server-side log tied to the target.
- Distinguish “click succeeded” from “state persisted” and “request accepted” from “downstream effect completed.”
- Outcome gate: an independent read confirms the intended external state for the exact target.

## Recovery workload

Use when diagnosis or retries involve renders, builds, batch workers, benchmarks,
or other expensive jobs. This checklist does not authorize their execution.

- Account for jobs already running and whether another process duplicates the editor's project and caches. Prefer an existing suitable queue over another full copy when it meets the task.
- Before a permitted run, choose the smallest useful workload, a concurrency/memory budget, a cancellation path and a stop condition. Leave capacity for the user's active work; do not stop unrelated jobs.
- After overload or a memory stop, establish a relevant reduction before retrying: fewer workers, a smaller case, less duplicated state, or an effective supported limit. Confirm what the worker consumes; a written preference or environment variable alone is insufficient.
- Outcome gate: the next check stays within its declared budget and produces evidence for the reported defect. A completed benchmark alone does not establish that the user's problem is fixed.
