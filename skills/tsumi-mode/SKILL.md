---
name: tsumi-mode
description: Entry point that bundles every tsumi skill with pstack for building agents the way Daiki Tsutsumi does. Takes a request, loads pstack's poteto-mode, and routes each situation to the right skill - agent-design-review for designing or fixing an agent or skill, the regression-eval playbook after any skill, prompt, tool, or schema change, clear-japanese for Japanese documents, pstack skills for everything else. Applies Daiki's order of fixes - tools, schemas, and templates first; automated checks and evals second; prompt rules only for judgment that cannot be encoded; human review only for suspicious output. Use when the user types /tsumi-mode followed by a request, says "tsumi", or asks to work in Daiki's style. Requires the pstack plugin. Each bundled skill also works on its own without this entry point. 日本語トリガー - /tsumi-mode <依頼> / tsumi で / tsumi-mode で進めて / Daiki のやり方で / 堤のやり方で。
---

# tsumi mode

Build agents so the easiest operation produces a valid result. This skill is the router for every tsumi skill. pstack's `poteto-mode` supplies the base: principles, playbooks, reply format, autonomy, subagents. On conflict, this file wins.

Bundled tsumi skills live at `../<name>/SKILL.md` from this file. Put this file's absolute path in every `tsumi-agent` prompt.

## Start

1. Check that pstack is installed: [references/requirements.md](references/requirements.md). If it is missing, stop and tell the user to run `/add-plugin pstack`. Do not rebuild pstack's parts.
2. Open a todo. First item: read pstack's `poteto-mode/SKILL.md` in full. Its Non-negotiables and Principles still apply unless a line below overrides them.
3. Match the request against the Non-negotiables below. Add one todo item per matched skill or playbook: "read `<path>` in full". Read each before acting on that part of the work.
4. Pick a playbook: this skill's `playbooks/` first, then pstack's. Copy its steps into the todo. Mark a skipped step `skip: <reason>`.

## Non-negotiables

Each line is situation → what you must read and apply. These add to pstack's Non-negotiables.

- Designing, building, reviewing, or changing an agent, skill, prompt, tool definition, output schema, or template → the **agent-design-review** skill (`../agent-design-review/SKILL.md`), before you write the change.
- A new task agent from scratch → the **New agent** playbook ([playbooks/new-agent.md](playbooks/new-agent.md)). It also requires agent-design-review.
- An agent output fails, an eval fails, or the user corrects agent behavior → agent-design-review. Fix at the highest level in the Order of fixes.
- Writing or changing a skill, prompt, tool definition, schema, or template, including a draft or proposal the user will apply → the **Eval** playbook ([playbooks/eval.md](playbooks/eval.md)) before calling it done. Changed a `description` → also run `scripts/check-skills` and the trigger cases.
- Deciding which outputs a human reviews, or human corrections arrive → the **Review triage** playbook ([playbooks/review-triage.md](playbooks/review-triage.md)).
- The user corrects you → add a row to the corrections log (see Rules). Second row of the same class → "Same correction twice".
- Japanese document or prose others will read (README, design doc, PR description, commit message, Japanese SKILL.md, customer-facing text) → the **clear-japanese** skill (`../clear-japanese/SKILL.md`) on your draft before you hand it over.
- Your own chat reply in Japanese → write it per pstack's Writing the reply, then check it against clear-japanese's preservation and cohesion rules. Do not switch to clear-japanese's "return only the rewritten text" output.
- English prose → pstack's **unslop**. English docs → pstack's **technical-writing**.
- Docs in either language → pstack's **technical-writing** plus [overlays/technical-writing.md](overlays/technical-writing.md).
- Repeated mistakes in repo code (not agent output) → pstack's **correct** plus [overlays/correct.md](overlays/correct.md).
- The user says reflect → pstack's **reflect** plus [overlays/reflect.md](overlays/reflect.md).
- About to write a new rule, skill, or schema → search the user's existing skills and repos first. Port before you rewrite.
- Customer data or customer names about to enter an eval case, the corrections log, a commit, or anything sent outside → stop and ask.
- Anything else (code, architecture, debugging, verification, PRs) → pstack's Non-negotiables, unchanged.

When tsumi gains a skill, add its line here. `scripts/check-skills` fails if a tsumi skill is missing from this file.

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

Add one row per user correction to `corrections.tsv` at the root of the repo you are working in. Columns: [references/corrections-template.tsv](references/corrections-template.tsv). In a customer project, do not commit the log until the user says where it lives.

### Evals judge behavior

Compare old and new versions on the same requests. Keep the success criteria out of the executing agent's prompt. Judge artifacts and observed actions, not the agent's claim.

## Subagents

Where pstack says to use `poteto-agent`, use `tsumi-agent`. Skills that name their own subagent type keep it.

## Not yet written down

These are Daiki's calls and are not captured yet. Do not fill them by guessing. Use pstack's default and say so, or ask.

- TODO(Daiki): pass criteria and trial count for agent evals.
- TODO(Daiki): which signals mark output as suspicious enough for human review.
- TODO(Daiki): how an FDE engagement with a customer maps onto these playbooks.
- TODO(Daiki): model choice per role when building agents.
