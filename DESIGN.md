# tsumi 設計

更新 2026-10-18（JST）。前の版は box の `/workspace/dstack/DESIGN.md`（仮名 dstack）。

ラベルの意味は次の通り。

- measured は、ファイルや投稿を読んで確かめたこと。
- inferred は、読んだものから推したこと。
- guess は、確かめていない予想。

## 0. 決まったこと

- プラグイン名は `tsumi`。ルーターは `tsumi-mode`。
- リポジトリは GitHub の private リポジトリ `223mle/tsumi`。
- pstack を前提にして、足りない分だけ足す。dyl-stack と同じ考え方。

この3つから、次も決まると見ている（inferred）。

- モデル設定は pstack の `~/.cursor/rules/pstack-models.mdc` をそのまま使う。tsumi 用の設定ファイルは作らない。
- `/in-your-own-words` など、pstack にあって変える必要のないスキルは pstack のものを呼ぶ。写さない。

## 1. 読んだもの

- pstack v0.15.25（`/workspace/plugins/pstack/`）。構造の要約は前の版の DESIGN.md 1章（measured）。
- dyl-stack（`cursor/plugins` の `dyl-stack/`、最新コミット fae2c6e、2026-09-30 09:58 JST）。`dyl-mode/SKILL.md`、`references/requirements.md`、`playbooks/opening-a-pr.md`、`agents/dyl-agent.md`、README を GitHub の raw から読んだ（measured）。
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

## 4. 汎用スキルにどう足すか

### 4.1 足す必要があるもの

| pstack のスキル | 足すもの |
|---|---|
| `/unslop` | 日本語の規則 |
| `/technical-writing` | 日本語の文書の扱い |
| `/correct` | 開発中のエージェントの誤りは Harden に回す、という一行 |
| `/reflect` | Accepted の各行に評価お題の欄 |
| `/bro`、`/sharpen` | なし。pstack のものを呼ぶだけ |

### 4.2 比べた方法

| 方法 | 中身 | 良い点 | 悪い点 |
|---|---|---|---|
| A. tsumi-mode に直接書く | ルーターの gate に4つの追記を全部書く | ファイルが1つで済む。dyl の「返信は `/bro`」と同じ形 | 日本語の規則13個などでルーターが太る。毎回全部読まれる。pstack がプレイブックを参照ファイルに分けた理由（必要なときだけ読む）に反する |
| B. overlay 参照ファイル | `tsumi-mode/overlays/<スキル名>.md` を置く。tsumi-mode に「pstack のスキルを使うとき、同名の overlay があれば本体のあとに読む。食い違ったら overlay が勝つ」と一行書く | dyl の同名プレイブック上書きと同じ仕組みを、スキルに広げるだけ。必要なときだけ読まれる。スラッシュ名は増えない。`/technical-writing` の中で `/unslop` を当てるような、スキル経由の呼び出しにも一行の規則で届く | tsumi-mode を付けずに `/unslop` を直接打つと、overlay は読まれない |
| C. 別名の小さなスキル | `/unslop-ja` や `/tsumi-reflect` を作り、中で pstack 本体を読ませる | tsumi-mode なしでも単独で使える | 同じ仕事に名前が2つできる。pstack の他のスキルや `poteto-mode` の Non-negotiables は `unslop` を名指しするので、別名は呼ばれない。dyl-stack もこの方法は使っていない |
| D. pstack を写して書き換える | 移植6本を tsumi に持つ | 自由に変えられる | 今回の方針（写さない）に反する。pstack の更新を追う手間が増える |

### 4.3 選んだのは B

理由は次の4つ。

1. dyl-stack が実際に使っている仕組み（同名ファイルを上書き分として、本体のあとに読ませる）と同じ形になる（measured）。pstack の利用者が読み慣れた形。
2. pstack 本体は呼ばれ方が変わらない。`poteto-mode` や `/technical-writing` は今まで通り `unslop` を名指しし、tsumi-mode の一行の規則で overlay が付いてくる。C だとここが切れる（inferred）。
3. 必要なときだけ読まれる。日本語の規則はルーターに入れず、`/unslop` を使うときだけ読む。A よりトークンが少ない（inferred）。
4. 足す量が小さい。`/correct` と `/reflect` は数行で済む。別名のスキルを作るほどの量ではない。

B の弱点（tsumi-mode なしで `/unslop` を直接打つと日本語の規則が付かない）は受け入れる。困る場面が実際に出たら、そのときに `/unslop` 用だけ C を足す。

