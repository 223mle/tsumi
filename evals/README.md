# 評価ハーネス設計案（未実装）

tsumi のスキル、ルーター、プロンプトを変えたときに回す回帰評価。Daiki の Mac 上の cursor-agent CLI でローカルに回す前提。クラウドエージェントは使わない。

ラベルは DESIGN.md と同じ（measured、inferred、guess）。

## 目的

- スキルを1つ変えたら、20〜50件のお題を回して前回と比べる。
- 回帰（前は通ったのに落ちたお題）を、出す前に見つける。
- 修正ログの2回目のクラスを、お題として固定する。

## ディレクトリ

```
evals/
  README.md            # この文書
  cases/               # お題。1件1ファイル、YAML
  fixtures/            # お題が使う作業ディレクトリの雛形。名前はふつうのプロジェクト名にする
  rubrics/             # judge 用の採点基準。候補エージェントには見せない
  schemas/
    case.schema.json   # お題ファイルの JSON スキーマ
    judge-output.schema.json   # judge の出力を縛る JSON スキーマ
  bin/                 # run / score / compare（未実装）
  runs/                # 実行結果。git に入れない
  baseline.json        # 受け入れた最新の結果（未作成）
```

## お題の形式

`cases/<id>.yaml`。`schemas/case.schema.json` で検査する。お題ファイル自体をスキーマで縛るのは tsumi-mode の Order of fixes の1段目を、評価そのものにも当てたもの。

| 項目 | 必須 | 中身 |
|---|---|---|
| `id` | 必須 | ファイル名と同じ。`<対象>-<連番>` |
| `title` | 必須 | 何を確かめるか一行 |
| `targets` | 必須 | 対象のスキル名やプレイブック名 |
| `tags` | 任意 | `smoke`、`must-pass`、`routing` など |
| `source` | 必須 | お題の出どころ。修正ログの行、実際の失敗、手書き |
| `fixture` | 任意 | `fixtures/` 下の雛形名。実行時に一時ディレクトリへ写す |
| `prompt` | 必須 | ユーザーがふつうに打つ依頼文 |
| `trials` | 任意 | 試行回数。既定3 |
| `checks` | 必須 | 決定的な検査のリスト。1件以上 |
| `judge` | 任意 | 決定的に採点できない部分だけ。rubric ファイルと基準のリスト |

`checks` の種類の案。

| `type` | 中身 |
|---|---|
| `file_exists` | 作業ディレクトリにファイルがある |
| `must_match` / `must_not_match` | ファイルか最終返信（`path: "@reply"`）が正規表現に合う、合わない |
| `json_schema` | ファイルか返信内の JSON がスキーマに合う |
| `command` | 作業ディレクトリでコマンドを走らせ、終了コードを見る |
| `must_read` / `must_not_read` | エージェントが読んだファイルのパス（stream-json の `readToolCall`）が glob に合う、合わない |
| `max_turns` | ツール呼び出しの回数の上限 |

例は `cases/trigger-*.yaml`。

## トリガーお題

description はエージェントがスキルを読むかどうかを決める。description を変えたら、読むべき依頼と読むべきでない依頼の組で確かめる。

- 1つのスキルにつき、読むべき依頼（`must_read`）と、近いが読むべきでない依頼（`must_not_read`）を対にする。
- 依頼文にスキル名を書かない。ユーザーがふつうに言う言葉で書く。例外は tsumi-mode の「tsumi で」で、これは description が定めたトリガー語そのもの。
- `tags` に `trigger` を付ける。
- 判定は transcript の読んだパスで行う。エージェントの自己申告は使わない。
- 形式の検査（name の形、description の長さ、いつ使うかの記述）は `scripts/check-skills` が先に行う。

今あるお題は6件（clear-japanese、agent-design-review、tsumi-mode で各2件）。まだ一度も回していない。

### blinding の規則

pstack の Eval プレイブックの規則をそのまま使う（measured、`playbooks/eval.md`）。

- 候補が見るディレクトリ名、ファイル名、依頼文に `eval`、`test`、`judge`、`rubric`、`score`、`benchmark`、`candidate` などを入れない。
- 依頼文はふつうの依頼にする。どのスキルを使ったか自己申告させない。
- 振り分けやスキルの読み込みは、自己申告ではなく `must_read` で transcript から判定する。
- judge は採点していると知ってよいが、出力は匿名ラベルで見せ、モデル名は見せない。

## 採点

1. **決定的な検査を先に。** 試行ごとに `checks` を全部回す。1つでも落ちたらその試行は不合格。
2. **judge は残りだけ。** `judge` があるお題だけ、候補と別のモデル系統で採点する。基準ごとに合否と一行の理由を返させ、1〜10点の点数は使わない。出力は `schemas/judge-output.schema.json` で縛り、合わなければ judge の失敗として扱う。
3. **お題の判定。** k 試行のうち全部合格なら `pass`、一部なら `flaky`、全部不合格なら `fail`。
4. **全体の判定。** `baseline.json` と比べる。
   - `pass` から `flaky` か `fail` に落ちたお題は回帰として列挙する。
   - `must-pass` のお題が1件でも回帰したら不合格。
   - 全体の通過率の許容低下幅は未決（DESIGN.md 10章の5）。
5. **数字の説明。** 回帰が出たら、対象の transcript を読み、変更のせいか、お題が不安定なのか、環境のせいかを書く（pstack の Explain the Number、measured）。

## コマンド像（Mac、cursor-agent CLI）

