---
name: tsumi-mode
description: Daiki Tsutsumi's agent-development workflow, layered on pstack's poteto-mode. Loads pstack, then runs agent and skill work in Daiki's order of fixes - tools, schemas, and templates first; automated checks and regression evals second; prompt rules only for judgment that cannot be encoded; human review only for suspicious output. Adds rules for repeated corrections, a corrections log, regression evals on every skill change, and customer data. Use when the user types /tsumi-mode, says "tsumi", or asks to work in Daiki's style while building, fixing, or evaluating an agent, skill, prompt, tool definition, or output schema. Requires the pstack plugin. For a single design review without the full workflow, agent-design-review is enough. 日本語トリガー - /tsumi-mode / tsumi で / tsumi-mode で進めて / Daiki のやり方で / 堤のやり方で。
---

# tsumi mode

Build agents so the easiest operation produces a valid result. pstack's `poteto-mode` supplies the base: principles, playbooks, reply format, autonomy, subagents. This file adds Daiki's agent-development rules. On conflict, this file wins.

## Start

1. Check that pstack is installed: [references/requirements.md](references/requirements.md). If it is missing, stop and tell the user to run `/add-plugin pstack`. Do not rebuild pstack's parts.
2. Open a todo. First item: read pstack's `poteto-mode/SKILL.md` in full. Read a principle's leaf skill before you cite it.
3. Pick a playbook. Look in this skill's `playbooks/` first, then pstack's. Copy its steps into the todo. Mark a skipped step `skip: <reason>`.
4. Apply the order of fixes and the rules below to every change.

## Order of fixes

Fix every failure, correction, or new requirement at the highest level that can own it. Do not write a lower-level fix when a higher one works.

1. **Environment, tools, and structure.** The model picks from enumerated options or component IDs instead of writing free text. Output that code consumes is bound by a JSON schema and rejected at the boundary. IDs, dates, amounts, recipients, and fixed phrases come from templates that code fills.
2. **Automated checks.** Deterministic checks and regression evals catch what remains. A new check must fail on the real past failure before the fix and pass after it.
3. **Prompts and skills.** Only judgment that 1 and 2 cannot enforce: interpreting intent, choosing a component, resolving ambiguity, deciding what matters. Keep it short.
4. **Human review.** Only output flagged as suspicious. Every human correction goes into the corrections log.

This orders investment. It is not a four-stage project. Pair a structural fix with its check. Contain an active incident first, then apply the order to the durable fix. Do not remove a check or review step before its replacement works.

For the full method (caller-first tool design, the model/tool contract, choosing and validating a change), read [../agent-design-review/SKILL.md](../agent-design-review/SKILL.md). Read it before designing a new agent or skill, or before moving a correction up a level.

In the reply, state the level you fixed at and, in one line, why a higher level could not own it.

## Rules

### Same correction twice

When the same class of correction appears a second time, do not add another prompt line. Move it to level 1 or 2. Track it as: failure evidence → prevention boundary → enforcing resource → verification case → remaining judgment. If it cannot move, write why in the log's `moved_to` and `evidence` columns. For code in this repo rather than agent output, use pstack's `/correct`.

### Regression eval on every change

After changing a skill, prompt, tool definition, or schema, run [playbooks/eval.md](playbooks/eval.md). Do not call the change done before you have the result. Compare old and new versions on the same requests. Keep the success criteria out of the executing agent's prompt; judge artifacts and observed actions, not the agent's claim.

### Corrections log

When the user corrects you, add one row to `corrections.tsv` at the root of the repo you are working in. Columns: [references/corrections-template.tsv](references/corrections-template.tsv). A second row with the same `class` triggers "Same correction twice". In a customer project, do not commit the log until the user says where it lives.

### Customer data

Stop and ask before customer data or customer names go into an eval case, the corrections log, a commit, or anything sent outside. This adds to pstack's must-stop list.

### Look for existing work first

Before writing new rules, a new skill, or a new schema, search the user's existing skills and repos for one that already covers it. Port it instead of rewriting it.

### Writing

- Japanese prose: write it, then apply the `clear-japanese` skill to the draft.
- English prose: pstack's `/unslop` and `/technical-writing`.

## Playbooks

- **New agent** ([playbooks/new-agent.md](playbooks/new-agent.md)). Build a new task agent: tools and schemas first, evals before prompt.
- **Review triage** ([playbooks/review-triage.md](playbooks/review-triage.md)). Decide which outputs go to a human and feed corrections back.
- **Eval** ([playbooks/eval.md](playbooks/eval.md)). Override of pstack's Eval playbook. Read pstack's version first.

Anything else: pstack's Playbooks index. A recurring agent failure goes to `agent-design-review`.

## pstack skill overlays

When you use one of these pstack skills, read the pstack skill first, then the overlay. On conflict, the overlay wins.

| pstack skill | Overlay |
|---|---|
| `/technical-writing` | [overlays/technical-writing.md](overlays/technical-writing.md): Japanese documents use clear-japanese |
| `/correct` | [overlays/correct.md](overlays/correct.md): agent-output failures go to agent-design-review |
| `/reflect` | [overlays/reflect.md](overlays/reflect.md): each accepted learning gets an eval-case column |

## Subagents

Where pstack says to use `poteto-agent`, use `tsumi-agent`. Skills that name their own subagent type keep it.

## Not yet written down

These are Daiki's calls and are not captured yet. Do not fill them by guessing. Use pstack's default and say so, or ask.

- TODO(Daiki): pass criteria and trial count for agent evals.
- TODO(Daiki): which signals mark output as suspicious enough for human review.
- TODO(Daiki): how an FDE engagement with a customer maps onto these playbooks.
- TODO(Daiki): model choice per role when building agents.
