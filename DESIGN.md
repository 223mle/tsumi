# tsumi 設計

更新 2026-10-18（JST）。

ラベルの意味は次の通り。

- measured は、ファイルや投稿を読んで確かめたこと。
- inferred は、読んだものから推したこと。
- guess は、確かめていない予想。

## 0. 決まったこと

- プラグイン名は `tsumi`。ルーターは `tsumi-mode`。
- リポジトリは GitHub の private リポジトリ `223mle/tsumi`。
- pstack を前提にして、足りない分だけ足す。dyl-stack と同じ考え方。
- **主役は Daiki のエージェント開発の考え方と tips をスキルにすること**（2026-10-18 の Daiki の指摘で決まった）。pstack の汎用スキルへの上書き（overlay）は脇役にした。
- `agent-design-review` と `clear-japanese` の正本は tsumi にする。223mle/skills と、個人のスキルフォルダ（`~/.claude/skills`、`~/.codex/skills`）からは消す（2026-10-18 の Daiki の決定）。
- tsumi-mode はコマンド専用（`disable-model-invocation: true`）にし、子スキルは description で自動に発動させる（同日の Daiki の決定。4.4）。
- pstack の `unslop` は使わない。Daiki は英語の文章を書かないため（同日の Daiki の決定）。pstack が unslop を呼ぶ箇所（Non-negotiables とプレイブック）では、人が読む日本語の文書なら clear-japanese を使い、チャットの返信にはどちらも使わない。
- マージした変更は、Claude Code の SessionStart フックが `scripts/sync-installs` を呼んで、`~/tsumi` と Cursor 用の clone に取り込む。手で `git pull` しない（同日の Daiki の決定）。
- tsumi を使う環境は Cursor と Claude Code の2つ（同日の Daiki の決定）。本体は `~/tsumi` の main にする。Claude Code は `~/.claude/skills/tsumi` のシンボリックリンクから読み、Cursor は `~/.cursor/plugins/local/tsumi` の clone から読む。tsumi を直すときは `~/tsumi` から worktree を切り、PR を出す。
- 優先順位は次の4段。tsumi の背骨にする。
  1. 環境と道具で間違いを起こせなくする（部品から選ばせる、JSON スキーマで縛る、テンプレートで値を固定する）。
  2. 自動チェックと回帰評価（スキルを変えるたびに、変更に見合った数のお題を回す）。
  3. 仕組みにできない判断だけをプロンプトに最小限書く。同じ修正が2回出たら1か2へ移す。
  4. 人のレビューは最後で、怪しいものだけ。修正はログに残す。

## 1. 読んだもの

- pstack v0.15.25（`/workspace/plugins/pstack/`）。構造の要約は前の版の DESIGN.md 1章（measured）。
- dyl-stack（`cursor/plugins` の `dyl-stack/`、最新コミット fae2c6e、2026-09-30 09:58 JST）。`dyl-mode/SKILL.md`、`references/requirements.md`、`playbooks/opening-a-pr.md`、`agents/dyl-agent.md`、README を GitHub の raw から読んだ（measured）。
- 223mle/skills（public、最新コミット 43e6320、2026-10-18 00:06 JST）。7スキルの SKILL.md と、clear-japanese と agent-design-review の参照ファイルを全部読んだ（measured）。
- Agent Skills の公式ドキュメント3ページ。要点は `docs/skill-authoring.md`（measured）。
- poteto の投稿 2111133080526495985。原文と図は box の `/workspace/dstack/research/` にある。図は poteto の著作物なので、このリポジトリには入れていない。

## 2. pstack の構造（要点、measured）

- `.cursor-plugin/plugin.json` に `skills: "./skills/"` と `agents: "./agents/"` を書く。
- ルーター `poteto-mode` は、状況ごとに呼ぶスキルの一覧（Non-negotiables）と、principle とプレイブックの索引だけを持つ。
- プレイブック23本はスキルではなく、`poteto-mode/playbooks/` の参照ファイル。合ったものの手順を todo の先頭にそのまま写させる。
- principle 24本は9〜34行の短い leaf スキル。返信で、使った principle と変わった選択を名指しさせる。
- 54スキル中53本が `disable-model-invocation: true`。スラッシュ専用でスキル一覧に出ない。

