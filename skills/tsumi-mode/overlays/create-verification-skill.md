# /create-verification-skill overlay (task agents)

Read pstack's `create-verification-skill/SKILL.md` first and follow it. When the thing to verify is a task agent rather than an app, read its terms this way:

- **App**: the agent, run the way its real caller runs it (a CLI call, an API request, a chat message).
- **Drive**: feed one eval case's input. Keep the case's success criteria out of what the agent sees.
- **Evidence**: the output plus its side effects (sent messages, written rows, files, rendered images).
- **Feature map**: one file per kind of request the agent handles.

Two additions:

- Before handing the skill over, show that each check passes a hand-made correct output and fails a deliberately broken one. Label the broken one synthetic.
- Its "prove the generated skill" step needs a working first tool. For a new agent, generate the skill once the first tool exists (New agent step 4), not before.

When the output itself is the evidence, such as structured output a script consumes, do not generate a skill. Write the run command and the evidence path next to the eval cases.
