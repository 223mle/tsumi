# Required plugin

tsumi sits on pstack. Check before you start.

| Plugin | How to detect | Where its files are |
|---|---|---|
| `pstack` | `setup-pstack` appears in the skill list | Most pstack skills are slash-only and hidden from the list. They sit next to `setup-pstack`: `<setup-pstack dir>/../poteto-mode/SKILL.md`, `../poteto-mode/playbooks/<name>.md`, `../principle-<name>/SKILL.md`, `../unslop/SKILL.md`, `../technical-writing/SKILL.md`, `../correct/SKILL.md`, `../reflect/SKILL.md`. |

If pstack is missing, stop and tell the user to run `/add-plugin pstack`. Do not rebuild the missing parts.

If several pstack versions exist, use the one with the highest `version` in `.cursor-plugin/plugin.json`.
