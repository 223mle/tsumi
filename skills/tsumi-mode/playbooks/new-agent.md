### New agent

**You own the agent's design and the evals that show it works. Write the prompt last.**

1. Read `agent-design-review/SKILL.md` in full.
2. Write the task flow: input, output, who uses the output and how, and the cost of a wrong output.
3. Sketch one successful tool call from the agent's side: a small structured request and an observable result. Derive the tool interface from it.
4. List the finite choices and fixed values: categories, recipients, statuses, IDs, dates, amounts, fixed phrases. Make choices enums or component IDs. Bind output with a JSON schema validated at the boundary. Put fixed values in templates that code fills.
5. Write eval cases before the prompt. Use real task inputs. If they contain customer data, apply "Customer data" in tsumi-mode first.
6. Write the prompt: only the judgment that steps 3–5 cannot enforce.
7. Run the evals. Record the pass rate and why each failure failed.
8. Set the human-review conditions with `playbooks/review-triage.md`.

**Reply:** task flow, the caller example, mistakes removed by tools/schemas/templates, where the schemas and templates live, eval count and pass rate, judgment left in the prompt and why, review conditions.
