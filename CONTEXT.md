# Disciplined Workflows

The shared language of this project: a tool that packages disciplined,
checkpoint-gated AI-coding workflows and the professional skills they drive.
This file is a glossary, not a spec — it defines what terms mean, not how
anything is built.

## Language

**Workflow**:
An ordered composition of skills with built-in human checkpoints, installed and
run as one unit.
_Avoid_: pipeline, flow, automation

**Skill**:
A single professional capability a workflow drives (e.g. grilling, producing a
PRD). Authored upstream; referenced and pinned, never re-authored here.
_Avoid_: plugin, command

**Cross-cutting helper**:
A skill that doesn't belong to a single step — reached for in any phase when the
situation calls (prototyping a design, diagnosing a bug, zooming out for
context), then left behind to resume the current step. Declared and pinned like
any skill, but listed apart from the ordered steps; using one never advances the
workflow or clears a checkpoint.
_Avoid_: utility, tool, plugin

**Orchestrator**:
The thin skill that sequences a workflow's steps, renders the progress map, and
enforces checkpoints. Owns no step logic — it composes skills.
_Avoid_: runner, engine

**Manifest**:
The machine-readable declaration of a workflow: its ordered steps, each step's
checkpoint type, and the pinned sources (skills and shared context) it depends
on. The single source of truth a teammate can audit.

**State file**:
The committed, per-feature record under `.workflow/` showing which steps ran and
linking each to the real artifact it produced. The team-visible proof a change
went through the workflow.
_Avoid_: log, tracker, journal

**Checkpoint**:
A stopping point in a workflow where the human must decide before it advances.
`hard` = won't proceed without explicit approval; `soft` = narrated, then
continues.

**Shared context source**:
A team-wide glossary that many projects inherit as their baseline vocabulary,
referenced at a pinned version the same way a skill is. A project's own local
glossary overrides it; it is read-only where it is inherited.
_Avoid_: platform, SharePoint, central server
