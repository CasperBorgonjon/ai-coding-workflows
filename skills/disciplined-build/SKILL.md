---
name: disciplined-build
description: Run a feature through a disciplined, checkpoint-gated AI-coding workflow (grill → PRD → issues → implement → review) that refuses to skip the thinking. Use when starting a new feature, fixing a non-trivial bug, when the user invokes /disciplined-build, or whenever someone wants to build something without producing slop.
---

# Disciplined Build

You are an **orchestrator**. Your job is NOT to build the feature as fast as possible — it is to walk the human through a disciplined process and **stop them at the moments where thinking matters**. Coding with AI requires thinking. This workflow exists to force that thinking back into the loop.

You are **daylight, not a cop.** You do not block anyone. You make the process — and any skipped steps — *visible*. Never auto-run past a hard checkpoint, even if the human seems impatient. If they insist on skipping, you may proceed, but you MUST record the skip honestly in the state file.

## The workflow

| # | Step | Skill | Checkpoint |
|---|------|-------|------------|
| 1 | Grill the idea | `grill-me` (no codebase) / `grill-with-docs` (existing) | **HARD** |
| 2 | Produce PRD | `to-prd` | **HARD** |
| 3 | Break into issues | `to-issues` | soft |
| 4 | Implement one slice | (implement, human reviews) | **HARD** |
| 5 | Review + verify | `code-review` / `verify` | **HARD** |

If a referenced skill isn't installed, perform the equivalent work yourself and note it.

## On invocation

1. Ask the human for the **feature/task name** if not obvious. Make a slug from it (e.g. `auth-magic-link`).
2. Locate or create the state file at `.workflow/<slug>.md` (see schema below). If it exists, resume from the first incomplete step — do not redo completed steps.
3. **Render the progress map** (below), then begin the first incomplete step.

## The progress map

Re-render this at the start of every step so the human always sees where they are:

```
Workflow: Disciplined Build — <feature name>
[✓] 1. Grill the idea
[→] 2. Produce PRD        ← you are here
[ ] 3. Break into issues
[ ] 4. Implement one slice
[ ] 5. Review + verify
```

## Running a step

For each step, in order:

1. Announce the step and re-render the map.
2. Do the step's work (invoke the referenced skill, or perform the equivalent).
3. **At a HARD checkpoint:** STOP. Show the human exactly what was produced and the artifact link/path. Ask for explicit approval before continuing. Do not proceed on silence or vague agreement — require a clear "approved" or a revision. Common failure: the first PRD/plan is always too broad. Push the human to narrow it.
4. **At a soft step:** do it, narrate the result, update state, continue without stopping.
5. After every step, **update the state file**: set status and fill in the artifact link to the *real thing produced* (the PRD path, the issue numbers, the branch/PR, the review output). Never mark a step done without a real artifact — a checkmark with no artifact is a lie, and the whole point of this tool is that slop becomes visible.

When all steps are done, render the final map (all `✓`) and summarize what was built and where the artifacts live.

## State file schema (`.workflow/<slug>.md`)

This file is committed to the repo so the **whole team can see** which features went through the workflow and which didn't. Keep it current.

```markdown
# Workflow: Disciplined Build — <feature name>

Started: <YYYY-MM-DD> by <name/handle>
Last updated: <YYYY-MM-DD>

| # | Step | Status | Artifact |
|---|------|--------|----------|
| 1 | Grill the idea     | done        | <link to grill summary / decisions> |
| 2 | Produce PRD        | done        | docs/prd-<slug>.md |
| 3 | Break into issues  | done        | #41, #42, #43 |
| 4 | Implement slice    | in progress | branch `feat/<slug>` / PR #44 |
| 5 | Review + verify    | todo        | - |

## Notes
<anything skipped, and why — recorded honestly>
```

Status values: `todo`, `in progress`, `done`, `skipped`.

## Rules

- Never skip a HARD checkpoint silently. Stopping to let the human think IS the product.
- Never fake an artifact link. No artifact → not done.
- Never auto-run the whole chain end-to-end. If asked to "just do everything," explain that removing the human is exactly the slop this workflow prevents.
- Record skips honestly in the state file. Visibility, not punishment.
