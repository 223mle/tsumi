# Required plugin

tsumi sits on pstack. Check before you start.

| Harness | How to detect pstack | Where its files are | Install command |
|---|---|---|---|
| Cursor | `setup-pstack` appears in the skill list | Next to `setup-pstack`. Version in `.cursor-plugin/plugin.json`. | `/add-plugin pstack` |
| Claude Code | `pstack:setup-pstack` appears in the skill list | `~/.claude/plugins/cache/<marketplace>/pstack/<version>/`. Version in `.claude-plugin/plugin.json`. | `/plugin marketplace add cursor/plugins`, then `/plugin install pstack@cursor-plugins` |

Most pstack skills are slash-only and hidden from the list. They sit next to `setup-pstack`: `<setup-pstack dir>/../poteto-mode/SKILL.md`, `../poteto-mode/playbooks/<name>.md`, `../principle-<name>/SKILL.md`, `../correct/SKILL.md`, `../reflect/SKILL.md`, `../create-verification-skill/SKILL.md`.

If pstack is missing, stop and give the user the install command for their harness. Do not rebuild the missing parts.

If several pstack versions exist, use the one with the highest `version`.