## 3. dyl-stack の上乗せのしかた（measured）

- スキルは5本だけ。`dyl-mode`、`dyl-ready-pr`、`dyl-review`、`build-figma`、`principle-the-algorithm`。
- `dyl-mode` は自分を「Thin router over pstack's `poteto-mode`」と書く。共有の principle とプレイブックは pstack から読ませ、内容を写さない。
- **gate。** `dyl-mode` の中に Dylan 固有の規則を「Dylan gates」として並べ、pstack と食い違ったら gate が勝つと書く。例は「返信の既定の声は `/bro`」。pstack の Writing the reply と `unslop` は残したまま、gate で上書きしている。
- **同名プレイブックの上書き。** `dyl-mode/playbooks/` に pstack と同じ名前のファイル（`bug-fix.md`、`feature.md`、`opening-a-pr.md`）を置く。中身は「pstack 版を先に読め。そのあとこの gate を当てる。食い違ったらこちらが勝つ」。pstack の本体は変えない。
- **前提の確認。** `references/requirements.md` に、pstack が入っているかの見分け方（スキル一覧に `setup-pstack` があるか）と、一覧に出ない pstack のスキルのパス（`<setup-pstack のディレクトリ>/../<名前>/SKILL.md`）を書く。なければ止めて `/add-plugin` を案内する。
- **サブエージェント。** `dyl-agent` は「dyl-mode を読み、次に pstack の poteto-mode を読む」とだけ書く。
- pstack のスキルの別名（`dyl-unslop` のようなもの）は作っていない。

## 4. スキルの構成

| スキル | 役割 | 出どころ | 自動で読まれるか |
|---|---|---|---|
| `tsumi-mode` | 全スキルの入口となるルーター。pstack の poteto-mode を読ませ、Non-negotiables で状況ごとに tsumi と pstack のスキルを割り当てる。4段の順番と規則を足す | 新規 | 読まれない。`/tsumi-mode`（Claude Code では `/tsumi:tsumi-mode`）で呼んだときだけ |
| `agent-design-review` | エージェントやスキルの設計と改善。4段の中身（呼び出し側からの道具設計、モデルと道具の契約、再発した修正の追い方） | 223mle/skills から移した | 読まれる |
| `clear-japanese` | 日本語の清書 | 223mle/skills から移した | 読まれる |

### 4.0 tsumi-mode をルーターにした理由

Daiki の要望（2026-10-18）は「`/tsumi-mode <依頼>` で、ここで定義した全てのスキルを使う」こと。poteto-mode と同じ形にした（measured、poteto-mode の SKILL.md）。

- Non-negotiables に「状況 → 必ず読むスキル」を並べた。pstack の Non-negotiables に足す形で、食い違ったら tsumi が勝つ。
- 子スキルは `../<name>/SKILL.md` の相対パスで指す。poteto-mode と同じ書き方。
- tsumi-mode 自身はコマンド専用にした。子スキルは `disable-model-invocation` を付けず、単独でも発動する。pstack は子スキルもスラッシュ専用にしているが、tsumi の子スキルは description で発動させたい（4.4）。
- tsumi に新しいスキルを足したら、Non-negotiables に1行足す。`scripts/check-skills` は、tsumi-mode の本文に `../<name>/SKILL.md` がないスキルを見つけるとエラーにする。書き忘れを仕組みで止める（4段の2段目）。

### 4.0.1 呼び出し形式

- Cursor では、スキルを `/skill-name` で呼ぶ（measured、cursor.com/docs/skills と cursor.com/docs/plugins）。
- Claude Code では、プラグインのスキル名に `tsumi:` が付く。`claude -p` の起動イベントにあるスキル一覧に、`tsumi:tsumi-mode`、`tsumi:agent-design-review`、`tsumi:clear-japanese` が出た（measured、2026-10-18、Claude Code 2.1.283）。
- 同じ名前のスキルが個人のスキルフォルダにもあると、Claude Code では `clear-japanese` と `tsumi:clear-japanese` の両方が見えた（measured、同日）。そのため、個人のコピーは消す（0章）。

