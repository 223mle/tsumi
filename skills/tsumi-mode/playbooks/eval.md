### Eval (tsumi override)

#### Writing a skill description

The description decides whether an agent ever opens the skill. Apply these when you write, rewrite, or propose one.

1. State what the skill does and the requests or situations that should open it. Put the main situation first.
2. Third person. No "I can" or "You can".
3. Use the words users actually say. End with `日本語トリガー - ` and Japanese phrasings, except for a skill written fully in Japanese.
4. Name a nearby situation where it should not open, if one exists.
5. At most 1,024 characters. No XML tags.
6. Write one request that should open the skill and one close request that should not. Add them to `evals/cases/trigger-<skill>-NNN.yaml` in the repo, or include them in the reply when you only propose the text.
7. Run `scripts/check-skills`, then the trigger cases, when you can run commands.

#### After changing a skill, prompt, tool definition, or schema

Read pstack's `poteto-mode/playbooks/eval.md` first. Keep its blinding rule and its rule to judge from the transcript.

When you change a skill, prompt, tool definition, or schema, add these steps:

1. Run the evals on the old version (see `evals/README.md` in the tsumi repo). Use a stored baseline if there is one.
2. Make the change.
3. Run the same cases with the same pstack version and model.
4. Compare. If any `must-pass` case fails, do not ship. Explain the failure from the transcript.
5. For each new case, record that it fails on the old version.
6. If you changed a `description`, also run the trigger cases (`evals/cases/trigger-*.yaml`) and `scripts/check-skills`.

**Reply:** pstack's Eval reply plus pass rate before and after, regressed cases, flaky cases, pstack version used.
