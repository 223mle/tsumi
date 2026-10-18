---
name: tsumi-mode
description: Daiki のエージェント開発スタイル。pstack の poteto-mode の上に乗る。道具とスキーマとテンプレートで間違いを消し、変更ごとに回帰評価を回し、プロンプトは判断だけに絞り、人は怪しいものだけ見る。Use for Daiki, /tsumi-mode, or requests to work in this style.
disable-model-invocation: true
---

# tsumi mode

pstack の `poteto-mode` に乗る薄いルーター。principle、プレイブック、返信の書き方、Autonomy、Subagents の土台は pstack にある。ここには tsumi が足す分だけを書く。pstack と食い違ったら、このファイルの gate を優先する。

## 前提

pstack が要る。最初に [references/requirements.md](references/requirements.md) で確かめる。なければ作業を始めず、ユーザーに `/add-plugin pstack` を案内して止まる。

## 最初にやること

1. todo を開く。1項目目は「pstack の `poteto-mode/SKILL.md` を全部読む」。Principles 索引もそこにある。使った principle は leaf を読んでから名指しする。
2. プレイブックを選ぶ。このスキルの `playbooks/<名前>.md` を先に探す。
   - tsumi だけにある名前なら、それを使う。
   - pstack と同じ名前なら、pstack 版を読んでから tsumi 版を読む。tsumi 版は上書き分で、食い違ったら tsumi 版が勝つ。
   - tsumi になければ pstack 版を使う。
   - 手順は pstack と同じく todo の先頭にそのまま写す。やらない手順は `skip: <理由>` を残す。
3. pstack のスキルを使うときは、このスキルの `overlays/<スキル名>.md` を探す。あれば pstack 本体を読んだあとに読み、両方に従う。食い違ったら overlay が勝つ。別のスキルの途中で使うとき（`/technical-writing` の中で `/unslop` を当てるときなど）も同じ。
4. 下の tsumi gates を当てる。

## tsumi gates

### 修正の段

修正指示、評価の失敗、エラーが出たら、次の順で直せるかを試す。上の段で直せるなら、下の段には書かない。

1. **道具と環境。** 選択肢が有限なら、自由文ではなく列挙や ID 付きの部品から選ばせる。後段のコードが読む出力は JSON スキーマで縛り、スキーマ外は境界で弾く。黙って直さない。スキーマはコードの型と同じ元から作る。ID、日付、金額、宛先、定型文はモデルに書かせず、テンプレートの穴をコードで埋める。
2. **自動チェックと回帰評価。** バリデータ、テスト、評価お題で捕まえる。お題は直す前の版で落ちることを確かめてから足す。
3. **プロンプト。** 1と2で強制できない判断だけ書く。書くなら、判断が要る理由を一つと失敗例を一つ。pstack の `principle-encode-lessons-in-structure` を読む。
4. **人のレビュー。** 全件は回さない。スキーマ違反、バリデータの警告、評価で不安定な入力に近いもの、信頼度の低い出力だけを回す。人が直した内容は修正ログに残す。

返信には、直した段と、上の段で直せなかった理由を一行ずつ書く。

### 同じ修正の2回目

同じクラスの修正が2回目に出たら、プロンプトへの追記で済ませない。段1か段2に移す。移せなかったら理由を修正ログの `moved_to` と `evidence` に書く。開発中のエージェントの誤りなら `playbooks/harden.md`、リポジトリのコードの誤りなら pstack の `/correct` を使う。

### 変更ごとの回帰評価

スキル、プロンプト、ツール定義、スキーマを変えたら `playbooks/eval.md` を通す。結果を見るまで完了と言わない。回帰が出たら、pstack の `principle-explain-the-number` に沿って原因を説明できるまで出さない。

### 修正ログ

ユーザーから修正を受けたら、修正ログに1行足す。形は [references/corrections-template.tsv](references/corrections-template.tsv)。置き場所が決まるまでは作業中のリポジトリ直下の `corrections.tsv` に書き、コミットしない。同じ `class` の行が2つになったら「同じ修正の2回目」を当てる。

### 顧客データ

顧客のデータや固有名を、評価お題、修正ログ、コミット、外部への送信に入れる前に止まり、ユーザーに確かめる。pstack の Autonomy の「必ず止まる」に足す項目。

## 返信

pstack の Writing the reply に従う。日本語で書くときは `overlays/unslop.md` の J 規則も当てる。

## サブエージェント

pstack が `poteto-agent` を使えと言う場面では `tsumi-agent` を使う。`tsumi-agent` はこのファイルと pstack の `poteto-mode` の両方を読む。`how`、`why`、`reflect` など、pstack のスキルが自分で指定するサブエージェントの種類は変えない。

## tsumi のプレイブック

- **New agent**（`playbooks/new-agent.md`）。業務エージェントを新しく作る。
- **Harden**（`playbooks/harden.md`）。開発中のエージェントの誤りの一類を、段1から順に潰す。
- **Review triage**（`playbooks/review-triage.md`）。人に回す出力の選び方と、人の修正をログとお題に戻す流れ。
- **Eval**（`playbooks/eval.md`）。pstack の Eval プレイブックへの上書き。tsumi の `evals/` ハーネスで回す。

それ以外は pstack の Playbooks 索引から選ぶ。

## pstack のスキルへの上書き

| pstack のスキル | tsumi の扱い |
|---|---|
| `/unslop` | `overlays/unslop.md` で日本語の規則を足す |
| `/technical-writing` | `overlays/technical-writing.md` で日本語の文書の扱いを足す |
| `/correct` | `overlays/correct.md` で開発中のエージェントの誤りを Harden に回す |
| `/reflect` | `overlays/reflect.md` で Accepted の各行に評価お題の欄を足す |
| `/bro`、`/sharpen`、`/in-your-own-words` ほか | 上書きなし。pstack のものをそのまま使う |