### 4.1 Daiki の考えの出どころ

tsumi に書いた Daiki の考えは、次から取った（measured）。

- 4段の順番。Daiki がこの作業の指示で示したものと、`agent-design-review` の Improvement order。
- 呼び出し側から道具を設計する、モデルの入力と道具の持ち分を表で決める。`agent-design-review` の「Design the tool from its caller」。
- 再発した修正を「失敗の証拠 → 防ぐ境界 → 強制する資源 → 確かめるお題 → 残る判断」で追う。`agent-design-review` の「Choose and validate a change」。
- 新しいチェックは、過去の実際の失敗で落ちることを示してから入れる。同じ出典。
- 評価では成功基準を実行するエージェントに見せず、成果物と観察した行動で判定する。同じ出典。

読める資料がなかったものは、tsumi-mode の「Not yet written down」に TODO(Daiki) として残した。評価の合否基準と試行回数、人に回す出力の目印、FDE の顧客案件との対応、役割ごとのモデル選び。推測で埋めていない。

223mle/skills の `plan-delegate`、`fresh-review`、`spec-first`、`field-guide`、`context-economy` は移していない。中身が pstack の委譲、レビュー、仕様の規則と重なる（inferred）。どちらを使うかは未決事項に残す。

### 4.2 clear-japanese を独立したスキルにした理由

前の版では、pstack の `/unslop` への overlay として日本語の規則（J1〜J13、自作）を置いていた。これを捨て、`skills/clear-japanese/` として独立させた。

1. description で発動させるため。overlay は tsumi-mode が動いているときにしか読まれない。独立したスキルなら、「日本語を直して」のような依頼だけで読まれる（ドキュメントの仕組みから inferred）。
2. Daiki がすでに使っている名前と description をそのまま使える。「日本語を直して」「AIっぽさを消して」のように、ユーザーが実際に言う言葉が入っている（measured）。
3. 正本は tsumi（0章）。本文と参照7本は 223mle/skills からそのまま写し、description だけ「README・PR 説明」を足した。
4. unslop という名前は pstack の英語向けスキルと紛れる。日本語の清書は clear-japanese と呼ぶほうが、何をするかが名前で分かる。

`/technical-writing` で日本語の文書を書くときは、overlay から clear-japanese を呼ぶ。

### 4.3 description の言語

- `agent-design-review` は英語で書き、末尾に「日本語トリガー - 」で日本語の言い回しを並べた。223mle/skills の6スキルと同じ形（measured）。
- `tsumi-mode` の description はモデルに見えず、`/` メニューに出るだけなので、英語で役割と呼び方だけを書いた。
- `clear-japanese` は全文日本語。元のまま。
- スキル本文も 223mle/skills に合わせた。`clear-japanese` は日本語、それ以外は英語。223mle/skills の README は英語にする理由を「トークン効率と小型モデルでの追従性のため」と書いている（measured）。

### 4.4 tsumi-mode だけをコマンド専用にした理由

`disable-model-invocation: true` を付けたスキルは、description がモデルのコンテキストに入らず、`/スキル名` で呼んだときだけ読まれる（measured、Claude Code と Cursor のドキュメント）。

前の版では、description をトリガーとして働かせるため、全スキルから外した（corrections.tsv の2行目）。2026-10-18 に、tsumi-mode にだけ付け直した。

- tsumi-mode は、作業全体のやり方を切り替え、pstack の poteto-mode を全部読ませる重いスキル。入るかどうかを description というモデルの判断に任せると、プロンプトの段（3段目）で発動を決めることになる。コマンドなら確実に入るので、道具の段（1段目）で決まる。pstack が poteto-mode をコマンド専用にしているのも同じ形。
- 子スキルは、いつ必要になるかをユーザーが予想できない。そこで description で発動させ、トリガーお題（2段目）で見張る。tsumi-mode が動いているあいだは、ルーターがパスで読ませるので、発動のぶれは関係しない。
- 子スキルの description が Claude Code で働くことは、外す前の評価で確かめた（12章）。
- この分け方は `scripts/check-skills` が強制する。tsumi-mode に `disable-model-invocation: true` がない場合と、子スキルに付いている場合をエラーにする。そのため、tsumi-mode が発動するかどうかのお題はやめた。振り分けのお題は残す。コマンドで入ったあと、どの子スキルを読むかはモデルの判断だからである。

