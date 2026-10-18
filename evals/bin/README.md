# bin

- `run-trigger`: トリガーお題（`cases/trigger-*.yaml`）を Cursor CLI で回し、stream-json の tool_call から読んだ SKILL.md を判定する。Python 3 の標準ライブラリだけで動く。
- run.ts、score.ts、compare.ts は未実装。設計は ../README.md の「ハーネス」と「run.ts の中身の案」。
