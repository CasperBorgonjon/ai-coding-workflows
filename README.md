# Disciplined Workflows

Installable, disciplined AI-coding workflows that refuse to skip the thinking.

## The problem

AI lets anyone generate code fast — and a lot of it is slop: unreviewed, unplanned, pushed and forgotten. The tooling that exists mostly pushes toward *more automation* (fire-and-forget pipelines). This goes the other way: it keeps the human in the loop at the moments that matter.

## The idea

A **workflow** is not a single skill — it's an ordered *composition* of skills with built-in human checkpoints. You install a workflow, and it walks you through a disciplined process, stopping you to think (and approve) at the points where slop normally creeps in.

**Philosophy: daylight, not a cop.** The tool doesn't block anyone. It makes the process — and any skipped steps — *visible*, via a committed state file the whole team can see. Norms, not walls.

## v1: `disciplined-build`

One workflow, for building a feature without slop:

1. **Grill the idea** — interrogate the plan until it's sharp. *(hard stop)*
2. **Produce a PRD** — turn it into a spec; narrow the too-broad first draft. *(hard stop)*
3. **Break into issues** — mechanical once the PRD is approved.
4. **Implement one slice** — you review each slice. *(hard stop)*
5. **Review + verify** — run it, don't just trust the tests. *(hard stop)*

Progress is shown live as a map, and recorded in `.workflow/<feature>.md` — committed so the team can see what went through the workflow and what didn't. Each step links to the *real artifact* it produced (PRD, issues, PR, review output); a checkmark with no artifact is a lie.

## Install

```sh
./install.sh            # installs into ~/.claude/skills (global)
./install.sh --project  # installs into ./.claude/skills (this repo only)
```

Then in Claude Code, start a feature with the `disciplined-build` skill (e.g. ask to "build X using disciplined-build").

> The skill is plain markdown. It also works with other LLMs — paste `skills/disciplined-build/SKILL.md` into the context; only the loading mechanism differs.

## Status

v1 — testing with my own team. Success signal: do teammates reach for it *again, unprompted*?
