# PRD — Disciplined Workflows v1 (team-adoptable)

> Status: draft. Tracker not configured (repo is not yet under git, no issue-tracker vocab available),
> so this PRD lives as a file. When a tracker + `git init` exist, run `/to-issues` against this and
> apply the `ready-for-agent` label.

## Problem Statement

I want my team to work with AI in a disciplined, consistent way — using *professional, proven* skills, not homemade imitations — so that we stop shipping slop and can tell, from the outside, who actually followed a real process.

Today three things block that:

1. **Adoption is fragile.** My `disciplined-build` orchestrator references professional skills (the Matt Pocock pack: grilling, PRD, issues, review/verify), but installing the workflow only installs *my orchestrator*. If a teammate doesn't already have the professional skills, the workflow silently falls back to a weaker, home-grown version of each step. That "my version" fallback feels unprofessional and undermines trust in the whole thing.
2. **The process can be faked.** The committed state file can mark a step `done` with no real artifact behind it. A checkmark that can be lied about proves nothing — which defeats the "make slop visible" purpose.
3. **It's not yet shareable.** The project isn't under version control, so the per-feature state files can't become the team-visible artifact the design depends on.

## Solution

A single, installable workflow that a team adopts together. Installing it:

- **Brings the professional skills with it**, pinned to a known-good version, so the orchestrator always drives the *real* professional skills — never a degraded local imitation.
- **Walks the operator through the disciplined process** (grill → PRD → issues → implement → review/verify) with hard human checkpoints that won't advance without a decision, and that refuse to auto-run end-to-end.
- **Records a committed, _validated_ state file** per feature, in which a step can only be `done` if it links to the real artifact it produced — enforced by a deterministic validator, not by trust.

The orchestrator stays thin on purpose: it is the disciplined *composition* of professional skills plus the visibility layer. The professional skills are the engine; this is the seatbelt and the dashboard. Philosophy throughout: **daylight, not a cop** — never block, always make the process (and any skips) visible.

## User Stories

1. As a team lead, I want every teammate to install one workflow that brings the professional skills with it, so that we all run the same proven steps instead of personal improvisations.
2. As a teammate adopting the workflow, I want the install to fetch and pin the professional skills it depends on, so that I don't have to hunt down and version-match them myself.
3. As a teammate, I want the workflow to drive the *real* professional skills (not a built-in imitation), so that the quality matches what the original skill authors intended.
4. As a teammate with a missing dependency, I want the workflow to tell me exactly which professional skill to install, so that I never silently get a degraded experience.
5. As an operator starting a feature, I want the workflow to grill the idea before any code, so that hidden decisions surface before they become bugs.
6. As an operator, I want a hard stop after grilling that won't proceed without my explicit approval, so that I actually think instead of rubber-stamping.
7. As an operator, I want a short PRD produced with an explicit out-of-scope list, so that the first draft is narrowed instead of ballooning.
8. As an operator, I want the issues step to run without stopping me, so that mechanical work doesn't add friction.
9. As an operator, I want a hard stop to review each implemented slice, so that I read the code instead of trusting it.
10. As an operator, I want the workflow to actually run/verify the result before finishing, so that "it compiles" never substitutes for "it works."
11. As an operator who tries to shortcut, I want the workflow to refuse "just do everything," so that the human is never automated out of the loop.
12. As an operator who deliberately skips a step, I want the skip recorded honestly in the state file with a reason, so that the record stays truthful.
13. As a reviewer on a PR, I want to see a committed state file showing which steps were done and links to their artifacts, so that I can tell a disciplined change from a slop dump.
14. As a reviewer, I want a step marked `done` to be guaranteed to have a real artifact, so that I can trust the checkmarks without re-verifying each one.
15. As a teammate, I want the state file validated automatically, so that a faked or malformed record is caught rather than believed.
16. As a maintainer, I want the workflow's dependencies declared in one manifest, so that I can update or pin the professional-skill versions in a single place.
17. As a user of a non-Claude tool, I want the workflow content to be plain portable markdown with a documented way to load it, so that the discipline isn't locked to one vendor.
18. As a new adopter, I want a one-command install (and a documented uninstall), so that trying it costs five minutes.
19. As a team, I want the project under version control with the state files committed, so that the process record is shared and durable.
20. As a skeptical teammate, I want a short explainer with a concrete before/after scenario, so that I understand *why* before I'm asked to change how I work.

