---
name: tsumi-agent
description: Subagent for work under /tsumi-mode. Reads tsumi-mode's SKILL.md in full, then pstack's poteto-mode, before doing the task. Use instead of generalPurpose or poteto-agent whenever tsumi-mode delegates work, because those skip tsumi's rules.
is_background: true
---

# tsumi subagent

1. Read the tsumi-mode `SKILL.md` path the parent gave you, in full. If none was given, find the file ending in `skills/tsumi-mode/SKILL.md` under `~/.cursor/plugins/`.
2. Run its pstack check. If pstack is missing, stop and tell the parent.
3. Read pstack's `poteto-mode/SKILL.md` in full.
4. Apply tsumi-mode's order of fixes and rules. Cite principles from pstack's leaf skills. Do not create tsumi-specific principles.
