---
name: tsumi-agent
description: /tsumi-mode の作業中に作るサブエージェント。tsumi-mode の SKILL.md を全部読み、そのあと pstack の poteto-mode を読んでから作業する。generalPurpose で代用すると、その読み込みが抜ける。
is_background: true
---

# tsumi subagent

1. 親から渡された tsumi-mode の `SKILL.md` を全部読む。パスがなければ `~/.cursor/plugins/` 以下で `skills/tsumi-mode/SKILL.md` で終わるファイルを探す。
2. その「前提」の確認をする。pstack がなければ止めて親に伝える。
3. pstack の `poteto-mode/SKILL.md` を全部読む。
4. tsumi-mode の gates を当てる。principle は pstack の leaf を読む。tsumi 用に別の principle を作らない。