## Implementation Decisions

- **Workflow manifest.** Introduce a machine-readable manifest for a workflow: an ordered list of steps, where each step declares its required professional skill (name + source URL + pinned version/ref) and its checkpoint type (`hard` | `soft`). The orchestrator's prose map is generated from / kept consistent with this manifest.
- **Dependency-installing setup.** The installer reads the manifest and installs the declared professional skills (Matt Pocock pack) alongside the orchestrator, pinned to a known-good ref for stability (the Q5 "pin a copy" decision). Source skills live upstream; we reference and pin, we do not re-author them.
- **Remove the degraded fallback.** Drop the "if a referenced skill isn't installed, perform the equivalent yourself" instruction from the orchestrator. Replace with: on a missing dependency, surface exactly which skill to install and how — never silently substitute a home-grown version.
- **State file (`.workflow/<slug>.md`).** Committed per-feature record. Schema unchanged from the prototype: a step row may be `done` only with a non-empty artifact reference; statuses are `todo | in progress | done | skipped`; skips require a reason in Notes.
- **State-file validator (the deterministic gate).** A standalone checker: input = state-file text, output = pass or a list of violations. Violations include: `done` with empty/`-` artifact, invalid status, missing required sections, `skipped` without a reason. This is the embodiment of "determinism comes from gates, not prompts." It is independent of any LLM and is the tracer-bullet for later CI gating and the (parked) proof layer.
- **Distribution.** `git init` the project; adopt via `git clone` + `install.sh` (global or `--project`). A thin `npx`-style entry point is a later nicety, not v1.
- **Tool portability.** Workflow content remains plain markdown. Document the per-tool loading adapter (Claude Code auto-discovery; paste/attach for other LLMs). No code investment in multi-tool loaders for v1 beyond documentation.

## Testing Decisions

A good test here checks **external behavior at the highest seam**, not internal structure — feed an input artifact, assert the observable result. Seams, highest first:

- **Seam 1 — State-file validator (unit, deterministic).** Primary test target. Given state-file text, assert the exact set of violations (or pass). Cover: `done`-without-artifact, invalid status, `skipped`-without-reason, well-formed file passes. This is pure input→output, no mocks, no LLM.
- **Seam 4 — Dependency resolution + installer (integration).** Run the installer into a temp dir; assert the orchestrator *and* every manifest-declared professional skill land at the expected paths, at the pinned ref. Prior art: the manual `install.sh --project` / fake-`HOME` runs already done this session.
- **Seam 3 — Orchestrator behavior (scenario / behavioral eval, not unit).** The checkpoint-stopping and auto-run-refusal behavior is LLM-driven and not deterministically unit-testable. Verify via the adversarial scenario: instruct it to "just do everything" (expect refusal) and to "skip the PRD" (expect it proceeds but writes `skipped` + reason). Prior art: the cooperative `/tmp/health-demo` run this session covered the happy path (8/10 rows); the adversarial run covers rows 9–10.

Tested modules: the validator (Seam 1) and the installer/resolver (Seam 4) are the code under test. The orchestrator SKILL.md is validated behaviorally, and indirectly through the validator (its output — the state file — must pass).

## Out of Scope

- The **app/IDE pivot** (owning the model UI). Parked; "determinism via gates" is being captured by the validator instead, without a full app.
- A **thin wrapper/CLI that owns prompt assembly** (the "(B)" option). Not v1; revisit only if the markdown skill's soft enforcement proves insufficient in practice.
- **Hosting or authoring skills** on a platform (playlist→library). Reference + pin only for now.
- The **measurement / proof layer** (using state files as evidence of who works well). Parked; the validator is its precondition.
- **CI hard-gating** that blocks PRs. Opt-in team policy at most, later — never the default.
- A **public marketplace, accounts, discovery, ranking**. Team-scope only for v1.

## Further Notes

- Honest framing carried from design: the win condition is "great learning + a tool my team actually re-uses unprompted." Startup is a real but low-probability upside, kept alive by building right, not by betting on it.
- Pass/fail signal for the whole effort remains behavioral: do teammates reach for the workflow *again, unprompted*?
- Existing artifacts: orchestrator at `skills/disciplined-build/SKILL.md`, concept/install at `README.md`, teammate pitch at `EXPLAINER.md`, design of record in the project memory (`disciplined-workflow-platform.md`).
