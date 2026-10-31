# tsumi

[English](README.md) | **日本語**

## これは何？

tsumi は、[223mle](https://github.com/223mle) がエージェント開発で使っている考え方と tips をまとめたスキル集です。Cursor と Claude Code のプラグインとして使えます。[pstack](https://github.com/cursor/plugins/tree/main/pstack) を土台にしていて、エージェント開発に必要な部分だけを足しています。名前は「積み上げる」から取りました。

業務エージェントの間違いをプロンプトの注意書きで防ごうとすると、注意書きが増えるばかりで、同じ間違いはまた起きます。tsumi は、エージェントを作る・直すときに最初に評価を用意させ、修正をどこに置くかを決まった順番で決めさせます。同じ修正を二度しないためです。

pstack は、principle、プレイブック、返信の書き方など、開発作業全般の土台を持っています。tsumi は pstack をそのまま使い、その上にエージェント開発の部分を足します。

## インストール

tsumi は pstack の上で動くため、先に pstack をインストールしてください。

```text
# Cursor
/add-plugin pstack

# Claude Code
/plugin marketplace add cursor/plugins
/plugin install pstack@cursor-plugins
```

tsumi の本体は、`~/tsumi` に clone した作業コピーの main です。Claude Code はこの作業コピーをそのまま読み込み、Cursor は別の場所に clone したコピーを読み込みます。

```bash
git clone https://github.com/223mle/tsumi.git ~/tsumi
```

### Claude Code

`~/.claude/skills/` にシンボリックリンクを作成します。Claude Code は、このディレクトリにあるプラグインをコピーせずにそのまま読み込みます。

```bash
ln -s ~/tsumi ~/.claude/skills/tsumi
```

新しいセッションを開き、スキル一覧に tsumi のスキルが表示されればインストール完了です。

### Cursor

Cursor はプラグインのフォルダの外を指すシンボリックリンクを読み込まないため、`~/.cursor/plugins/local/` にもう1つ clone します。

```bash
git clone https://github.com/223mle/tsumi.git ~/.cursor/plugins/local/tsumi
```

Cursor を再起動するか、コマンドパレットから「Developer: Reload Window」を実行してください。スキル一覧に tsumi のスキルが表示されればインストール完了です。

### 自動で最新版に更新する

Claude Code の `~/.claude/settings.json` に次のフックを追加すると、セッションを開くたびに `scripts/sync-installs` が実行され、`~/tsumi` と `~/.cursor/plugins/local/tsumi` が main の最新版に更新されます。

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

更新されるのは、main ブランチにいて未コミットの変更がない作業コピーだけです。実行結果は `~/Library/Logs/tsumi-sync.log` に記録されます。Cursor 用のコピーもこのフックで更新されるため、Claude Code を開かずに Cursor だけを使っている間は更新されません。

### Codex

`html-explainer`を追加した版へ更新した後は、インストーラーを一度再実行して新しいスキルのリンクを作成します。

macOS では、作業ブランチで次のコマンドを実行すると、Codex 用の自動更新を設定できます。この設定は、Claude Code・Cursor 向けの設定とは独立しています。

```bash
python3 scripts/install-codex-sync
```

インストーラーは次の2つを行います。

- マージ済みの最新版を `~/.codex/tsumi/current` に取得し、Codex が読み込む4つの tsumi スキルを、そこへのリンクに切り替えます。
- `~/.codex/hooks.json` に、チャットの開始・再開時に更新するフックを追加します。既存のフックはそのまま残ります。

設定が終わったら、Codex の Hooks 設定でこのフックを一度確認し、信頼してください。信頼するまでは自動で実行されません。

フックは GitHub の main を読み取るだけで、`~/tsumi`、Cursor 用のコピー、ローカル・リモートの main ブランチには触れません。更新が終わってから読み込み先を切り替えるため、取得や検査に失敗したときは旧版のまま動きます。実行中の会話には、更新は反映されません。

<details>
<summary>Codex の自動更新についての補足</summary>

- 更新ログは `~/.codex/tsumi/update.log` に記録されます。
- 導入前のリンクとフック設定は `~/.codex/tsumi/install-backup.json` に保存されます。
- Codex が変更を検知しないときは、Codex を再起動してください。自動更新を止めるときは、Hooks 設定でこのフックを無効にします。
- 更新スクリプト自体は自動では更新されません。スクリプトを新しくしたいときは、インストーラーを再実行してください。
- `clear-japanese` を `unslop` に改名した版は、古い更新スクリプトでは取り込めず、旧版のままになります。インストーラーを一度再実行してください。このとき、pstack の `unslop` を指す `~/.agents/skills/unslop` は tsumi の `unslop` へのリンクに置き換わり、`~/.agents/skills/clear-japanese` は削除されます。置き換え前のリンクは `install-backup.json` に残ります。

</details>

## 使い方

作業を始めるときに、依頼の前に `/tsumi-mode`（Claude Code では `/tsumi:tsumi-mode`）を付けます。tsumi-mode が依頼の内容を読み、tsumi と pstack のスキルから必要なものを選んで使います。

```text
/tsumi-mode 問い合わせメールを「請求」「解約」「その他」に分類するエージェントを作りたい
```

- 会話が長くなると、tsumi-mode の指示が効きにくくなります。新しい作業を始めるときは、もう一度 `/tsumi-mode` を付けて依頼してください。Cursor では、`/` メニューで tsumi-mode を選んで Option+Enter（Windows は Alt+Enter）を押すと、毎ターン読み込まれる Custom Mode になります。
- 「このエージェントが毎回ちがう表記で返してくる。どう直すのがいい？」と相談すると、tsumi-mode を付けなくても `agent-design-review` が読み込まれます。
- 日本語の文章を貼って「読みにくいので直して」と頼むと、`unslop` が清書した本文を返します。メモを渡して「手順書を書いて」と頼んだときも、`unslop` が読み込まれます。

## スキル一覧

入口は `tsumi-mode` で、コマンドで呼んだときだけ動きます。残りの3つは単独でも動き、tsumi-mode を付けなくても、依頼の内容に合えばエージェントが自分で読み込みます。

| スキル | 単独で読み込まれる場面 |
|---|---|
| [`tsumi-mode`](skills/tsumi-mode/SKILL.md) | `/tsumi-mode`（Claude Code では `/tsumi:tsumi-mode`）と打ったときだけ。「tsumi で」と書くだけでは読み込まれません |
| [`agent-design-review`](skills/agent-design-review/SKILL.md) | エージェントやスキルを設計するとき、設計を見直すとき、同じ間違いや出力のぶれが続くとき |
| [`unslop`](skills/unslop/SKILL.md) | 日本語の文書を書くとき、「日本語を直して」「分かりやすくして」と頼んだとき |
| [`html-explainer`](skills/html-explainer/SKILL.md) | 日本語の解説・設計説明を、図やアニメーションで仕組みが分かる単独HTML資料にするとき。冒頭に要点を置き、シーケンス図や経路図を1手ずつ進め、折れ線で逆転点を示し、用語と図を連動させます。図はスマートフォン用の配置にも切り替わります。unslopと組み合わせ、生成後に実描画を確認します |
| [`tsumi-reflect`](skills/tsumi-reflect/SKILL.md) | 会話の最後に「reflect して」と言ったとき。週報や振り返りの文書を書く依頼では読み込まれません |

<details>
<summary>状況ごとに tsumi-mode が読み込むもの</summary>

| 状況 | tsumi-mode が読み込むもの |
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

`agent-design-review` と `unslop`（移したときの名前は `clear-japanese`）は [223mle/skills](https://github.com/223mle/skills) から移しました。正本は tsumi で、223mle/skills には残していません。

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
- **223mle とエージェントの対話の記録。** 会話の最後に「reflect して」と言うと、`tsumi-reflect` がその会話から学びを拾い、スキルの修正と修正ログの行を1つの PR にまとめます。材料にするのは、reflect をしたスレッドだけです。修正ログには、顧客名や顧客データを書きません。

修正ログに同じ種類の行が2つたまったら、プロンプトに書き足さずに仕組みへ移します。まだ決まっていない評価の合否基準や、人に回す出力の目印も、この記録の傾向から決めます。

## コントリビュート

[CONTRIBUTING.md](CONTRIBUTING.md) を読んでください。設計の判断は [DESIGN.md](DESIGN.md)、評価の設計は [evals/README.md](evals/README.md) にあります。

tsumi を修正するときは、読み込まれているコピーを直接編集しないでください。`~/tsumi` から worktree を作って修正し、PR を出してください。
