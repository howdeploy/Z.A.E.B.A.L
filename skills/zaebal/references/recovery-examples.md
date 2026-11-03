# Recovery failures: anonymized examples

These are paraphrased patterns from actual recovery conversations. Names,
identifiers, dates, private paths, infrastructure details, and transcript
quotations are omitted. They illustrate failure mechanisms, not measured success
rates. Read the relevant example; this is not another mandatory checklist.

## The audit authorized work nobody requested

The user asked an agent to inspect and compare a live implementation. Both the
agent and its auditor paraphrased that as a request to deploy a fix. Saving the
paraphrase as a goal made the mistake persist, and repository changes were
published without the requested investigation being the actual deliverable.

**Break the loop:** reread the user's action words. An auditor's interpretation
cannot authorize publication. Question the proposed solution before testing it.

## A new style document erased the old structure

A redesign replaced a visual style. The agent discarded the earlier specification
entirely, including its still-required settings screens, and repeatedly checked
only the subset it had implemented. Elsewhere, two independent palettes were
merged into one and tests reinforced the unwanted merger.

**Break the loop:** identify exactly what the later instruction changed and what
must remain. Test the omitted surface or independent behavior, not just new tokens.

## Correct geometry inside the wrong model

A small navigation view repeatedly behaved differently from what the user meant.
The agent's coordinate calculations were consistent with its own interpretation,
but the reference frame was unresolved. Later clarification made the intended
behavior explicit; it was not evidence that every detail had been clear earlier.

**Break the loop:** state what stays fixed, what moves, and relative to what.
Resolve the one remaining geometric ambiguity before another implementation.

## An apology substituted for a change

After an audit restored an earlier working state, the user requested a redesign.
The agent claimed the redesign was complete even though it had only read files
since that request. A later check found no corresponding new change.

**Break the loop:** connect the claimed action to an actual artifact and result.
If existing work already meets the request, prove that; otherwise do the missing
work. Neither an apology nor a previous modification proves a new correction.

## The passing test never reached the failure

A command hung in an interactive client. A helper/RPC check passed, and the agent
reported a broader fix without exercising the interactive path. In another case,
it checked a development runtime while the user was using the packaged build.

**Break the loop:** identify the exact client, build, and failing path. Keep the
result unverified when that path cannot be checked; do not override UI permissions.

## The audit became the next loop

The user asked for a runnable preview, then asked to stop redundant tests. The
agent stopped testing but continued adding guards and requesting reviews. One
guard rejected valid explicit input outside the narrow behavior under discussion.
Even a later request for a handoff triggered another audit instead of delivery.

**Break the loop:** preserve the allowed input with a positive check, remove the
unjustified restriction, and deliver the requested available result. Each new
action must address the reported mismatch or distinguish a remaining cause.

## Repetition disappeared from the counter

Related complaints were separated by long audits, so the emotional streak expired.
A later report of the same symptom contained no profanity. The agent treated the
next audit as a fresh start instead of examining why its earlier fix failed.

**Break the loop:** compare the previous diagnosis, actual correction, and repeated
symptom regardless of the numeric level. Permission to continue is not acceptance
of the result. Use the transcript; no new task-contract store is needed.

## A diagnostic command launched the workload

An agent assumed a local test wrapper would handle `--help`. It forwarded the
argument incorrectly and launched the existing large suite. The log proved the
launch, not the later suspected cause of machine instability.

**Break the loop:** read the wrapper's dispatch before invoking it. Bound claims
to the observed result; do not turn an expensive run into an unproven crash cause.

## A second complaint was mistaken for a second failed fix

While an agent was still repairing an output artifact, the user reported another
visible defect the agent had already noticed. Elsewhere, a user accepted a text
revision and later requested stricter editing. Counting either as a completed
fix followed by a regression exaggerated the failure rate.

**Break the loop:** check chronology and what was actually claimed complete.
Distinguish an ongoing repair, a newly clarified requirement, and a repeated
failure after a claimed fix. A retrospective diagnosis is not a completion claim.

## Parameter tuning replaced an audit of the construction method

A garment was fitted by offsetting its vertices from the body. Clearance checks
could pass while its silhouette remained an unwanted tight shell. In an animation,
joint movement was approximated by deforming a single image; successive pin and
mask corrections tore neighboring regions. Later layer repairs introduced extra
cuts and invented backing pixels. Audits named local defects, but further versions
continued modifying the same construction without establishing that it expressed
the requested shape or independent movement.

**Break the loop:** identify the required cut, joints, connections and overlaps;
challenge the method on one representative region or motion phase before another
full rebuild. Preserve accepted source layers/geometry. Counts, clearances and
selected clean frames cannot establish the requested appearance. Inspect the
assembled result only when authorized, otherwise hand it over as unverified.

## A local repair lost working parts of the asset

During repeated repairs to a character, rebuilding changed its calibration,
weights, materials and physics, and a working facial controller disappeared.
A seam check passed, but it did not establish that the rebuilt asset retained
those earlier working components. Comparing the actual packages exposed the
losses; another local seam correction could not restore them.

**Break the loop:** briefly separate WORKING / BROKEN / UNKNOWN and name what
must survive. Trace the requested aspect to actual component/option diffs. Ask:
"Did I actually change that aspect, and what else changed?" Explain necessary
dependencies and narrow accidental changes without replacing the entire current
asset or reverting unrelated work. A repeated diagnosis is not a repair.

## A loaded option was not the effective runtime state

Hair-physics settings were adjusted while a runtime controller overwrote gravity.
In a related repair, disabling a collider object did not rebuild the native spring
buffer. Later plans also proposed disabling mechanisms that were already disabled
in the delivered asset. The correct package and valid bindings did not establish
which state the simulation actually consumed during the failing movement.

**Break the loop:** inspect effective values at the failure, identify later
writers and derived caches, and check the rebuild boundary. Compare before/after
options and asset data before proposing the same change again. A rest-state
correction does not prove dynamic behavior; keep that outcome unverified until
the relevant permitted inspection.

## Recovery duplicated the workload until memory ran out

An editor already held a project and its caches. A second full renderer reached
a memory stop. The agent wrote lower cache preferences and launched it again,
reaching the stop again: that headless path did not load those preferences.
The retry changed a file without establishing a reduction in the actual load.

**Break the loop:** account for existing jobs and duplicated state, then use
a suitable existing queue or a smaller bounded job when authorized. Verify that
the worker consumes the intended limits and set a cancellation/stop condition.
After overload, another attempt requires an effective load reduction. Do not
attribute a system crash to the job without evidence or stop unrelated user work.
