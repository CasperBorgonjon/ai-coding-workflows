# Workflow: Disciplined Build — Platform (store/share workflows + shared context across teams)

Started: 2026-06-10 by Casper
Last updated: 2026-06-10 (grill complete)

| # | Step | Status | Artifact |
|---|------|--------|----------|
| 1 | Grill the idea     | done        | CONTEXT.md + decisions in Notes below |
| 2 | Produce PRD        | done        | docs/prd-platform-shared-context.md |
| 3 | Break into issues  | done        | #7, #8, #9 |
| 4 | Implement slice    | done        | branch `feat/shared-context-source` (slice #7); 32/32 tests pass |
| 5 | Review + verify    | done        | two-axis review (Standards+Spec vs #7) + e2e verify run; 3 findings fixed |

## Notes

### Grill outcome (step 1)
Idea as stated was broad ("make it a platform / SharePoint"). Grilling narrowed it
hard, against the v1 PRD's own Out-of-Scope list (which had parked "platform",
"marketplace", "hosting skills" only one day earlier). Resolved decisions:

- **Real problem:** context sharpened by grilling lives per-repo; teams want one
  shared glossary, and there will be more than one workflow over time.
- **Sharing boundary = (b):** many repos/teams inherit ONE shared glossary.
  (Boundary (a) — single repo — is already solved by git; no tool needed.)
- **Goal = (A):** solve the team's problem with the least new stuff. NOT building
  a product/platform. ("Build right, not bet" — carried from v1 Further Notes.)
- **Mechanism:** a **shared context source** = a pinned git repo holding
  `CONTEXT.md`, declared in `manifest.json` and fetched by `install.sh` exactly
  like a skill (`source + ref`). No hosting, no accounts, no service. The word
  "SharePoint" was rejected — it smuggled in a hosted product.
- **Scope:** the glossary (`CONTEXT.md`) ONLY. ADRs stay local (they are
  decisions about one system, not shared language). A "library of workflows"
  needs no new mechanism — each workflow is already its own pinnable repo.
- **Consumption:** shared glossary lands at a known path, pinned/read-only; the
  orchestrator (which we own) points the grilling step at it. Local CONTEXT.md
  overrides shared.
- **Promotion = (A) manual:** grilling updates the LOCAL glossary; sharing a term
  is a manual PR to the shared repo. Assisted/auto promotion is out of scope (it
  would reintroduce the "live updates / latest" anti-pattern v1 rejected).

Glossary captured inline in `CONTEXT.md` (new this session).

### Review outcome (step 5)
Two-axis review (Matt's `review` skill) against issue #7, plus an end-to-end verify
run (real `install.sh --project` against a real glossary repo — glossary landed,
pinned to the correct SHA). Three findings fixed:
- Standards: `rm -rf "$shared"` now guarded with `${shared:?}` (mirrors the skill loop).
- Spec criterion 6 (wholesale replace): was implemented but untested → test added.
- Spec criterion 5 (missing key): raw Python traceback → clean `error:` message + test.
Rejected: forcing a `sharedContext` into the shipped manifest to satisfy criterion 8 —
disciplined-build deliberately inherits no glossary; the drift checker reads only
`steps`, so the new top-level key is structurally safe. (False positive on `repo_for`
cache reuse — `repo_for` clones on demand; proven by the verify run.)

### Scope shipped this session
Slices #7, #8, and #9 — the full feature.
- #7: install.sh fetches a pinned shared CONTEXT.md to .workflow/shared/CONTEXT.md.
- #8: orchestrator (skills/disciplined-build/SKILL.md) step 1 now reads that file as
  the inherited baseline; local CONTEXT.md overrides; sharpened terms written locally.
  Behavioral change (no deterministic test); verified by path-consistency with #7's
  producer + full suite still green. Full grill-scenario confirmation is in-the-loop.