コマンドで呼んでも、会話が進むと tsumi-mode の効き目は薄れる。pstack の poteto-help も、Enter で付けたスキルは会話が進むと薄れると書いている（measured）。Cursor では Custom Mode で毎ターン読み込める。Claude Code には同じ仕組みがないので、毎ターン短い注意書きを差し込む hook を別の PR で検討する。

## 5. pstack への上書き（脇役）

dyl-stack の同名プレイブック上書きと同じ仕組みを使う。pstack のスキルを使うとき、`tsumi-mode/overlays/<スキル名>.md` があれば本体のあとに読む。食い違ったら overlay が勝つ。

| pstack のスキル | overlay |
|---|---|
| `/technical-writing` | 日本語の文書は clear-japanese で清書する |
| `/correct` | エージェントの出力の誤りは agent-design-review に回す |

`/unslop` には overlay を置かず、tsumi-mode の Non-negotiables で読まないと決めている（0章）。

`/reflect` の overlay は消し、tsumi の `mistake-triage` スキルに置き換えた。理由は次のとおり。

- pstack の reflect は、会話の記録ファイルを `agent-transcripts/` から探して読む。tsumi は、その場の会話だけを対象にする。
- pstack の reflect は、仕組みで防げる指摘を Backlog に回し、`/correct` につながらない。mistake-triage は、ミスごとに「仕組み（`/correct` の順）」「文章」「評価お題」「ユーザーに聞く」へ振り分ける。
- 振り分けの結果は JSON で出し、`references/triage.schema.json` と `scripts/check_triage.py` で縛る。2回出たミスに仕組みの行き先がない場合と、文章の修正に評価お題がない場合は、理由がなければエラーにする。
- 名前を reflect にすると、Cursor のスラッシュメニューで pstack の `/reflect` とぶつかる。

プレイブックの上書きは `playbooks/eval.md` だけ。前の版の Harden プレイブックは消した。中身が agent-design-review の「Choose and validate a change」と重なるため。

## 6. ディレクトリ構成

```
tsumi/
  .cursor-plugin/plugin.json   # Cursor 用
  .claude-plugin/plugin.json   # Claude Code 用
  README.md  CONTRIBUTING.md  DESIGN.md  corrections.tsv
  docs/skill-authoring.md
  agents/tsumi-agent.md
  skills/
    tsumi-mode/
      SKILL.md
      overlays/      technical-writing.md correct.md
      playbooks/     new-agent.md review-triage.md eval.md
      references/    requirements.md corrections-template.tsv
    agent-design-review/
      SKILL.md  references/  assets/
    clear-japanese/
      SKILL.md  references/
    mistake-triage/
      SKILL.md  references/triage.schema.json  scripts/check_triage.py
  scripts/
    check-skills          # name、description、manifest の機械的な検査
    install-hooks
    sync-installs        # セッション開始時に作業コピーを main の最新にする
    hooks/pre-push
  .github/workflows/check.yml   # PR ごとに check-skills を回す
  evals/
    README.md  cases/  fixtures/  rubrics/  schemas/  bin/  runs/
```

LICENSE は未決なので置いていない。`research/` は調査メモで、git に入れない。

## 7. 修正ログ

- 形は `skills/tsumi-mode/references/corrections-template.tsv`。
- tsumi 自体への指摘は、リポジトリ直下の `corrections.tsv` に書き、コミットする。顧客データを含まないため。
- 顧客案件の修正ログは、置き場所をユーザーが決めるまでコミットしない（tsumi-mode の規則）。

## 8. 評価

