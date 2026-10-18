# tsumi

tsumi は、堤 大樹（Daiki Tsutsumi）のエージェント開発の考え方と tips を、エージェントが使えるスキルにしたプラグインです。Cursor と Claude Code で使えます。[pstack](https://github.com/cursor/plugins/tree/main/pstack) を土台にして、足りない分だけを足します。名前は「積み上げる」から取りました。

## 何のためのものか

業務エージェントを作るとき、間違いをプロンプトの注意書きで防ごうとすると、注意書きが増えるだけで同じ間違いが戻ってきます。tsumi は、エージェントを作る・直す・評価する作業で、修正を置く場所を順番に決めます。エージェントにこの順番を守らせ、同じ修正を二度しないようにします。

pstack は、principle、プレイブック、返信の書き方といった開発作業全般の土台を持っています。tsumi は pstack をそのまま使い、エージェント開発の部分だけを足します。

## 考え方

修正は、次の順で、できるだけ上の段に置きます。

1. **環境と道具で間違いを起こせなくする。** 選択肢が決まっているものは、自由に書かせず部品や ID から選ばせます。コードが読む出力は JSON スキーマで縛り、合わないものは受け取る側で弾きます。ID、日付、金額、宛先、定型文はテンプレートに入れ、コードで埋めます。
2. **自動チェックと回帰評価で捕まえる。** 残った間違いは、決まった検査と評価のお題で見つけます。スキルやプロンプトを変えるたびに、変更に見合った数のお題を回して前の版と比べます。
3. **プロンプトには、仕組みにできない判断だけを書く。** 依頼の意図の読み取りや、どの部品を選ぶかといった判断です。同じ修正が2回出たら、プロンプトに書き足さずに1か2へ移します。
4. **人のレビューは最後に、怪しいものだけに絞る。** 人が直した内容は修正ログに残し、次の修正の材料にします。

この順番は投資の順番です。4段階を順に終わらせる計画ではありません。

## スキル

入口は `tsumi-mode` です。`/tsumi-mode <依頼>`（Claude Code では `/tsumi:tsumi-mode <依頼>`）と打つと、tsumi の全スキルと pstack のスキルを、状況に合わせて使い分けます。

| 状況 | tsumi-mode が読むもの |
|---|---|
| エージェント、スキル、プロンプト、ツール定義、出力スキーマを設計する・直す | `agent-design-review` |
| 業務エージェントを新しく作る | New agent プレイブック（`agent-design-review` も読む） |
| エージェントの出力の失敗、評価の失敗、エージェントへの修正 | `agent-design-review` |
| スキル、プロンプト、ツール定義、スキーマを変えた | Eval プレイブック（回帰評価）。description を変えたら `scripts/check-skills` とトリガーお題も |
| 人に回す出力を決める、人の修正が届く | Review triage プレイブック |
| 日本語の文書（README、設計書、PR 説明、コミット文など） | `clear-japanese` |
| 英語の文章、文書 | pstack の `unslop`、`technical-writing` |
| それ以外（コード、設計、デバッグ、検証、PR） | pstack の `poteto-mode` の規則のまま |

各スキルは単独でも動きます。tsumi-mode を通さなくても、依頼の内容に合えばエージェントが自分で読みます。

| スキル | 単独で読まれる場面 |
|---|---|
| [`tsumi-mode`](skills/tsumi-mode/SKILL.md) | `/tsumi-mode` と打ったとき、「tsumi で」と頼んだとき。明示がなければ読まれません |
| [`agent-design-review`](skills/agent-design-review/SKILL.md) | エージェントやスキルを設計するとき、設計を見直すとき、同じ間違いや出力のぶれが続くとき |
| [`clear-japanese`](skills/clear-japanese/SKILL.md) | 「日本語を直して」「分かりやすくして」と頼んだとき、日本語の文書を整えるとき |

`agent-design-review` と `clear-japanese` は [223mle/skills](https://github.com/223mle/skills) から移しました。正本は tsumi で、223mle/skills には残しません。

## 入れ方

本体は、`~/tsumi` に置いた git の作業コピーの main です。Claude Code はこの作業コピーを直接読み、Cursor は別に置いた clone を読みます。

1. pstack を入れます。

   - Cursor では `/add-plugin pstack` を実行します。
   - Claude Code では `/plugin marketplace add cursor/plugins` を実行し、続けて `/plugin install pstack@cursor-plugins` を実行します。

2. tsumi を `~/tsumi` に clone します。

   ```bash
   git clone https://github.com/223mle/tsumi.git ~/tsumi
   ```

3. Claude Code では、`~/.claude/skills/tsumi` に `~/tsumi` へのシンボリックリンクを張ります。Claude Code は、`~/.claude/skills/` にあるプラグインをコピーせずにその場で読みます。

   ```bash
   ln -s ~/tsumi ~/.claude/skills/tsumi
   ```

4. Cursor では、`~/.cursor/plugins/local/tsumi` にもう一つ clone します。Cursor は、このフォルダの外を指すシンボリックリンクを読みません。

   ```bash
   git clone https://github.com/223mle/tsumi.git ~/.cursor/plugins/local/tsumi
   ```

5. Claude Code では新しいセッションを始めます。Cursor では、再起動するか Developer: Reload Window を実行します。スキル一覧に tsumi のスキルが出ていれば入っています。

更新するときは、`~/tsumi` と `~/.cursor/plugins/local/tsumi` で `git pull` を実行します。

tsumi を直すときは、読み込まれているコピーは直しません。`~/tsumi` から worktree を切って直し、PR を出します。

## 使い方

Cursor では、スキルを `/スキル名` で呼びます。Claude Code では、`/tsumi:tsumi-mode` のようにプラグイン名を付けます。

```text
/tsumi-mode 問い合わせメールを「請求」「解約」「その他」に分類するエージェントを作りたい
```

- 「tsumi で〜して」と頼んでも、tsumi-mode が読まれます。
- 「このエージェントが毎回ちがう表記で返してくる。どう直すのがいい？」と相談すると、tsumi-mode を通さずに `agent-design-review` が読まれます。
- 日本語の文章を貼って「読みにくいので直して」と頼むと、`clear-japanese` が清書した本文を返します。


## 開発に参加するとき

[CONTRIBUTING.md](CONTRIBUTING.md) を読んでください。設計の判断は [DESIGN.md](DESIGN.md)、評価の設計は [evals/README.md](evals/README.md) にあります。
