# tsumi

tsumi は、堤 大樹（Daiki Tsutsumi）のエージェント開発の考え方と tips を、エージェントが使えるスキルにした Cursor プラグインです。[pstack](https://github.com/cursor/plugins/tree/main/pstack) を土台にして、足りない分だけを足します。名前は「積み上げる」から取りました。

## 何のためのものか

業務エージェントを作るとき、間違いをプロンプトの注意書きで防ごうとすると、注意書きが増えるだけで同じ間違いが戻ってきます。tsumi は、エージェントを作る・直す・評価する作業で、修正を置く場所を順番に決めます。エージェントにこの順番を守らせ、同じ修正を二度しないようにします。

pstack は、principle、プレイブック、返信の書き方といった開発作業全般の土台を持っています。tsumi は pstack をそのまま使い、エージェント開発の部分だけを足します。

## 考え方

修正は、次の順で、できるだけ上の段に置きます。

1. **環境と道具で間違いを起こせなくする。** 選択肢が決まっているものは、自由に書かせず部品や ID から選ばせます。コードが読む出力は JSON スキーマで縛り、合わないものは受け取る側で弾きます。ID、日付、金額、宛先、定型文はテンプレートに入れ、コードで埋めます。
2. **自動チェックと回帰評価で捕まえる。** 残った間違いは、決まった検査と評価のお題で見つけます。スキルやプロンプトを変えるたびに、20〜50件のお題を回して前の版と比べます。
3. **プロンプトには、仕組みにできない判断だけを書く。** 依頼の意図の読み取りや、どの部品を選ぶかといった判断です。同じ修正が2回出たら、プロンプトに書き足さずに1か2へ移します。
4. **人のレビューは最後に、怪しいものだけに絞る。** 人が直した内容は修正ログに残し、次の修正の材料にします。

この順番は投資の順番です。4段階を順に終わらせる計画ではありません。

## スキル

| スキル | エージェントが読む場面 |
|---|---|
| [`tsumi-mode`](skills/tsumi-mode/SKILL.md) | `/tsumi-mode` と打ったときや、「tsumi で」と頼んでエージェントやスキルを作る・直す・評価するとき。pstack の `poteto-mode` を読み、上の順番と修正ログなどの規則を足して進めます |
| [`agent-design-review`](skills/agent-design-review/SKILL.md) | エージェントやスキルを設計するとき、設計を見直すとき、同じ間違いや出力のぶれが続くとき。モデルが繰り返している判断を、道具、部品、スキーマ、テンプレートへ移します |
| [`clear-japanese`](skills/clear-japanese/SKILL.md) | 「日本語を直して」「分かりやすくして」と頼んだときや、設計書、README、PR 説明などの日本語を整えるとき。意味と文体を保って清書します |

`agent-design-review` と `clear-japanese` は [223mle/skills](https://github.com/223mle/skills) から移しました。

## 入れ方

1. pstack を入れます。

   ```text
   /add-plugin pstack
   ```

2. tsumi はマーケットプレイスに出していません。リポジトリを `~/.cursor/plugins/local/tsumi` に写します。Cursor は、このフォルダの外を指すシンボリックリンクを読みません。

   ```bash
   git clone https://github.com/223mle/tsumi.git ~/src/tsumi
   rsync -a --delete --exclude .git ~/src/tsumi/ ~/.cursor/plugins/local/tsumi/
   ```

3. Cursor を再起動するか、Developer: Reload Window を実行します。Customize に tsumi のスキルが出ていれば入っています。

更新するときは、`git pull` のあとに手順2の `rsync` をもう一度実行します。

## 使い方

- 「tsumi で、問い合わせメールを分類するエージェントを作りたい」のように頼みます。`/tsumi-mode` と打っても同じです。
- 「このエージェントが毎回ちがう表記で返してくる。どう直すのがいい？」と相談すると、`agent-design-review` が読まれます。
- 日本語の文章を貼って「読みにくいので直して」と頼むと、`clear-japanese` が清書した本文を返します。

## 開発に参加するとき

[CONTRIBUTING.md](CONTRIBUTING.md) を読んでください。設計の判断は [DESIGN.md](DESIGN.md)、評価の設計は [evals/README.md](evals/README.md) にあります。
