---
name: tsumi-reflect
description: Runs pstack's reflect over the current conversation with tsumi's additions - each accepted learning gets an eval case or a structural fix, small structural fixes land in the same PR as the skill edits, and every accepted or backlog finding is recorded in tsumi's corrections.tsv without customer names or data. Use when the user explicitly says reflect or /reflect, or asks to feed what this conversation taught back into tsumi's skills. Do not use to summarize the day's work or to write a retrospective or weekly report. 日本語トリガー - reflect して / この会話を振り返って tsumi に反映して / 今回の学びをスキルに戻して。
---

# tsumi reflect

pstack's `reflect`, plus tsumi's additions. Learnings enter tsumi only through this skill, so every step here applies even outside `/tsumi-mode`.

## 1. Read pstack's reflect

Find pstack with [../tsumi-mode/references/requirements.md](../tsumi-mode/references/requirements.md). Read pstack's `reflect/SKILL.md` in full and follow it with the changes below. On conflict, this file wins.

## 2. Changes to pstack's steps

- **Step 4, structural enforcement check.** Do not move structural items to Backlog. tsumi fixes at the highest level that can own a problem (agent-design-review's Improvement order). Mark each Accepted item:
  - `fix here`: an eval case, a `scripts/check-skills` rule, a schema field, or another structural fix that fits in this PR.
  - `backlog`: too large for this PR. Write what to do.

  The user approves this split together with the Accepted list in step 5.
- **Step 5, apply.** Before editing a skill for an Accepted row, decide its eval case: `yes: <case id and one-line content>` or `no: <reason>`. For `yes`, add the case to `evals/cases/` before editing the skill. Do not file Backlog to a tracker. Record it (section 3).
- **Same class twice.** Look up each finding's `class` in tsumi's `corrections.tsv`. On the second occurrence, apply "Same correction twice" in tsumi-mode instead of adding prose.
- **Where to edit.** A skill path in the transcript is an installed copy. Edit tsumi only per "Changing tsumi" in tsumi-mode: a worktree from `~/tsumi` and a PR against `main`.

## 3. Record in tsumi's corrections.tsv

In the tsumi worktree, add rows to `corrections.tsv` at its root. Columns: [../tsumi-mode/references/corrections-template.tsv](../tsumi-mode/references/corrections-template.tsv).

- One row per Accepted or Backlog finding, with `source` set to `reflect`. Do not record Rejected findings.
- One row per user correction that this conversation logged in another repo's `corrections.tsv`, with `source` set to `correction`. After the PR is open, delete those rows from the other repo's log so the next reflect does not move them again.
- `moved_to`: where the fix went (tool, check, eval case, prompt), or `backlog: <what to do>`.
- `evidence`: the date and a label for the conversation. Never a repo name, customer name, customer data, or quoted transcript text. Label a customer project with a placeholder such as `customer project A`.
- Abstract `wrong` and `correction` the same way.

Show these rows next to the Accepted list so the user approves them in pstack's step 5. Put them in the same PR as the skill edits. If no skill changes, open a PR with the rows alone. Run `scripts/check-skills` before declaring done.
