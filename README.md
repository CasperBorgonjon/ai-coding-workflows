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

## Use with Claude Code

Claude Code auto-discovers skills from `~/.claude/skills` (global) and `./.claude/skills` (per-project), so after install there is nothing to configure. Start a feature by asking to "build X using disciplined-build", or just describe a new feature — the skill description triggers on that.

## Use with other LLMs

The workflow is plain, portable markdown — there is no vendor-specific code in it. For any tool that doesn't auto-discover skills:

1. Paste or attach `skills/disciplined-build/SKILL.md` into the conversation context.
2. Tell the model to act as the orchestrator it describes.

Only the loading mechanism differs per tool; the workflow content is identical everywhere.

## Uninstall

Trying this should cost five minutes; leaving should cost five seconds. One command, depending on how you installed:

```sh
rm -rf ~/.claude/skills/disciplined-build    # global install
rm -rf ./.claude/skills/disciplined-build    # --project install
```

State files already committed under `.workflow/` are part of your repo's history and are deliberately untouched — they remain readable without the skill installed.

## Validate a state file

A deterministic checker (no LLM, no network) verifies that a state file isn't lying — every `done` step has a real artifact, every skip has a recorded reason:

```sh
./bin/validate-state-file .workflow/<feature>.md
```

Exit code 0 means the record is well-formed; violations are listed otherwise. Run `./test.sh` for the project's test suite.

## Status

v1 — testing with my own team. Success signal: do teammates reach for it *again, unprompted*?
