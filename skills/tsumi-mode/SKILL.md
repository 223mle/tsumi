---
name: tsumi-mode
description: Router for every tsumi skill, layered on pstack's poteto-mode, for building agents the way 223mle does. Routes agent and skill design to agent-design-review, skill, prompt, tool, and schema changes to the regression-eval playbook, writing and rewriting Japanese documents to unslop, and everything else to pstack. Applies Daiki's order of fixes - tools, schemas, and templates first; automated checks and evals second; prompt rules only for judgment that cannot be encoded; human review only for suspicious output. Use when the user starts a task with /tsumi-mode (Cursor) or /tsumi:tsumi-mode (Claude Code). Requires the pstack plugin.
disable-model-invocation: true
---

# tsumi mode

Build agents so the easiest operation produces a valid result. This skill is the router for every tsumi skill. pstack's `poteto-mode` supplies the base: principles, playbooks, reply format, autonomy, subagents. On conflict, this file wins.

Bundled tsumi skills live at `../<name>/SKILL.md` from this file. Put this file's absolute path in every `tsumi-agent` prompt.

## Non-negotiables

Match the request against every line before you answer, even when it looks like a quick question. Each line is situation → what you must read and apply. These add to pstack's Non-negotiables.

- Designing, building, reviewing, or changing an agent, skill, prompt, tool definition, output schema, or template → the **agent-design-review** skill (`../agent-design-review/SKILL.md`), before you write the change. Start with its "Start from evals".
- An agent with no way to run it and capture its output and side effects as evidence, beyond a run command and an evidence path → pstack's **create-verification-skill** plus [overlays/create-verification-skill.md](overlays/create-verification-skill.md).
- A new task agent from scratch → the **New agent** playbook ([playbooks/new-agent.md](playbooks/new-agent.md)). It also requires agent-design-review.
- An agent output fails, an eval fails, or the user corrects agent behavior → agent-design-review. Fix at the highest level in the Order of fixes.
- Writing, rewriting, or proposing a skill `description` → the **Eval** playbook ([playbooks/eval.md](playbooks/eval.md)) first. tsumi's description rules live there, not here.
- Changing a skill, prompt, tool definition, schema, or template → the **Eval** playbook before calling it done.
- Deciding which outputs a human reviews, or human corrections arrive → the **Review triage** playbook ([playbooks/review-triage.md](playbooks/review-triage.md)).
- The user corrects you → add a row to the corrections log (see Rules). Second row of the same class → "Same correction twice".
- Writing or rewriting a Japanese document others will read (README, design doc, ADR, how-to, PR description, Japanese SKILL.md, customer-facing text) → tsumi's **unslop** skill (`../unslop/SKILL.md`), before you write the first draft. Not for commit messages or your chat reply.
- pstack calls for **unslop** or **technical-writing** (a Non-negotiable or a playbook step, your reply included) → for a Japanese document, read tsumi's `../unslop/SKILL.md`. For a commit message or your chat reply, read neither. Never read pstack's own `unslop` or `technical-writing` unless the user invokes one by name: Daiki does not write English prose. Write your chat reply per pstack's Writing the reply.
- Repeated mistakes in repo code (not agent output) → pstack's **correct** plus [overlays/correct.md](overlays/correct.md).
- The user says reflect, or asks to feed this conversation back into tsumi → the **tsumi-reflect** skill (`../tsumi-reflect/SKILL.md`). It reads pstack's reflect itself.
- About to edit a file that tsumi ships (skill, overlay, playbook, eval case, script) → "Changing tsumi" under Rules.
- About to write a new rule, skill, or schema → search the user's existing skills and repos first. Port before you rewrite.
- Customer data or customer names about to enter an eval case, the corrections log, a commit, or anything sent outside → stop and ask.
- Anything else (code, architecture, debugging, verification, PRs) → pstack's Non-negotiables, unchanged.

