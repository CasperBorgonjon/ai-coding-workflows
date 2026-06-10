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

No clone needed — one line (requires `git` and `python3`):

```sh
curl -fsSL https://raw.githubusercontent.com/CasperBorgonjon/ai-coding-workflows/main/bootstrap.sh | bash
```

Add `-s -- --project` after `bash` to install into `./.claude/skills` (current repo only) instead of `~/.claude/skills` (global).

Or from a clone:

```sh
./install.sh            # installs into ~/.claude/skills (global)
./install.sh --project  # installs into ./.claude/skills (this repo only)
```

Installing brings the **professional skills the workflow drives along with it** — fetched from their source repos at the exact commits pinned in the [manifest](#workflow-manifest), never "latest". Re-running is safe and idempotent; if a source is unreachable, the install fails loudly rather than leaving you with a silent partial setup. Requires `git` and `python3`.

## Workflow manifest

The workflow's dependencies are declared in one place: `skills/disciplined-build/manifest.json`. It lists the five steps in order and, for each, the checkpoint type (`hard` | `soft`) and the professional skills the step drives — each with its source repo, path, and a pinned commit SHA (the upstream publishes no tags, so a full SHA is the only real pin). A teammate can audit exactly which skill versions the team runs by reading this one file; bump a version by editing its `ref`.

- **Format:** JSON, because the installer (bash) parses it with python3's stdlib — already a dependency via the validator — so no extra tooling. The file is small enough that JSON's verbosity doesn't hurt auditability.
- **Consistency:** the manifest is the source of truth. The prose step table in `SKILL.md` is hand-written, and a drift test in `./test.sh` fails whenever the two disagree on step names, order, checkpoint types, or skill names.

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

The professional skills the installer fetched (`grill-me`, `grill-with-docs`, `to-prd`, `to-issues`, `review`, `improve-codebase-architecture`) are useful on their own, so uninstalling the workflow leaves them in place. To remove those too:

```sh
cd <skills dir>  # ~/.claude/skills or ./.claude/skills
rm -rf grill-me grill-with-docs to-prd to-issues review improve-codebase-architecture
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
