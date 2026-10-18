### Review triage

**Human review is the last level. Send people only suspicious output, and turn their corrections into structure.**

1. Write the review conditions so code can evaluate them: schema violations, validator warnings, inputs close to unstable eval cases. TODO(Daiki): add the signals Daiki uses in practice.
2. Point review at meaning, business assumptions, and decisions that cannot yet be checked reliably. Do not spend it on what a check could catch.
3. For each condition, count how many past outputs it would send. If too many, first look for a kind that level 1 or 2 can remove.
4. Log every human correction in `corrections.tsv`, one row each.
5. When a `class` reaches two rows, apply "Same correction twice" in tsumi-mode.
6. Turn corrections worth preventing into eval cases.

**Reply:** conditions, expected volume, log location and format, cases added.
