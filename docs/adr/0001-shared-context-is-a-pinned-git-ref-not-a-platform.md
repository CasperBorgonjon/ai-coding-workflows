# Shared context is a pinned git ref, not a hosted platform

To share a team glossary across many repos, we declare a **shared context
source** — a separate git repo holding `CONTEXT.md` — and pin it in
`manifest.json` (`source + ref`), fetched by `install.sh` exactly like a skill.
We deliberately rejected building a hosted platform / "SharePoint" (web UI,
accounts, live updates, discovery).

**Why:** the pinned-git mechanism already exists and works for skills, gives
version history, access control, and diffs for free, and preserves our core
decision to *pin* for stability. The hosted alternatives each collapsed under
prior decisions — live updates contradict pinning; a discovery catalog is the
marketplace parked in the v1 PRD; non-technical editing is the only real
advantage and has no actual user yet (the glossary is authored by the AI +
engineer, who are already in git).

**Reversal trigger:** the day a non-technical teammate must edit the shared
glossary and git is the wall — that real user, not a guess, justifies a UI.
