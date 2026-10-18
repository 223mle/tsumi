---
name: mistake-triage
description: Looks back over the current conversation for mistakes that recur, such as the user correcting the same thing twice, a failed check, or reverted work, and proposes how to stop each one. Routes every mistake to one or more fixes - a mechanism that makes it impossible (architecture, types, lint, test, via pstack's correct procedure), a prose edit to a skill or rule, an eval case that catches a recurrence, or a question for the user - and emits the result as schema-checked JSON. Use when the user asks to reflect on or look back at the conversation, asks why a mistake keeps happening, or asks how to make sure it does not happen again. Reads only the current conversation, never history files. Do not use for reviewing code changes or summarizing work. 日本語トリガー - 振り返って / 今の会話を振り返って / 同じミスをしないようにして / また同じ間違い / 何度も言ってる / 再発を防いで / reflect。
---

# Mistake triage

Find the mistakes this conversation keeps making and send each one to the fix that stops it. tsumi's order of fixes applies: a mechanism beats a rule, a rule needs a check, and only real judgment goes to the user.

## Scope

Use only the conversation in your context. Do not read `~/.claude/projects/`, `~/.cursor/projects/`, `agent-transcripts/`, or any other chat history file, even if pstack's reflect would. If part of the conversation was compacted away, work from what remains and say so.

You may read `corrections.tsv` at the root of the repo you are working in, and the skill or rule files a fix would change.

## Steps

1. **Collect.** List each mistake with its evidence: a user correction, a failed check or eval, reverted or redone work, a rule you broke. Quote the turn that shows it. Group repeats of the same mistake under one `class` in kebab case. Reuse a `class` name from `corrections.tsv` when it fits.
2. **Count.** `count_in_conversation` is how many times it happened here. `count_in_log` is the number of `corrections.tsv` rows with the same `class` (0 if there is no log).
3. **Route.** Give each mistake one or more routes:
   - `mechanism`: a structure can make it impossible or catch it. Name the highest level that works, in pstack's correct order: `architecture`, `types`, `lint`, `test`, `docs`. Say how to prove the check fails on the real past mistake.
   - `prose`: only judgment can prevent it. Name the file to change and the exact change.
   - `eval`: a recurrence would go unnoticed. Write the case id, the request, and the deterministic check.
   - `ask`: you cannot decide between routes, or the fix needs a call only the user can make. Write the question.

   Seen twice or more in total → `mechanism`, or give `no_mechanism_reason`. A `prose` route needs an `eval` route too, or `no_eval_reason`. Use `ask` only when the routes above cannot be chosen from the evidence. Drop one-offs with no recurrence risk into `dropped` with a reason.
4. **Emit.** Write the result as one ```json block that follows [references/triage.schema.json](references/triage.schema.json). If you can run commands, run `python3 <this skill's dir>/scripts/check_triage.py` on it and fix every error before you show it.
5. **Present.** After the JSON, give one line per mistake in the user's language: what happened, where it goes, why. Then wait for approval. Apply nothing before the user picks.

## After approval

- `mechanism` → read pstack's `correct/SKILL.md` and follow it for that class: highest level first, prove the check fails on the real past mistake, one commit per class.
- `prose` → make the edit. In tsumi files, follow "Changing tsumi" in tsumi-mode.
- `eval` → add the case under `evals/cases/` before or with the fix it guards.
- Add one `corrections.tsv` row per user correction you acted on, with `moved_to` naming the mechanism, prose, or eval case.

## Reply

The JSON block, the one-line summaries, and what you are waiting for.
