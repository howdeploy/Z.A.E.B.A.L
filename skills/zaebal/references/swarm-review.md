# L4 — Swarm Review

Use only for a genuine L4 incident or an explicit `zaebal swarm` request. This is
a last-resort fresh assessment of the project, not permission to rewrite it from
scratch. Installing or discussing the feature does not request a swarm launch.

When complaints reach L4, the agent itself offers to assemble the swarm. The user
does not need to request it or know `zaebal swarm`. Ask which reasoning effort
and team setup to use; do not automatically set MAX or select the team for them.

## Prepare a concrete launch proposal

Do read-only preparation before asking. Identify the project roots and active
worktree/branch, the requested outcome and failed user scenario, and the last
accepted working baseline where available. Inventory the entire current diff:
working tree, staged changes, relevant commits, required untracked/generated
files, assets and options. Preserve the attribution of unrelated user changes.

Find available recent sessions belonging to this project, including neighboring
sessions that introduced the problem or attempted recovery. State the time window
and source list in the proposal; include the original request, later corrections,
complaints, previous audits and their actual follow-up actions. Do not substitute
keyword hits or the working agent's summary for the relevant full chronologies.
Missing/deleted history is a coverage gap, not evidence that nothing happened.

Offer suitable team setups with 5–7 sub-agents, recommending six reviewers plus
the current coordinator. Explain the differences in reviewer count and roles;
include model/vendor choices only where the host actually supports selecting them.
List the supported reasoning effort choices and ask which to use, including MAX
only when available. State each assignment, raw evidence scope, actual launch
capability, allowed tools/checks, concurrency/waves and a bounded time/resource budget.
Explain that this is substantially more work and may consume more paid usage;
do not invent a monetary estimate. Ask explicit permission for this particular
team and scope before launching any reviewer or external auditor. A preselected
option, silence, earlier general autonomy or `zaebal swarm` itself is not consent.
Use the host's available question mechanism in the user's language.
Ask for effort, team setup and launch consent together where practical. A single
explicit response can choose both settings and approve the concrete launch; an
answer that only chooses settings does not authorize launch. Do not ask again for
choices or launch consent already given for this concrete proposal.
If that concrete proposal has already been explicitly approved and its pass is
still active, continue within its scope; repeated hooks do not require another
approval or another team. A new pass or expanded scope needs its own decision.

## Assign independent roles

| Reviewer | Primary assignment |
|---|---|
| Task and session history | Reconstruct what the user wants, why they are dissatisfied, the first divergence, and which previous diagnosis/action failed. Distinguish changed requirements from repeated failed fixes. |
| Complete diff and provenance | Review every changed file/asset/option in the manifest and connected callers. Track requirement → actual delta → delivered artifact; identify lost working parts and unrequested changes. |
| Code, architecture and runtime | Trace the failing path and interactions, runtime identity, last writers/caches and reproducible causes. Separate implementation bugs from an unsuitable approach. |
| Design, UX and graphics | Compare behavior/appearance with the user's references and accepted decisions; inspect composition, interaction, geometry, rig/motion and output quality as relevant. Mark unavailable visual evidence unverified. |
| Software, configuration and compatibility | Review relevant versions, formats, dependencies, integration/settings, build/delivery paths, resource costs and operational limits. Verify current semantics instead of guessing flags or APIs. |
| Independent challenge and repair plan | Try to disprove the team's emerging conclusions using primary artifacts; assess the smallest complete fixes and useful refactoring, regression risks and exact outcome gates. |

Use five by combining genuinely overlapping roles, or seven for a distinct large
subsystem. Do not invent filler assignments. Start reviewers in fresh contexts
with the original words, raw locators and assigned coverage, not the coordinator's
causal theory. Each first forms an independent reading; then cross-check findings
and disagreements. All swarm members remain internal auditors regardless of vendor.
Do not relabel their results as an external `<zaebal-verdict>`.

Use the human's chosen reasoning effort and team setup for the approved reviewers.
Verify the host's supported settings; do not invent an EFFORT flag, change the
parent session silently, or claim MAX when effort cannot be selected. If a choice
cannot be applied, disclose the limitation and agree on an alternative before
launching; do not silently substitute MAX, a lower effort or a different team.
Respect slot/resource limits and run waves if needed; do not add recursive teams
beyond the approved reviewer count.
If the host cannot launch the proposed team, disclose the gap and obtain a revised
decision rather than silently presenting a solo audit as a swarm.

## Diagnose, reconcile, and repair

The team collectively covers the declared diff, project areas and recent sessions.
Track actual coverage and missing sources; a file count is not proof of review
quality. Require findings to cite a user requirement/complaint, file or artifact,
and observed failure. Keep WORKING / BROKEN / UNKNOWN explicit. Find competing
causes and a discriminating check; agreement or severity of the complaint alone
does not establish a cause. Audit earlier audits against the actions actually taken.

For each proposed change, explain what must change, what must remain, the relevant
diff/options and the exact acceptance evidence. Include refactoring where it is
needed to solve a confirmed problem; broad critique is not blanket authorization
to replace the architecture, redesign accepted UI, upgrade dependencies or delete
features. Assess design/software problems on the same evidence basis as code bugs.

Synthesize confirmed causes, unresolved disputes, missed requirements and a ranked
repair/refactoring plan. Launch approval authorizes the team and agreed diagnostic
scope. Apply repairs only if existing explicit authorization covers their concrete
scope or the user approves that plan; do not ask again for work already covered.
Assign one writer per file/asset and sequence dependent changes. Maintain the
requirement → change → outcome trace and compare against the accepted baseline.
Tests, visual inspection, external access, spending and deployment still need
their applicable authorization; include needed checks in the concrete proposal.

Finish one bounded pass. Report actual reviewers/effort, sources/coverage gaps,
evidence-backed findings, why earlier audits failed, the repair plan, changes
actually made and verified/unverified outcome gates. Deliver a concise synthesis
with artifact/report links where available; do not dump seven unreconciled verdicts
or automatically start another swarm. A counter reset is not proof of a fix.
