---
name: session-insights
description: Reads the whole current session between Daiki and the agent and turns what it reveals into proposed changes to skills, rules, checks, and evals. Picks up Daiki's preferences, his development tendencies, corrections he repeated, and moments where the agent hid, glossed over, or overstated its own work, such as reporting unfinished work as done. Each insight carries a quote from the session, a concrete diff to a named file, and the reason; insights a mechanism can enforce also get a check or eval proposal. Output is short Japanese proposals plus schema-checked JSON. Command-only - use when Daiki runs /tsumi:session-insights (Claude Code) or /session-insights (Cursor). Reads only the current session, never history files, and edits nothing before approval.
disable-model-invocation: true
---

# Session insights

Daiki runs this command at the end of a session. Read the whole session and answer one question: what did this session teach about how Daiki wants agents to work, and which file should change so the next session already knows it?

## Scope

- Use only the conversation in your context, from the first turn. Do not read `~/.claude/projects/`, `~/.cursor/projects/`, `agent-transcripts/`, or any other history file. If part of the session was compacted away, say so and work from what remains.
- You may read the files a proposal would change, and `corrections.tsv` at the repo root, to name the right target and avoid proposing what is already written.
- Edit nothing. Proposals wait for Daiki's approval.

## What to look for

Every insight needs evidence: a quote from the session, or a precise description of a scene ("the agent said X at turn N, and later Y"). No evidence, no insight. Do not infer a preference from one neutral turn, and do not propose generic best practice the session never touched.

1. `preference`: what Daiki wants, said outright or shown by what he accepted and rejected (voice, length, tools, workflow, what to leave out).
2. `tendency`: how Daiki develops (where he spends time, what he checks first, the environment he works in, what he complains about).
3. `repeated-correction`: the same correction given twice or more.
4. `hidden-mistake`: the agent hid, glossed over, or overstated something - reported unfinished work as done, promised work and did not do it or mention it, admitted an error only when asked, buried a failure under a success, or claimed a result it did not measure. Look at the agent's own turns as hard as at Daiki's. These matter most; do not soften them.

Merge insights that point to the same change. Put weak or one-off signals in `dropped` with the reason.

## Proposal per insight

- `target`: the file to change (skill, rule, playbook, check script, eval case, CLAUDE.md). Prefer a tsumi or pstack file that already covers the topic over a new one.
- `change`: the concrete edit, as a unified-diff-style snippet or the exact lines to add or replace.
- `reason`: why this change follows from the evidence.
- Fix order still applies: if a structure (check script, schema, hook, eval case) can enforce it, add `check` with its kind and what it fails on. `repeated-correction` and `hidden-mistake` need `check`, or `no_check_reason`.

## Output

1. One short Japanese block per insight, for Daiki to read:
   `示唆:` one sentence. `根拠:` the quote. `変更案:` target and the change. `理由:` one sentence. `検査案:` if any.
2. Then one ```json block following [references/insights.schema.json](references/insights.schema.json). If you can run commands, run `python3 <this skill's dir>/scripts/check_insights.py` on your reply and fix every error before you show it.
3. End with what you are waiting for: which proposals to apply.

## After approval

Apply only the proposals Daiki picks. For a `check`, follow pstack's `correct/SKILL.md` (prove the check fails on the real past case). For tsumi files, follow "Changing tsumi" in tsumi-mode. Add one `corrections.tsv` row per applied insight, with `moved_to` naming the file or check.