### 4.4 overlay の置き場所と書き方

- スキルへの上書きは `skills/tsumi-mode/overlays/<pstack のスキル名>.md`。
- プレイブックへの上書きは dyl-stack と同じく `skills/tsumi-mode/playbooks/<pstack のプレイブック名>.md`。今は `eval.md` だけ。
- どの overlay も1行目で「pstack の本体を先に読む」と書き、そのあと足す分だけを書く。pstack の文章は写さない。
- overlay が読まれたかは評価で確かめる（`evals/README.md` の「上書きファイルの読み込み」）。

## 5. ディレクトリ構成

```
tsumi/
  .cursor-plugin/plugin.json
  .gitignore
  README.md
  DESIGN.md
  agents/
    tsumi-agent.md
  skills/
    tsumi-mode/
      SKILL.md
      overlays/
        unslop.md
        technical-writing.md
        correct.md
        reflect.md
      playbooks/
        new-agent.md
        harden.md
        review-triage.md
        eval.md               # pstack の Eval への上書き
      references/
        requirements.md
        corrections-template.tsv
  scripts/
    install-hooks         # scripts/hooks/ を .git/hooks/ に写す
    hooks/pre-push        # main への push を止める
  evals/
    README.md
    cases/ fixtures/ rubrics/ schemas/ bin/ runs/
```

LICENSE は未決なので置いていない。

## 6. manifest

`.cursor-plugin/plugin.json` だけを置く。dyl-stack も同じでルートの `plugin.json` はない（measured）。

- `description` の先頭に「Requires pstack.」と書いた。manifest に依存を書く欄は pstack にも dyl-stack にもなかった（measured）。
- `keywords` に `pstack` を入れた。
- `license` はライセンスが未決なので書いていない。
- `description` は英語にした。pstack と dyl-stack が英語だから。言語は未決事項に残す。

## 7. tsumi-mode の中身

- 冒頭で「pstack の `poteto-mode` に乗る薄いルーター。食い違ったら tsumi の gate が勝つ」と書く。
- 前提の確認は `references/requirements.md`。pstack がなければ止まる。
- 最初にやることは4つ。pstack の `poteto-mode` を全部読む。プレイブックは tsumi を先に探し、同名なら pstack のあとに読む。pstack のスキルを使うときは overlay を探す。tsumi の gate を当てる。
- tsumi gates は次の通り。
  - **修正の段。** 道具と環境、自動チェックと回帰評価、プロンプト、人のレビューの順に直せるか試す。返信に、直した段と上の段で直せなかった理由を書く。
  - **同じ修正の2回目。** プロンプトに足さず段1か段2に移す。エージェントの誤りは Harden、コードの誤りは pstack の `/correct`。
  - **変更ごとの回帰評価。** スキル、プロンプト、ツール定義、スキーマを変えたら Eval を通す。
  - **修正ログ。** 修正を受けたら1行足す。
  - **顧客データ。** 評価お題、ログ、コミット、外部送信に入れる前に止まる。
- サブエージェントは `tsumi-agent`。
- プレイブックは New agent、Harden、Review triage、Eval（上書き）の4本。

## 8. dstack 案から削ったもの

| dstack 案 | tsumi | 理由 |
|---|---|---|
| 汎用6スキルの移植 | 写さない。4本は overlay、2本は pstack を呼ぶだけ | 上乗せの方針 |
| principle 7本の leaf | 作らない。tsumi-mode の gate に入れた | dyl-stack も principle は1本だけ（measured）。中身の多くは pstack の `encode-lessons-in-structure`、`type-system-discipline`、`boundary-discipline`、`explain-the-number` と重なる（inferred）。gate が10行を超えたり、名前で引用したくなったら leaf に分ける |
| `/harden` `/eval-case` `/regress` スキル | Harden プレイブックと Eval の上書きにした。お題づくりは Harden の手順2と New agent の手順4に入れた | スラッシュ名を増やさない。pstack と同じく、手順はプレイブックに置く |
| prompt-or-skill-change と eval-authoring のプレイブック | Eval の上書きに入れた | pstack に Eval プレイブックがある |
| customer-poc のプレイブック | 作らない | 未決事項に残す |
| `validate-skills.ts` と `corrections.ts` | まだ作らない | 中身が固まってから。修正ログは当面手で数える |

## 9. 修正ログ

