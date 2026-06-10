# PRD — Shared context source (inherit a team glossary, pinned)

> Status: draft, awaiting approval at the disciplined-build PRD checkpoint.
> Tracker is now available (`gh` authenticated, remote `CasperBorgonjon/ai-coding-workflows`),
> so on approval this is broken into real issues via `/to-issues` with the `ready-for-agent` label.
> Grill decisions: `.workflow/platform.md`. Glossary: `CONTEXT.md`. Decision record:
> `docs/adr/0001-shared-context-is-a-pinned-git-ref-not-a-platform.md`.

## Problem Statement

When a teammate grills an idea against a codebase, `grill-with-docs` sharpens the
domain vocabulary into a `CONTEXT.md`. Today that glossary is born and lives
**per-repo, per-person**: there is no way for many repos or many teams to share
one baseline vocabulary. As the team grows beyond a single workflow and a single
repo, everyone re-derives — or quietly diverges on — the same terms. The team
wants **one shared glossary they all inherit**, without standing up a hosted
platform to get it.

## Solution

A workflow can declare a **shared context source**: a separate git repo holding a
`CONTEXT.md`, pinned to a ref in `manifest.json` the exact way professional skills
are already pinned. On a project install, `install.sh` fetches that glossary to a
known path inside the repo (`.workflow/shared/CONTEXT.md`), pinned and read-only.
The orchestrator points the grilling step at it as an **inherited baseline**; the
project's own local `CONTEXT.md` **overrides** it where they disagree. Sharpening
a term still updates the *local* glossary; promoting it to the shared glossary is
a deliberate, manual PR to the shared repo.

No hosting, no accounts, no service, no UI. The shared store is "one more pinned
source," reusing a mechanism that already exists and is already tested.

## User Stories

1. As a team lead, I want to declare one shared glossary that every repo inherits, so that my teams start from the same vocabulary instead of re-deriving it.
2. As a teammate adopting a workflow, I want the install to fetch and pin the shared glossary automatically, so that I don't hunt it down or version-match it by hand.
3. As a teammate, I want the shared glossary pinned to a known ref, so that I never get a surprise "latest" vocabulary change mid-feature.
4. As an operator grilling an idea, I want the grilling step to read the shared glossary as a baseline, so that the AI challenges my terms against the team's agreed language.
5. As an operator whose project has special local language, I want my local `CONTEXT.md` to override the shared one, so that project-specific terms win over the company-wide default.
6. As an operator, I want the fetched shared glossary to be read-only in my repo, so that I don't accidentally edit a copy that a re-pin will overwrite.
7. As an operator who sharpens a term during grilling, I want that change written to my *local* glossary, so that my immediate work isn't blocked on a shared-repo PR.
8. As a vocabulary owner, I want promoting a term to the shared glossary to be an explicit PR to the shared repo, so that the shared baseline changes deliberately, not silently.
9. As a maintainer, I want the shared context source declared in the one manifest, so that I can audit or bump its pinned ref in a single place alongside the skills.
10. As a teammate, I want the install to fail loudly if the shared glossary can't be fetched or the ref is missing, so that I never get a silent partial setup.
11. As a teammate doing a global install with no project, I want the shared-glossary fetch to be skipped cleanly, so that "no project" is not an error.
12. As a maintainer, I want the shared-context behavior covered by an installer test, so that a regression in fetching/pinning is caught before release.
13. As a skeptical teammate, I want the README/EXPLAINER to show how a shared glossary is declared and inherited, so that I understand the mechanism before adopting it.
14. As a maintainer, I want a workflow with *no* shared context source to install exactly as before, so that this feature is purely additive and breaks nothing.

## Implementation Decisions

- **Manifest schema — new top-level `sharedContext` block.** Sibling to `steps`,
  not nested in a step (a glossary is not a step). Shape mirrors a skill entry:
  `{ "source": <git url>, "path": <path to CONTEXT.md in that repo>, "ref": <full SHA> }`.
  Optional: a workflow with no `sharedContext` key behaves exactly as today.
- **Installer extension, parallel to the skill loop.** `install.sh` reads
  `sharedContext`, clones `source` once (reusing the existing per-source cache),
  verifies `ref` is a real commit, `git archive`s `path`, and validates the
  marker file is present — here `CONTEXT.md` rather than `SKILL.md`. Failure
  modes reuse the existing loud-fail pattern (unreachable source, missing ref,
  missing marker file).
