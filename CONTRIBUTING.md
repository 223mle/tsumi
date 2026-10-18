# 変更のしかた

## ブランチと PR

- 変更はブランチを切り、PR で出します。`main` へ直接 push しません。
- 最初に `scripts/install-hooks` を実行します。`main` への push を止める pre-push フックが入ります。

## スキルを変えたとき

1. `scripts/check-skills` を実行します。name の形、description の長さ、いつ使うかの記述、本文の行数、リンク切れを確かめます。
2. description を変えたら、`evals/cases/trigger-*.yaml` のお題で、読むべき依頼で読み、読むべきでない依頼で読まないことを確かめます。
3. 本文を変えたら、`evals/README.md` の手順で変更前と変更後を比べます。

スキルを足したら、`skills/tsumi-mode/SKILL.md` の Non-negotiables に「状況 → `../<名前>/SKILL.md`」の1行を足します。足し忘れると `scripts/check-skills` が落ちます。

description の書き方は [docs/skill-authoring.md](docs/skill-authoring.md) にまとめています。

## 修正ログ

tsumi 自体への指摘は、リポジトリ直下の `corrections.tsv` に1行ずつ足します。列は `skills/tsumi-mode/references/corrections-template.tsv` と同じです。同じ `class` が2行になったら、プロンプトへの書き足しではなく、スクリプトか評価のお題に移します。