- 設計は `evals/README.md`。
- description と2つの manifest の機械的な検査は `scripts/check-skills`。PR ごとに GitHub Actions で回す。
- Claude Code で評価するとき、評価中のエージェントが読めるのは pstack と tsumi の `skills/`、`agents/` だけにする。お題や設計文書を読ませないため。
- トリガーのお題は14件。子スキルの単独での発動8件と、`/tsumi-mode` からの振り分け6件（001、003〜007）。
- 振り返りのお題は2件（`triage-*`）。mistake-triage の JSON を `triage_valid` と `triage_route` で判定する。実行は `evals/bin/run-trigger` で、`--harness cursor` か `--harness claude` を選ぶ。

## 9. 作る順番

1. PR #1 をマージし、手元を0章の置き方に切り替える。個人のコピーはこのときに消す。
2. 未決事項の上位を決める。
3. TODO(Daiki) を埋める。
4. 他のリポジトリで出た指摘の戻し方、修正ログの `class` の数え方を決める（別 PR）。
5. 変更前後を比べる仕組みを作り、baseline を取る。

## 10. 未決事項（重要な順）

| # | 項目 | 論点 |
|---|---|---|
| 1 | 公開範囲 | private のまま個人で使う、LayerX 社内に共有する、公開する |
| 2 | 顧客データの扱い | 実際の案件からお題を作ってよいか。匿名化の基準 |
| 3 | 223mle/skills との二重管理 | 決定。正本は tsumi（0章） |
| 4 | 223mle/skills のハーネス5本 | plan-delegate など。pstack と重なる部分をどちらに寄せるか |
| 5 | 回帰の合否基準と予算 | must-pass の扱い、通過率の許容低下幅、試行回数 |
| 6 | 主な実行環境 | 決定。Cursor と Claude Code（0章） |
| 7 | ライセンス | 公開範囲で決まる |
| 8 | ハーネスの言語 | bun と TypeScript、Python、シェル |
| 9 | FDE 固有のプレイブック | 顧客案件の流れを入れるか（1と2に依存） |

## 11. 前の版から変えたこと

- 主役を overlay から Daiki の考えに移した。
- 自作の日本語規則 J1〜J13 と `overlays/unslop.md` を捨て、clear-japanese を移した。
- agent-design-review を移し、Harden プレイブックを消した。
- 全スキルの description を書き直し、`disable-model-invocation` を外した。
- README から無関係な話題とフックの詳細を外した。フックは CONTRIBUTING.md に移した。

## 12. 限界

- トリガーのお題は、Cursor の CLI で1回（20261018-153705-ce046f3）回した。このときの判定は、tsumi のコピーと個人のコピーを区別していなかった。
- Claude Code（Opus 5.5、effort medium）では、tsumi-mode をコマンド専用にした版（c7790b2）で10件を各3回回し、30回すべて合格した（20261018-172643-c7790b2-claude）。tsumi が持つファイルへの `must_read` は、すべて tsumi のコピーを読んで合格した。この実行では個人用スキルと CLAUDE.md を外している。Cursor では、この版を回していない。
- pstack の unslop を外した版でも、同じ条件で10件を各3回回し、30回すべて合格した（20261018-195159-aff008c-dirty-claude）。tsumi-mode-003 と 006 に足した「unslop を読まない」検査は、外す前の版でも1回ずつ合格した（20261018-185555-aff008c-dirty-claude）。この検査は、外したことの効果を示すものではなく、unslop を読む動きに戻ったときに気づくためのもの。
- main のブランチ保護は GitHub 側でかけられなかった（private リポジトリの無料プラン）。代わりの pre-push フックは手元だけの仕組み。同じ理由で、CI の検査は結果を出すだけで、マージを止められない。

## 13. 引用元の著作権表示

この文書の2章と3章は、pstack と dyl-stack の文を短く引用し、要約している。tsumi のスキルには、両者の文章を写していない。`agent-design-review` と `clear-japanese` は 223mle/skills（MIT、Copyright (c) 2026 223mle）から移した。223mle は Daiki 本人のアカウント。

pstack（https://github.com/cursor/plugins/tree/main/pstack）

```
MIT License

Copyright (c) 2026 Lauren Tan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

dyl-stack（https://github.com/cursor/plugins/tree/main/dyl-stack）は同じ MIT License で、Copyright (c) 2026 Dylan Gattey。条文は上と同じ。