- **Destination = the project repo, not the skills dir.** Skills install to
  `~/.claude/skills` or `./.claude/skills`; the shared glossary instead lands at
  `.workflow/shared/CONTEXT.md` in the working repo, with a `.pinned-ref`
  alongside it (same provenance marker the skill loop writes).
- **Project-scoped fetch.** The shared glossary only makes sense against a
  specific codebase, so it is fetched on a **project** install (`--project`) and
  skipped on a bare global install — skipping is normal, not an error (story 11).
- **Orchestrator points grilling at the baseline.** `disciplined-build/SKILL.md`
  (which we own) instructs step 1 to read `.workflow/shared/CONTEXT.md` as the
  inherited baseline when present, with local `CONTEXT.md` taking precedence. The
  upstream `grill-with-docs` skill is **not** forked — it already reads
  `CONTEXT.md`; we only feed it the baseline via the orchestrator's instruction.
- **Read-only by convention + provenance.** The fetched copy carries its
  `.pinned-ref`; re-running install replaces it wholesale (same as skills), so
  local edits to it are not durable — reinforcing "edit the shared repo, not the
  copy."

## Testing Decisions

A good test here asserts **observable filesystem outcome at the installer seam** —
feed a manifest, run the installer into a temp dir, assert what landed where at
which ref. No mocks, no LLM, no internal structure.

- **Primary seam — installer integration (existing `tests/test_installer.py`).**
  Highest seam, with direct prior art: the installer test already runs
  `install.sh` against a manifest and asserts skills land at pinned refs. Extend
  it: a manifest with a `sharedContext` block pointing at a fixture git repo →
  assert `.workflow/shared/CONTEXT.md` exists, matches the fixture content at the
  pinned ref, and that `.pinned-ref` records that ref. Cover failure modes:
  missing `CONTEXT.md` at `path` → loud non-zero exit; missing/invalid ref →
  loud non-zero exit; **no `sharedContext` key → install succeeds unchanged**
  (the additive-safety story).
- **Lower seam — manifest sync (existing `tests/test_manifest_sync.py`).** Verify
  the new top-level key does not break the manifest↔SKILL.md drift check (it is
  not a step, so it should not). Adjust only if the drift checker reads top-level
  keys.
- **Orchestrator behavior (behavioral, not unit).** "Grilling reads the shared
  baseline and local overrides it" is LLM-driven and not deterministically
  unit-testable. Verified behaviorally via a scenario run, as with the existing
  checkpoint behavior — not added to the deterministic suite.

Tested module under test: `install.sh` (the resolver/installer). The validator
(`bin/validate-state-file`) and the orchestrator SKILL.md are unaffected by this
feature's deterministic surface.

## Out of Scope

- **Any hosted platform, web UI, accounts, or service.** Recorded in
  `docs/adr/0001`. The shared store is a pinned git repo, full stop.
- **Sharing ADRs.** Only the glossary (`CONTEXT.md`) is shared; ADRs are
  decisions about one specific system and stay local.
- **Assisted/automatic promotion** of a sharpened term back to the shared
  glossary. Manual PR only — auto-promotion reintroduces the "live updates"
  anti-pattern the v1 PRD rejected.
- **A library/catalog of multiple workflows, discovery, or ranking.** Each
  workflow is already its own pinnable repo; "a library" needs no new mechanism
  and the catalog is the parked marketplace.
- **Multiple shared context sources / per-context maps (`CONTEXT-MAP.md`).** v1
  inherits at most one shared glossary; composition of several is later.
- **Merge tooling between shared and local glossaries.** Precedence is "local
  overrides shared," enforced by the orchestrator's reading instruction, not by a
  merge algorithm.

## Further Notes

- This is the narrowest extension that delivers boundary-(b) sharing (many
  repos/teams, one glossary) without betting on a product — consistent with the
  v1 "build right, not bet" framing.
- The reversal trigger for the parked platform is recorded in `docs/adr/0001`: a
  real non-technical teammate blocked by git on editing the shared glossary.
- Existing artifacts touched: `skills/disciplined-build/manifest.json` (schema),
  `install.sh` (fetch), `skills/disciplined-build/SKILL.md` (grilling instruction),
  `tests/test_installer.py` (coverage), `README.md`/`EXPLAINER.md` (docs).