Cursor のドキュメントでは CLI の名前は `agent` で、`-p`、`--output-format stream-json`、`--model`、`--force`、`--trust`、`--workspace`、`--plugin-dir`、`--mode ask` がある（measured、cursor.com/docs/cli/reference/parameters）。Daiki の Mac にあるのは `~/.local/bin/cursor-agent` で、版は 2025.09.18。`--help` に `--plugin-dir` と `--trust` がない（measured、2026-10-18）。下のコマンドを回すには CLI の更新が要る。以下は `cursor-agent` で書く。

### 1件を手で回す

```bash
RUN=$(mktemp -d)/acme-notes          # eval という語を含めない名前にする
cursor-agent -p --output-format stream-json --trust --force \
	--model "$MODEL" \
	--plugin-dir ~/src/pstack-pinned \
	--plugin-dir ~/src/tsumi \
	--workspace "$RUN" \
	"$(yq '.prompt' evals/cases/trigger-clear-japanese-001.yaml)" \
	> evals/runs/manual/stream.jsonl
```

- stream-json の `tool_call` イベントに `readToolCall.args.path` が出る（measured、output-format のドキュメント）。`must_read` はこれを読む。
- 最終返信は末尾の `{"type":"result", ...}` の `result`。
- `--plugin-dir` は複数指定できる（measured、parameters のドキュメント）。pstack は固定した版のコピーを渡す。pstack は自動更新されるので、版を固定しないと pstack 側の変化が tsumi の回帰に見える（inferred）。固定する版は `evals/pstack.lock` に commit SHA で書く案。
- `--plugin-dir` で作業中のコピーを読ませる。インストール済みの tsumi と同時に読まれたときの挙動は確かめていない（guess で衝突する）。回すときはインストール版を外すか、smoke お題で確かめる。

### ハーネス（未実装、bun 想定）

```bash
# 全件を3試行
bun evals/bin/run.ts --cases 'evals/cases/*.yaml' --trials 3 --model "$MODEL" --plugin-dir .

# smoke だけ（スキル変更のたびに）
bun evals/bin/run.ts --tag smoke --trials 1 --plugin-dir .

# 採点と比較
bun evals/bin/score.ts evals/runs/<run-id>
bun evals/bin/compare.ts --base evals/baseline.json --run evals/runs/<run-id>

# 受け入れたら baseline を更新
bun evals/bin/compare.ts --base evals/baseline.json --run evals/runs/<run-id> --accept
```

### 変更前後を比べる

```bash
git worktree add /tmp/tsumi-base main
bun evals/bin/run.ts --plugin-dir /tmp/tsumi-base --trials 3 --out evals/runs/base
bun evals/bin/run.ts --plugin-dir .                 --trials 3 --out evals/runs/head
bun evals/bin/compare.ts --base evals/runs/base --run evals/runs/head
```

### judge

```bash
cursor-agent -p --mode ask --output-format json --trust \
	--model "$JUDGE_MODEL" \
	"$(cat judge-prompt.txt)" | jq -r '.result' > judge.json
# judge.json を schemas/judge-output.schema.json で検査する
```

- `--mode ask` を読み取り専用として使う（inferred、ドキュメントでは plan と ask のモードがあると書いてある）。

### run.ts の中身の案

1. お題を読み、`case.schema.json` で検査する。合わなければ止める。
2. 試行ごとに一時ディレクトリを作り、fixture を写す。名前はお題 id と無関係なものにする。
3. `cursor-agent -p --output-format stream-json ...` を回し、`stream.jsonl` を保存する。並列数は2〜3から始める（guess、Mac の負荷とレート制限次第）。
4. 作業ディレクトリの差分、読んだパス、最終返信、所要時間を `trial.json` に書く。
5. `score.ts` が checks と judge を回し、`score.json` を書く。

`runs/<日時>-<git短縮SHA>/<case-id>/<trial>/` に置く。日時は JST。

## 最初の20件の案

tsumi は pstack の上に乗るので、pstack を入れた状態で回す。お題は tsumi が足した分だけを見る。pstack 単体の挙動は確かめない。

| 対象 | 件数 | 確かめること |
|---|---|---|
| smoke | 2 | `--plugin-dir` で tsumi が読まれるか。pstack の `poteto-mode/SKILL.md` と `tsumi-mode/SKILL.md` の両方を読むか（`must_read`） |
| トリガー | 6 | 各スキルの description で、読むべき依頼で読み、近いが違う依頼で読まないか（作成済み） |
| 修正の段 | 4 | 2回目の修正を、プロンプトではなく道具、スキーマ、テンプレート、評価に移すか |
| clear-japanese の清書 | 3 | 条件・数値・限定語が残り、原文にない因果を足さないか（clear-japanese の preservation.md の例を使う） |
| 振り分け | 3 | 依頼文から `playbooks/new-agent.md`、`review-triage.md`、`eval.md`（上書き）を読むか |
| 上書きファイルの読み込み | 1 | `/technical-writing` を tsumi-mode で使ったとき、pstack 本体のあとに `overlays/technical-writing.md` を読むか |
| pstack 不在 | 1 | pstack を外した環境で、作業を始めずに `/add-plugin pstack` を案内して止まるか |

その後は修正ログの2回目のクラスから足し、50件を上限の目安にする。

## 未決（DESIGN.md 10章と重なるもの）

- 顧客データの扱い（2）、合否基準と予算（5）、ハーネスの言語（8）。
