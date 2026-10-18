### Eval (tsumi override)

Read pstack's `poteto-mode/playbooks/eval.md` first. Keep its blinding rule and its rule to judge from the transcript.

When you change a skill, prompt, tool definition, or schema, add these steps:

1. Run the evals on the old version (see `evals/README.md` in the tsumi repo). Use a stored baseline if there is one.
2. Make the change.
3. Run the same cases with the same pstack version and model.
4. Compare. If any `must-pass` case fails, do not ship. Explain the failure from the transcript.
5. For each new case, record that it fails on the old version.
6. If you changed a `description`, also run the trigger cases (`evals/cases/trigger-*.yaml`) and `scripts/check-skills`.

**Reply:** pstack's Eval reply plus pass rate before and after, regressed cases, flaky cases, pstack version used.