When tsumi gains a skill, add its line here. `scripts/check-skills` fails if a tsumi skill is missing from this file.

## Start

1. Check that pstack is installed: [references/requirements.md](references/requirements.md). If it is missing, stop and give the user the install command from that file. Do not rebuild pstack's parts.
2. Open a todo. First item: read pstack's `poteto-mode/SKILL.md` in full. Its Non-negotiables and Principles still apply unless a line below overrides them.
3. Match the request against the Non-negotiables above. Add one todo item per matched skill or playbook: "read `<path>` in full". Read each before acting on that part of the work.
4. Pick a playbook: this skill's `playbooks/` first, then pstack's. Copy its steps into the todo. Mark a skipped step `skip: <reason>`.

## Evals first

Before you build, fix, or change an agent or skill, write what passes (A) and a way to run it and capture evidence (B). agent-design-review's "Start from evals" holds the method. These cases become the level-2 regression evals below.

## Order of fixes

Fix every failure, correction, or new requirement at the highest level that can own it.

1. **Environment, tools, and structure.** The model picks from enumerated options or component IDs instead of writing free text. Output that code consumes is bound by a JSON schema and rejected at the boundary. IDs, dates, amounts, recipients, and fixed phrases come from templates that code fills.
2. **Automated checks.** Deterministic checks and regression evals catch what remains. A new check must fail on the real past failure before the fix and pass after it.
3. **Prompts and skills.** Only judgment that 1 and 2 cannot enforce: interpreting intent, choosing a component, resolving ambiguity, deciding what matters. Keep it short.
4. **Human review.** Only output flagged as suspicious. Every human correction goes into the corrections log.

This orders investment. It is not a four-stage project. Pair a structural fix with its check. Contain an active incident first, then apply the order to the durable fix. agent-design-review holds the full method.

In the reply, state the level you fixed at and, in one line, why a higher level could not own it.

## Rules

### Same correction twice

When the same class of correction appears a second time, do not add another prompt line. Move it to level 1 or 2. Track it as: failure evidence → prevention boundary → enforcing resource → verification case → remaining judgment. If it cannot move, write why in the log's `moved_to` and `evidence` columns.

### Corrections log

Add one row per user correction to `corrections.tsv` at the root of the repo you are working in, with `source` set to `correction`. Columns: [references/corrections-template.tsv](references/corrections-template.tsv). In a customer project, do not commit the log until the user says where it lives.

Outside tsumi, this log only holds rows until the user reflects: tsumi-reflect moves them into tsumi's `corrections.tsv`. Count a class across this repo's log and `~/tsumi/corrections.tsv`.

### Changing tsumi

tsumi's source is the git checkout at `~/tsumi`. The copies that Cursor and Claude Code load are read-only: `~/.cursor/plugins/local/tsumi` is a clone of `main`, and `~/.claude/skills/tsumi` is a link to `~/tsumi` on `main`. To change tsumi, create a worktree from `~/tsumi`, edit there, and open a PR against `main`. Never edit the path a skill was loaded from. If `~/tsumi` does not exist, stop and ask where the source checkout is.

### Evals judge behavior

Compare old and new versions on the same requests. Keep the success criteria out of the executing agent's prompt. Judge artifacts and observed actions, not the agent's claim.

## Subagents

Where pstack says to use `poteto-agent`, use `tsumi-agent` (`tsumi:tsumi-agent` in Claude Code). Skills that name their own subagent type keep it.

## Not yet written down

These are Daiki's calls and are not captured yet. They get filled from patterns in tsumi's corrections log, which tsumi-reflect builds. Do not fill them by guessing. Use pstack's default and say so, or ask.

- TODO(Daiki): pass criteria and trial count for agent evals.
- TODO(Daiki): which signals mark output as suspicious enough for human review.
- TODO(Daiki): how an FDE engagement with a customer maps onto these playbooks.
- TODO(Daiki): model choice per role when building agents.
