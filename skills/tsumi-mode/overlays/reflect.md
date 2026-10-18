# /reflect overlay

Read pstack's `reflect/SKILL.md` first and follow it. Three additions:

- Add an `eval case` column to each Accepted row: `yes: <case id and one-line content>` or `no: <reason>`. For `yes`, add the case to `evals/cases/` before editing the skill.
- If the transcript has a user correction, check `corrections.tsv` for the same `class`. On the second occurrence, apply "Same correction twice" in tsumi-mode instead of adding prose.
- An Accepted row that edits a tsumi file follows "Changing tsumi" in tsumi-mode. The skill path in the transcript is an installed copy. Do not edit it.