- 形は `skills/tsumi-mode/references/corrections-template.tsv`。列は `ts`、`target`、`class`、`wrong`、`correction`、`moved_to`、`evidence`。
- 置き場所が決まるまでは、作業中のリポジトリ直下の `corrections.tsv` に書き、コミットしない。
- 同じ `class` が2行になったら「同じ修正の2回目」を当てる。数えるスクリプトは後で作る。

## 10. 評価

- 設計は `evals/README.md`。お題、採点、Mac 上の cursor-agent CLI でのコマンド像を書いた。
- tsumi は pstack の上に乗るので、pstack を入れた状態で回す。pstack は自動更新されるので、版を固定したコピーを `--plugin-dir` で渡す案にした（inferred）。
- 最初の20件は、tsumi が足した分だけを見る。overlay が読まれるか、tsumi のプレイブックに振り分けるか、段の順に直すか、pstack がないときに止まるか。

## 11. 作る順番

1. 未決事項の上位を決める。
2. tsumi-mode の初稿を、Daiki の実際の修正で直す。特に `overlays/unslop.md` の J 規則。
3. 評価ハーネスを作り、最初の20件を入れて baseline を取る。
4. 以後、スキルを変えるたびに Eval を通す。

## 12. 未決事項（重要な順）

| # | 項目 | 重要な理由 | 選択肢や論点 |
|---|---|---|---|
| 1 | 公開範囲 | 書ける内容（顧客名、社内事情）とライセンスの要否が決まる | private のまま個人で使う。LayerX 社内に共有する。公開する |
| 2 | 顧客データの扱い | 誤ると情報漏えいになる。評価お題と修正ログの両方に効く | 実際の案件からお題を作ってよいか。匿名化の基準。修正ログをコミットするか、ローカルだけにするか |
| 3 | スキル本文と返信の言語と文体 | これから書く全部の文章に効く。後で変えると全部書き直し | 日本語か英語か。日本語なら常体か敬体か。manifest の `description` の言語 |
| 4 | 主な実行環境 | 評価ハーネス、パス、インストール手順が変わる | Cursor IDE、cursor-agent CLI、Claude Code、Grok Bot。Claude Code も使うなら pstack の読み替え表に乗るか |
| 5 | 回帰の合否基準と予算 | 毎回の変更の速さとコストが決まる | must-pass が1件落ちたら不合格にするか。通過率の許容低下幅。1回に何件を何試行回すか。毎回全件か smoke だけか |
| 6 | `/unslop` の日本語規則の採否 | 初稿の J1〜J13 は候補（guess）。Daiki の実際の修正と合っていないと逆効果 | どの規則を残すか。足りない規則 |
| 7 | 日本語の文書の基準 | `/technical-writing` の overlay が最小限のまま | JTF 日本語標準スタイルガイド、社内ルール、自分の規則 |
| 8 | ライセンス | 共有や公開の前に要る | MIT か、なしか。公開範囲で決まる |
| 9 | tsumi の対象範囲 | gate とプレイブックの書き方が変わる | tsumi 自身のスキル評価までか、顧客向けエージェントの評価の型まで含めるか |
| 10 | ハーネスの言語 | 実装に入る前に要る | bun と TypeScript（pstack と同じ）、Python、シェル |
| 11 | FDE 固有のプレイブック | 顧客案件の流れを入れるか | customer-poc などを足すか。どこまで書けるか（1と2に依存） |

前の版から消したもの。置き場所、プラグイン名、mode 名、pstack との関係は決まった。モデル設定と `/in-your-own-words` は、上乗せの方針から決まった（0章）。

## 13. 限界

- tsumi-mode と overlay は初稿で、評価をまだ回していない。overlay が実際に読まれるかは確かめていない（guess で読まれる）。
- `--plugin-dir` が `-p` モードでスキルを読み込むか、pstack と tsumi を同時に渡したときの挙動は確かめていない（guess）。
- Cursor の IDE で private のプラグインを入れる手順は確かめていない。
- Daiki の過去の修正や transcript は読んでいない。
- main のブランチ保護は GitHub 側でかけられなかった。classic の branch protection も rulesets も「Upgrade to GitHub Pro or make this repository public to enable this feature.」（HTTP 403）で弾かれた（measured、2026-10-18 JST）。代わりの pre-push フックは手元だけの仕組みで、`--no-verify` で外せる。

## 14. 引用元の著作権表示

この文書の2章と3章は、pstack と dyl-stack の文を短く引用し、要約している。tsumi の他のファイルには、両者の文章を写していない。

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
