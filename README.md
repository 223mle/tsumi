# tsumi

tsumi は「積み上げる」の「積み」から取った名前。[pstack](https://github.com/cursor/plugins/tree/main/pstack) の上に、エージェント開発で足りない分だけを積む。

pstack が前提。tsumi だけでは動かない。

クラスメソッドの AI 駆動開発フレームワーク [classmethod/tsumiki](https://github.com/classmethod/tsumiki) とは別物で、関係はない。

## 入れ方

pstack は公式マーケットプレイスから入れる。

```text
/add-plugin pstack
```

tsumi は private リポジトリで、マーケットプレイスには出していない。手元では Cursor CLI の `--plugin-dir` で読ませる。`--plugin-dir` は複数指定できるので、pstack のコピーも一緒に渡せる。

```bash
cursor-agent --plugin-dir ~/src/pstack --plugin-dir ~/src/tsumi
```

Cursor の IDE で private のプラグインを入れる手順は、まだ確かめていない。

## 何を足すか

pstack の principle、プレイブック、返信の書き方はそのまま使う。tsumi が足すのは、エージェントを作るときの直し方の順番。

1. 道具と環境で間違いを消す。選択肢は選ばせる。出力は JSON スキーマで縛る。固定値はテンプレートで埋める。
2. 自動チェックと回帰評価で捕まえる。スキルやプロンプトを変えるたびにお題を回す。
3. 1と2で強制できない判断だけをプロンプトに書く。同じ修正が2回出たら1か2に移す。
4. 人のレビューは最後に、怪しいものだけ。人が直した内容はログに残す。

## スキル

| スキル | 使うとき |
|---|---|
| [`/tsumi-mode`](skills/tsumi-mode/SKILL.md) | エージェント開発の作業の頭に付ける。pstack の `poteto-mode` に tsumi の gate を足して動く |

tsumi のプレイブックは New agent、Harden、Review triage、Eval（pstack への上書き）の4本。`skills/tsumi-mode/playbooks/` にある。

pstack の `/unslop`、`/technical-writing`、`/correct`、`/reflect` は、tsumi-mode の中で使うと `skills/tsumi-mode/overlays/` の上書き分も読む。pstack 本体のファイルは変えない。

## サブエージェント

[`tsumi-agent`](agents/tsumi-agent.md)。tsumi-mode と pstack の poteto-mode の両方を読んでから作業する。

## 評価

`evals/` に回帰評価の設計と雛形がある。ハーネスは未実装。設計は [evals/README.md](evals/README.md)。

## main を守る

変更はブランチを切って PR で出す。main に直接 push しない。

GitHub の無料プランの private リポジトリでは、ブランチ保護も rulesets も使えなかった（2026-10-18、API が HTTP 403 を返した）。代わりに手元の pre-push フックで main への push を止める。clone したら一度だけ次を実行する。

```bash
scripts/install-hooks
```

フックは手元だけの仕組みで、`git push --no-verify` で外せる。GitHub 側では止まらない。

## 設計

[DESIGN.md](DESIGN.md)。

## ライセンス

未決。このリポジトリは pstack の文章を写していない。DESIGN.md で pstack と dyl-stack の文を短く引用している箇所があり、その著作権表示は DESIGN.md の末尾に置いた。
