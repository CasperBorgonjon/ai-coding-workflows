# What is this, and why should you care?

A 2-minute read for a teammate.

## The problem we all feel but can't name

AI lets anyone produce code fast. But "fast" splits into two very different things:

- **Person A** asks the AI to "build the login feature," gets 300 lines, skims it, pushes it. Looks productive. Half of it is wrong in ways nobody notices until it breaks in prod.
- **Person B** makes the AI plan first, narrows the scope, builds one piece at a time, reviews each piece, runs it before pushing. Slower-looking. Actually solid.

From the outside — in the PR, in standup — **you often can't tell A from B.** Both "used AI." Both shipped something. The difference only shows up later, as slop. And it's awkward to tell a colleague "you're using AI wrong," because *how* to use it well isn't a documented skill yet. There's no manual.

## The idea in one line

> **A workflow you install that walks you through a disciplined process and stops you to think at the moments where slop normally creeps in — and makes the whole thing visible to the team.**

It's not a new AI. It's not an IDE. It's a thin layer on top of the AI tools you already use (Claude Code, etc.) that turns "vibe-coding" into an actual engineering process: **grill the idea → write a short spec → break it into pieces → build one piece → review & verify.** It refuses to skip steps, and it refuses to "just do everything" for you — because removing the human is exactly what produces slop.

**Philosophy: daylight, not a cop.** It doesn't block you or police you. It just makes the process *visible*. Each feature leaves a little committed file showing which steps were actually done (with links to the real PRD, the real review, etc.). If someone skipped everything and pushed slop, that's now visible in the repo — not a private guess.

## Concrete scenario: ticket "Add a 'forgot password' flow"

**Sam (the old way):**
> Tells the AI "add forgot-password." Gets an email-sending function, a reset endpoint, a token table, a UI form — all at once, 400 lines. Glances at it, it "looks right," pushes. In review, nobody can fully follow it. Two weeks later: tokens never expire, and the email link works in dev but not prod. Nobody decided those things — the AI just guessed, and Sam didn't notice.

**Alex (using `disciplined-build`):**
> Runs the workflow. It **stops** and grills: *"Token expiry? One-time use? Email provider — confirmed working in prod? Rate-limited so it's not an abuse vector?"* Alex answers; some of those he hadn't thought about. It writes a 1-page PRD with an explicit "out of scope" list, **stops** for Alex to approve (and narrow it). It builds **one slice** — just the token model — and **stops** so Alex actually reads it. Then the endpoint, reviewed. Then it **runs the flow** to prove the email link resolves before anything is pushed. The PR links to the PRD and a `.workflow/forgot-password.md` file showing every step was done.

Same ticket. Same AI. The difference is entirely **process** — and now that process is visible.

## What you'd actually experience using it

You start a feature, and instead of one giant dump, you get a little map that fills in as you go:

```
[✓] 1. Grill the idea
[→] 2. Produce PRD        ← you are here, it won't move until you approve
[ ] 3. Break into issues
[ ] 4. Implement one slice
[ ] 5. Review + verify
```

It pauses at the ✓-worthy moments and waits for you. That's the whole trick: the pauses are where the thinking happens. It feels slightly slower the first time and then you realize the "slow" part was just the part you were skipping before.

## Why not just "be disciplined" without a tool?

Because nobody is, reliably, under deadline pressure — and because the discipline currently lives in one or two people's heads, not in something the team can share. This packages *how the good person works* into something everyone can install and follow, and makes it obvious when it wasn't followed. Good habits become the default path instead of a thing you have to remember.

## Try it (5 minutes)

```sh
cd disciplined-workflows
./install.sh --project        # installs into this repo's .claude/skills
```
Then in Claude Code, start a small real task with "build X using disciplined-build" and watch it stop you at each checkpoint. Try to make it cheat ("just do everything") — it should refuse. That refusal is the point.

---

*Honest framing: tools that chain AI steps exist already. What's different here is the stance — deliberately keeping the human thinking instead of automating them out — and making process visible to a team. That's the bet.*
