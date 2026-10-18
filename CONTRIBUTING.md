# 変更のしかた

## ブランチと PR

- 変更は `~/tsumi` から worktree とブランチを切り、PR で出します。`main` へ直接 push しません。Cursor や Claude Code が読み込んでいるコピーは直しません。
- 最初に `scripts/install-hooks` を実行します。`main` への push を止める pre-push フックが入ります。

## スキルを変えたとき

1. `scripts/check-skills` を実行します。PR を出すと、GitHub Actions も同じ検査を回します。name の形、description の長さ、いつ使うかの記述、本文の行数、リンク切れを確かめます。
2. description を変えたら、`evals/cases/trigger-*.yaml` のお題で、読むべき依頼で読み、読むべきでない依頼で読まないことを確かめます。回し方は `evals/README.md` の「回し方」にあります。作業の途中では関わるお題だけを1回ずつ回し、全件を3回ずつ回すのは PR を仕上げる最後の1回だけにします。
3. 本文を変えたら、変更前と変更後で同じお題を回し、結果を比べます。

スキルを足したら、`skills/tsumi-mode/SKILL.md` の Non-negotiables に「状況 → `../<名前>/SKILL.md`」の1行を足します。足し忘れると `scripts/check-skills` が落ちます。

description の書き方は [docs/skill-authoring.md](docs/skill-authoring.md) にまとめています。

## 修正ログ

tsumi 自体への指摘は、リポジトリ直下の `corrections.tsv` に1行ずつ足します。列は `skills/tsumi-mode/references/corrections-template.tsv` と同じです。同じ `class` が2行になったら、プロンプトへの書き足しではなく、スクリプトか評価のお題に移します。
