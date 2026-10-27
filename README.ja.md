# tsumi

[English](README.md) | **日本語**

tsumi は、堤 大樹（Daiki Tsutsumi）のエージェント開発の考え方と tips を、エージェントが使えるスキルにしたプラグインです。Cursor と Claude Code で使えます。[pstack](https://github.com/cursor/plugins/tree/main/pstack) を土台にして、足りない分だけを足します。名前は「積み上げる」から取りました。

業務エージェントを作るとき、間違いをプロンプトの注意書きで防ごうとすると、注意書きが増えるだけで同じ間違いが戻ってきます。tsumi は、エージェントを作る・直す作業を評価から始め、修正を置く場所を順番に決めます。エージェントにこの順番を守らせ、同じ修正を二度しないようにします。

pstack は、principle、プレイブック、返信の書き方といった開発作業全般の土台を持っています。tsumi は pstack をそのまま使い、エージェント開発の部分だけを足します。

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

5. Claude Code の `~/.claude/settings.json` に、セッション開始時のフックを足します。新しいセッションを始めるたびに `scripts/sync-installs` が動き、`~/tsumi` と `~/.cursor/plugins/local/tsumi` を main の最新にします。

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

   取り込むのは、main にいて未コミットの変更がない作業コピーだけです。結果は `~/Library/Logs/tsumi-sync.log` に残ります。Claude Code を開かずに Cursor だけを使うときは、Cursor 側は更新されません。

6. Claude Code では新しいセッションを始めます。Cursor では、再起動するか Developer: Reload Window を実行します。スキル一覧に tsumi のスキルが出ていれば入っています。

tsumi を直すときは、読み込まれているコピーは直しません。`~/tsumi` から worktree を切って直し、PR を出します。

### Codex だけでスキルを自動更新する

macOS では、作業ブランチで次を実行します。

```bash
python3 scripts/install-codex-sync
```

インストーラーは、マージ済みの最新版を取得し、Codex が読む3つの tsumi スキルを専用コピーへのリンクに切り替えます。`~/.codex/hooks.json` には、チャット開始・再開時に更新するフックを追加します。既存のフックは残します。設定後、Codex の Hooks 設定でこのフックを一度確認して信頼してください。信頼するまでは自動実行されません。

更新用コピーは `~/.codex/tsumi/current` に置きます。フックは GitHub の main を読み取るだけで、`~/tsumi`、Cursor 用のコピー、ローカル・リモートの main ブランチは変更しません。更新が終わってから読み込み先を切り替え、取得や検査に失敗した場合は旧版を維持します。実行中の会話に読み込み済みの指示は取り消しません。

- 更新ログは `~/.codex/tsumi/update.log` に残ります。
- 導入前のリンクとフック設定は `~/.codex/tsumi/install-backup.json` に保存します。
- Codex が変更を検知しない場合は再起動します。自動更新を止める場合は、Hooks 設定で対象のフックを無効にします。
- 更新スクリプト自体は自動更新しません。スクリプトを更新する場合は、インストーラーを実行し直します。
- `clear-japanese` を `unslop` に改名した版は、古い更新スクリプトでは取り込めず、旧版のままになります。インストーラーを一度実行し直してください。このとき、pstack の `unslop` を指す `~/.agents/skills/unslop` は tsumi の `unslop` へのリンクに置き換わり、`~/.agents/skills/clear-japanese` は消えます。置き換え前のリンクは `install-backup.json` に残ります。

この設定は Claude Code の起動に依存しません。既存の Claude Code・Cursor 向けの同期設定も変更しません。

## 使い方

作業の最初に `/tsumi-mode`（Claude Code では `/tsumi:tsumi-mode`）を打ちます。tsumi-mode は依頼を読み、tsumi のスキルと pstack のスキルを状況に合わせて使い分けます。

```text
/tsumi-mode 問い合わせメールを「請求」「解約」「その他」に分類するエージェントを作りたい
```

- 会話が長くなると、tsumi-mode の効き目は薄れます。新しい作業を始めるときは、もう一度コマンドで呼びます。Cursor では、`/` メニューで tsumi-mode を選んで Option+Enter（Windows は Alt+Enter）を押すと、毎ターン読み込まれる Custom Mode になります。
- 「このエージェントが毎回ちがう表記で返してくる。どう直すのがいい？」と相談すると、tsumi-mode を通さずに `agent-design-review` が読まれます。
- 日本語の文章を貼って「読みにくいので直して」と頼むと、`unslop` が清書した本文を返します。メモを渡して「手順書を書いて」と頼んだときも、`unslop` が読まれます。

## スキル

入口は `tsumi-mode` で、コマンドで呼んだときだけ動きます。残りの3つは単独でも動き、tsumi-mode を通さなくても、依頼の内容に合えばエージェントが自分で読みます。

| スキル | 単独で読まれる場面 |
|---|---|
| [`tsumi-mode`](skills/tsumi-mode/SKILL.md) | `/tsumi-mode`（Claude Code では `/tsumi:tsumi-mode`）と打ったときだけ。「tsumi で」と書くだけでは読まれません |
| [`agent-design-review`](skills/agent-design-review/SKILL.md) | エージェントやスキルを設計するとき、設計を見直すとき、同じ間違いや出力のぶれが続くとき |
| [`unslop`](skills/unslop/SKILL.md) | 日本語の文書を書くとき、「日本語を直して」「分かりやすくして」と頼んだとき |
| [`tsumi-reflect`](skills/tsumi-reflect/SKILL.md) | 会話の最後に「reflect して」と言ったとき。週報や振り返りの文書を書く依頼では読まれません |

<details>
<summary>状況ごとに tsumi-mode が読むもの</summary>

| 状況 | tsumi-mode が読むもの |
|---|---|
| エージェント、スキル、プロンプト、ツール定義、出力スキーマを設計する・直す | `agent-design-review` |
| 業務エージェントを新しく作る | New agent プレイブック（`agent-design-review` も読む） |
| エージェントの出力の失敗、評価の失敗、エージェントへの修正 | `agent-design-review` |
| 動かして証拠を取る手段がないエージェントを作る・直す | pstack の `create-verification-skill`（tsumi の overlay 付き） |
| reflect と言われた、この会話の学びを tsumi に戻す | `tsumi-reflect`（pstack の `reflect` に tsumi の追加分を当てる） |
| スキル、プロンプト、ツール定義、スキーマを変えた | Eval プレイブック（回帰評価）。description を変えたら `scripts/check-skills` とトリガーお題も |
| 人に回す出力を決める、人の修正が届く | Review triage プレイブック |
| 日本語の文書を書く・直す（README、設計書、ADR、手順書、PR 説明など。コミット文は除く） | `unslop` |
| それ以外（コード、設計、デバッグ、検証、PR） | pstack の `poteto-mode` の規則のまま |

</details>

pstack の `unslop` と `technical-writing` は使いません。pstack がこの2つを呼ぶ場面では、人が読む日本語の文書なら tsumi の `unslop` を使い、コミット文とチャットの返信にはどれも使いません。tsumi の `unslop` は、pstack の `technical-writing` の考え方のうち日本語にも当てはまるもの（文書の種類を先に決める、コードの名前をそのまま書く、など）を取り込んでいます。unslop の候補検出コマンドと hook の役割は、[文書の検査](docs/unslop-checks.md)を参照してください。

`agent-design-review` と `unslop`（移したときの名前は `clear-japanese`）は [223mle/skills](https://github.com/223mle/skills) から移しました。正本は tsumi で、223mle/skills には残しません。

## 考え方

### 最初に評価を用意する

エージェントを作る・直す・変えるときは、最初に評価を用意して、目指す方向を決めます。先に合格の定義（A）を書き、次に実物を動かして証拠を取る仕組み（B）を用意します。

- **A 合格の定義。** 実際の入力ごとに、合格になる出力、その出力を誰がどう使うか、間違えたときに何が起きるかを書きます。定量的か定性的かは、誰が判定するか（コード、別のモデル、人）の違いとして扱います。
- **B 実物を動かして証拠を取る仕組み。** 出力そのもの、送ったメールや書き込んだ行などの副作用、スライドの画像のような描画結果を証拠として残します。出力がそのまま証拠になるなら、実行コマンドと証拠の置き場所を決めれば足ります。それ以上が要るときは、pstack の `create-verification-skill` を tsumi の overlay 付きで使います。

判定は、手で作った正しい出力を通し、わざと壊した出力を落とすと確かめてから使います。ここで作った評価は、そのまま次の節の2段目の回帰評価になります。

### 修正はできるだけ上の段に置く

修正は、次の順で、できるだけ上の段に置きます。

1. **環境と道具で間違いを起こせなくする。** 選択肢が決まっているものは、自由に書かせず部品や ID から選ばせます。コードが読む出力は JSON スキーマで縛り、合わないものは受け取る側で弾きます。ID、日付、金額、宛先、定型文はテンプレートに入れ、コードで埋めます。
2. **自動チェックと回帰評価で捕まえる。** 残った間違いは、決まった検査と評価のお題で見つけます。スキルやプロンプトを変えるたびに、変更に見合った数のお題を回して前の版と比べます。
3. **プロンプトには、仕組みにできない判断だけを書く。** 依頼の意図の読み取りや、どの部品を選ぶかといった判断です。同じ修正が2回出たら、プロンプトに書き足さずに1か2へ移します。
4. **人のレビューは最後に、怪しいものだけに絞る。** 人が直した内容は修正ログに残し、次の修正の材料にします。

この順番は投資の順番です。4段階を順に終わらせる計画ではありません。

### トップの実践と対話の記録から育てる

tsumi は、2つの材料から育てます。

- **トップの実践。** 考え方は、poteto の投稿や pstack のような、トップの開発者の実践を起点にしています。今後もトップのブログやスキルから取り込みます。
- **Daiki とエージェントの対話の記録。** 会話の最後に「reflect して」と言うと、`tsumi-reflect` がその会話から学びを拾い、スキルの修正と修正ログの行を1つの PR にまとめます。材料にするのは、reflect をしたスレッドだけです。修正ログには、顧客名や顧客データを書きません。

修正ログに同じ種類の行が2つたまったら、プロンプトに書き足さずに仕組みへ移します。まだ決まっていない評価の合否基準や、人に回す出力の目印も、この記録の傾向から決めます。

## 開発に参加するとき

[CONTRIBUTING.md](CONTRIBUTING.md) を読んでください。設計の判断は [DESIGN.md](DESIGN.md)、評価の設計は [evals/README.md](evals/README.md) にあります。
