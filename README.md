# tsumi

**English** | [日本語](README.ja.md)

tsumi packages how Daiki Tsutsumi builds agents into skills an agent can use. It runs in Cursor and Claude Code, and sits on top of [pstack](https://github.com/cursor/plugins/tree/main/pstack): it keeps pstack as the base and adds only what agent development needs. The name comes from the Japanese 積み上げる (*tsumiageru*), "to stack up."

When you build a business agent and try to prevent mistakes with warnings in the prompt, the warnings pile up and the same mistakes come back. tsumi makes the agent start every build or fix from an eval, then decide where the fix belongs in a fixed order, so the same fix never has to be made twice.

pstack already covers general engineering work: principles, playbooks, and how to write replies. tsumi uses pstack as is and adds the agent-development layer.

## Install

The source of truth is the `main` branch of a git checkout at `~/tsumi`. Claude Code reads that checkout directly. Cursor reads a separate clone.

1. Install pstack.

   - In Cursor, run `/add-plugin pstack`.
   - In Claude Code, run `/plugin marketplace add cursor/plugins`, then `/plugin install pstack@cursor-plugins`.

2. Clone tsumi to `~/tsumi`.

   ```bash
   git clone https://github.com/223mle/tsumi.git ~/tsumi
   ```

3. For Claude Code, symlink `~/.claude/skills/tsumi` to `~/tsumi`. Claude Code reads plugins under `~/.claude/skills/` in place, without copying them.

   ```bash
   ln -s ~/tsumi ~/.claude/skills/tsumi
   ```

4. For Cursor, clone a second copy to `~/.cursor/plugins/local/tsumi`. Cursor does not follow symlinks that point outside this folder.

   ```bash
   git clone https://github.com/223mle/tsumi.git ~/.cursor/plugins/local/tsumi
   ```

5. Add a session-start hook to Claude Code's `~/.claude/settings.json`. Every new session runs `scripts/sync-installs`, which brings `~/tsumi` and `~/.cursor/plugins/local/tsumi` up to the latest `main`.

   ```json
   "hooks": {
     "SessionStart": [
       {
         "matcher": "startup",
         "hooks": [
           {
             "type": "command",
             "command": "[ -x \"$HOME/tsumi/scripts/sync-installs\" ] && \"$HOME/tsumi/scripts/sync-installs\"; exit 0",
             "timeout": 30
           }
         ]
       }
     ]
   }
   ```

   The hook only updates a checkout that is on `main` with no uncommitted changes. Results go to `~/Library/Logs/tsumi-sync.log`. If you use only Cursor and never open Claude Code, the Cursor copy is not updated.

6. In Claude Code, start a new session. In Cursor, restart or run **Developer: Reload Window**. tsumi is installed when its skills appear in the skill list.

To change tsumi, do not edit the loaded copies. Cut a worktree from `~/tsumi`, make the change there, and open a PR.

### Codex only: keep the skills up to date

On macOS, run this from a working branch:

```bash
python3 scripts/install-codex-sync
```

The installer fetches the latest merged version and points the three tsumi skills that Codex reads at a dedicated copy. It adds a hook to `~/.codex/hooks.json` that updates the copy when a chat starts or resumes, and keeps your existing hooks. After setup, open Codex's Hooks settings and trust the hook once. It does not run until you trust it.

The dedicated copy lives at `~/.codex/tsumi/current`. The hook only reads `main` from GitHub. It never changes `~/tsumi`, the Cursor copy, or any local or remote `main` branch. It switches the skills to the new version only after the update finishes, and keeps the old version if the fetch or the checks fail. It does not take back instructions already loaded into a running chat.

- The update log is at `~/.codex/tsumi/update.log`.
- The links and hook settings from before the install are saved in `~/.codex/tsumi/install-backup.json`.
- If Codex does not pick up a change, restart it. To stop auto-updates, disable the hook in Hooks settings.
- The update script does not update itself. To update the script, run the installer again.
- The version that renamed `clear-japanese` to `unslop` cannot be pulled by the old update script, which stays on the old version. Run the installer once more. This replaces `~/.agents/skills/unslop`, which points at pstack's `unslop`, with a link to tsumi's `unslop`, and removes `~/.agents/skills/clear-japanese`. The links from before the replacement stay in `install-backup.json`.

This setup does not depend on Claude Code starting, and it leaves the Claude Code and Cursor sync setup unchanged.

## Usage

Start a task with `/tsumi-mode` (in Claude Code, `/tsumi:tsumi-mode`). It reads your request and picks from tsumi's skills and pstack's skills as the task needs them.

```text
/tsumi-mode I want an agent that sorts support emails into "billing", "cancellation", and "other".
```

- tsumi-mode fades as a conversation grows long. Invoke it again when you start new work. In Cursor, pick tsumi-mode from the `/` menu and press Option+Enter (Alt+Enter on Windows) to make it a Custom Mode that loads every turn.
- Ask "This agent returns a different spelling every time. How should I fix it?" and `agent-design-review` loads on its own, without tsumi-mode.
- Paste Japanese text and ask "this is hard to read, fix it," and `unslop` returns the cleaned-up text. Hand it notes and ask for a how-to, and `unslop` loads too.

## Skills

The entry point is `tsumi-mode`. It runs only when you invoke it by command. The other three skills also work alone: the agent loads them when your request matches, with or without tsumi-mode.

| skill | loads on its own when |
|---|---|
| [`tsumi-mode`](skills/tsumi-mode/SKILL.md) | you type `/tsumi-mode` (`/tsumi:tsumi-mode` in Claude Code). Writing "use tsumi" is not enough. |
| [`agent-design-review`](skills/agent-design-review/SKILL.md) | you design an agent or skill, review a design, or keep seeing the same mistake or drifting output. |
| [`unslop`](skills/unslop/SKILL.md) | you write a Japanese document, or ask to fix or clarify Japanese text. |
| [`tsumi-reflect`](skills/tsumi-reflect/SKILL.md) | you say "reflect" at the end of a conversation. Not for weekly reports or retrospectives. |

<details>
<summary>what tsumi-mode reads in each situation</summary>

| situation | tsumi-mode reads |
|---|---|
| designing or fixing an agent, skill, prompt, tool definition, or output schema | `agent-design-review` |
| building a new business agent | the New agent playbook (plus `agent-design-review`) |
| a failing agent output, a failing eval, or a correction to an agent | `agent-design-review` |
| building or fixing an agent with no way to run it and capture evidence | pstack's `create-verification-skill`, with tsumi's overlay |
| you said reflect, or want this conversation's lessons fed back into tsumi | `tsumi-reflect` (pstack's `reflect` plus tsumi's additions) |
| a skill, prompt, tool definition, or schema changed | the Eval playbook (regression evals). If a description changed, also `scripts/check-skills` and the trigger cases |
| deciding which outputs go to a human, or a human correction arrives | the Review triage playbook |
| writing or fixing a Japanese document (README, design doc, ADR, how-to, PR description; not commit messages) | `unslop` |
| anything else (code, design, debugging, verification, PRs) | pstack's `poteto-mode` rules, unchanged |

</details>

tsumi does not use pstack's `unslop` or `technical-writing`. Where pstack would call them, tsumi uses its own `unslop` for Japanese documents people read, and nothing for commit messages or chat replies. tsumi's `unslop` borrows the parts of pstack's `technical-writing` that also apply to Japanese, such as choosing the document type first and writing code names exactly as they are. For the candidate-detection command and the hooks behind `unslop`, see [document checks](docs/unslop-checks.md) (Japanese).

`agent-design-review` and `unslop` (named `clear-japanese` when it moved) came from [223mle/skills](https://github.com/223mle/skills). tsumi is now their only source; they are not kept in 223mle/skills.

## How tsumi thinks

### Start from an eval

Before you build, fix, or change an agent, set up an eval to fix the direction. Write the definition of passing (A) first, then a way to run the real thing and capture evidence (B).

- **A. The definition of passing.** For each real input, write the output that passes, who uses that output and how, and what happens when it is wrong. Quantitative versus qualitative is just a question of who judges: code, another model, or a person.
- **B. A way to run it and capture evidence.** Keep the output itself, side effects such as a sent email or a written row, and rendered results such as slide images. If the output is already the evidence, deciding the run command and where the evidence goes is enough. If you need more, use pstack's `create-verification-skill` with tsumi's overlay.

Before trusting a judge, check that it passes a hand-made correct output and fails a deliberately broken one. The eval you build here becomes the regression eval in layer 2 below.

### Put each fix as high as it can go

Place each fix in the highest layer that works, in this order:

1. **Make the mistake impossible with the environment and tools.** When the choices are fixed, have the agent pick from components or IDs instead of writing freely. Constrain output that code reads with a JSON schema, and reject anything that does not match on the receiving side. Put IDs, dates, amounts, recipients, and boilerplate in templates and fill them with code.
2. **Catch it with automated checks and regression evals.** Find remaining mistakes with fixed checks and eval cases. Every time a skill or prompt changes, run a number of cases proportional to the change and compare with the previous version.
3. **Write only uncodeable judgment into the prompt.** Reading the intent of a request, or choosing which component to use. When the same fix shows up twice, move it to layer 1 or 2 instead of adding to the prompt.
4. **Save human review for last, and only for suspicious output.** Record what people corrected in the correction log, and use it as material for the next fix.

This is an order of investment, not a plan to finish four phases in sequence.

### Grow from top practice and recorded dialogue

tsumi grows from two sources.

- **Top practice.** The approach starts from the practice of top developers, such as poteto's posts and pstack, and will keep pulling from their blogs and skills.
- **Recorded dialogue between Daiki and agents.** Say "reflect" at the end of a conversation, and `tsumi-reflect` picks up the lessons and bundles the skill fixes and the correction-log rows into one PR. Only threads where reflect ran are used. The correction log never contains customer names or customer data.

When two rows of the same kind collect in the correction log, the fix moves into structure instead of the prompt. Pass/fail criteria for evals that are not yet settled, and the signals for which outputs go to a human, are also decided from the trends in this record.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). Design decisions are in [DESIGN.md](DESIGN.md), and the eval design is in [evals/README.md](evals/README.md). These documents are in Japanese.
