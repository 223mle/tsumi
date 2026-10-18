# スキルの書き方

Agent Skills の公式ドキュメントを読んで、tsumi で守ることをまとめました。出典は末尾にあります。`scripts/check-skills` は、このうち機械で確かめられるものを検査します。

## description

エージェントは、起動時に全スキルの `name` と `description` だけを読み、依頼と照らしてどのスキルを開くかを決めます。description が弱いと、スキルの中身がどれだけよくても読まれません。

- 何をするかと、どんな依頼や場面で使うかを両方書きます。
- 三人称で書きます。「I can」「You can」は使いません。
- ユーザーが実際に言う言葉を入れます。tsumi では英語の説明の後に「日本語トリガー - 」として日本語の言い回しを並べます。日本語の文章を扱う `clear-japanese` だけは全文を日本語で書きます。
- 近いが使わない場面があれば書きます（例「Do not use merely to run an existing skill」）。
- 主な使い方を先に書きます。一覧に入れるとき、長い説明は後ろが切られます。
- 1,024文字以内です。XML タグは使えません。

`disable-model-invocation: true` を付けると、description はエージェントに見えなくなり、`/名前` でしか動きません（Claude Code と Cursor の両方のドキュメントにあります）。pstack はほぼ全スキルにこれを付けています。tsumi では、ルーターの `tsumi-mode` だけに付けます。子スキルは自動で読まれることを前提にしているので付けません。`scripts/check-skills` が、この分け方から外れたスキルをエラーにします。

## name

- 64文字以内の小文字、数字、ハイフン。ディレクトリ名と同じにします。
- `helper` や `utils` のような何をするか分からない名前は避けます。

## 本文

- 500行未満にします。詳細は `references/` に分け、SKILL.md から1階層だけたどれるようにします。
- 100行を超える参照ファイルには、先頭に目次を置きます。
- エージェントが既に知っていることは書きません。
- 重要な指示は上に置きます。会話が要約されると、スキルの先頭部分しか残らないことがあります。
- 同じものは同じ名前で呼びます。選択肢を並べず、既定を一つ示します。

## 評価

- スキルを書く前にお題を作ります。少なくとも3件です。
- description は、読むべき依頼と、近いが読むべきでない依頼の組で確かめます（`evals/cases/trigger-*.yaml`）。
- 読まれたかどうかと、読んだ後に意図どおり動いたかは、別々に確かめます。

## 出典

- Agent Skills 概要 https://platform.claude.com/docs/ja/agents-and-tools/agent-skills/overview
- Skill 作成のベストプラクティス https://platform.claude.com/docs/ja/agents-and-tools/agent-skills/best-practices
- Claude Code のスキル https://code.claude.com/docs/ja/skills

2026-10-18 に読みました。
