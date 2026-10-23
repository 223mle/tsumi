### New agent

**You own the agent's design and the evals that show it works. Start from the evals. Write the prompt last.**

1. Read `agent-design-review/SKILL.md` in full, starting with "Start from evals".
2. Collect a few real task inputs. For each, write the output that passes, who uses it and how, and what a wrong output costs. These are the eval cases (A). Summarize the task flow from them in one paragraph. If the inputs contain customer data, apply the customer-data line in tsumi-mode's Non-negotiables first.
3. Decide what evidence each case produces and where it goes (B), and who judges each criterion: code, a second model, or a person. Show that each check passes a hand-made correct output and fails a deliberately broken one. Label the broken one synthetic.
4. Sketch one successful tool call from the agent's side: a small structured request and an observable result. Derive the tool interface from it. As soon as the first tool exists, run one case through to its evidence. If B needs more than a run command and an evidence path, generate it now with pstack's `create-verification-skill` and [../overlays/create-verification-skill.md](../overlays/create-verification-skill.md).
5. List the finite choices and fixed values: categories, recipients, statuses, IDs, dates, amounts, fixed phrases. Make choices enums or component IDs. Bind output with a JSON schema validated at the boundary. Put fixed values in templates that code fills.
6. Write the prompt: only the judgment that steps 4–5 cannot enforce.
7. Run the evals. Record the pass rate and why each failure failed.
8. Set the human-review conditions with `playbooks/review-triage.md`.

**Reply:** the eval cases and who judges each, where the evidence goes, the caller example, mistakes removed by tools/schemas/templates, where the schemas and templates live, eval count and pass rate, judgment left in the prompt and why, review conditions.
