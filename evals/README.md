# 評価

tsumi のスキル、ルーター、プロンプトを変えたときに回す回帰評価。Cursor の CLI か Claude Code で、ローカルに回す。クラウドエージェントは使わない。

ラベルは DESIGN.md と同じ（measured、inferred、guess）。

## 目的

- 作業の途中では、変えたスキルに関わるお題だけを1回ずつ回す。全件を3回ずつ回すのは、PR を仕上げる最後の1回だけにする。
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
  bin/run-trigger      # トリガーお題を回す
  runs/                # 実行結果。git に入れない
```

日本語の清書と起草の出力評価は [prose/README.md](prose/README.md) に分けてある。トリガー評価だけでは、説明量・意味の保持・構成の品質は確認できない。

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
- 依頼文にスキル名を書かない。ユーザーがふつうに言う言葉で書く。例外は tsumi-mode で、コマンド専用なので、依頼文を `/tsumi-mode` で始める。
- `tags` に `trigger` を付ける。
- 判定は transcript の読んだパスで行う。エージェントの自己申告は使わない。
- `/スキル名` で呼んだスキルの SKILL.md は、Read を通らずに入り、stream-json に出ない（measured、Cursor の CLI 2026.10.16 と Claude Code 2.1.283）。tsumi-mode はコマンドで必ず入るので、読んだかどうかは判定しない。
- 個人用スキル（`~/.claude/skills`、`~/.codex/skills`）も CLI に読まれる。同じ名前のスキルがあると結果が混ざる。そこで、tsumi が持つファイルへの `must_read` は、tsumi のコピーを読んだときだけ合格にする。
- 形式の検査（name の形、description の長さ、いつ使うかの記述）は `scripts/check-skills` が先に行う。

今あるお題は16件。子スキルが単独で発動するか（agent-design-review で3件、unslop で4件、tsumi-reflect で2件）と、`/tsumi-mode` から状況に合う子スキルやプレイブック、pstack のスキルへ振り分けるか（tsumi-mode-001、003〜008）。pstack の `unslop` は tsumi の `unslop` と同じ名前なので、pstack のものを読まないことを確かめる検査は、glob に `*/pstack/*` を入れてパスで分ける。tsumi-mode 自身の発動は、コマンド専用であることを `scripts/check-skills` が確かめるので、お題にしない。実行は `evals/bin/run-trigger`。結果は DESIGN.md 12章にある。

### blinding の規則

pstack の Eval プレイブックの規則をそのまま使う（measured、`playbooks/eval.md`）。

- 候補が見るディレクトリ名、ファイル名、依頼文に `eval`、`test`、`judge`、`rubric`、`score`、`benchmark`、`candidate` などを入れない。
- 依頼文はふつうの依頼にする。どのスキルを使ったか自己申告させない。
- 振り分けやスキルの読み込みは、自己申告ではなく `must_read` で transcript から判定する。
- judge は採点していると知ってよいが、出力は匿名ラベルで見せ、モデル名は見せない。

## 採点

1. **決定的な検査。** 試行ごとに `checks` を全部回す。1つでも落ちたらその試行は不合格。
2. **お題の判定。** k 試行のうち全部合格なら `pass`、一部なら `flaky`、全部不合格なら `fail`。
3. **数字の説明。** 回帰が出たら、対象の transcript を読み、変更のせいか、お題が不安定なのか、環境のせいかを書く（pstack の Explain the Number、measured）。

次の2つは未実装。決めてある方針だけを書く。

- judge は、決定的に採点できない部分だけを、候補と別のモデル系統で採点する。基準ごとに合否と一行の理由を返させ、出力は `schemas/judge-output.schema.json` で縛る。
- 前回の結果と比べ、`pass` から `flaky` か `fail` に落ちたお題を回帰として列挙する。`must-pass` のお題が1件でも回帰したら不合格にする。全体の通過率の許容低下幅は未決（DESIGN.md 10章の5）。

## 回し方

トリガーお題は `evals/bin/run-trigger` で回す。結果は `evals/runs/<日時>-<git短縮SHA>-<harness>/` に出る。

pstack は自動で更新されるので、版を固定しないと、pstack 側の変化が tsumi の回帰に見える（inferred）。比べる2回は同じ pstack の版で回す。

### Claude Code

```bash
evals/bin/run-trigger --harness claude \
	--pstack ~/.claude/plugins/cache/cursor-plugins/pstack/<版> \
	--model claude-opus-5-5 --effort medium --trials 3
```

- `claude -p --output-format stream-json` に、pstack と tsumi だけを `--plugin-dir` で渡す。`--setting-sources project` を付けるので、個人用スキル、ユーザーのプラグイン、CLAUDE.md は読み込まれない（measured、2026-10-18）。
- 評価中のエージェントが読めるのは、pstack と、tsumi の `skills/` と `agents/` だけにする（`--add-dir`）。お題、この文書、DESIGN.md、corrections.tsv は読めない。
- `--permission-mode dontAsk` で回すので、許可が要るツール（Bash、Edit など）は拒否される。読んだかどうかは、Read と Skill の呼び出しのうち、エラーにならなかったものから判定する。

### Cursor

```bash
evals/bin/run-trigger --harness cursor --pstack <pstack のディレクトリ> --trials 3
```

- ログイン済みの CLI（`agent`）が要る。`--mode ask` で、読み取りだけに絞って回す（inferred、ドキュメントでは plan と ask のモードがあると書いてある）。
- stream-json の `tool_call` イベントにある `.md` のパスを、読んだファイルとして扱う。
- Cursor の CLI では、評価中のエージェントが読める範囲を絞っていない。

## 次に足すお題の案

tsumi は pstack の上に乗るので、pstack を入れた状態で回す。お題は tsumi が足した分だけを見る。pstack 単体の挙動は確かめない。

| 対象 | 件数 | 確かめること |
|---|---|---|
| smoke | 2 | `--plugin-dir` で tsumi が読まれるか。pstack の `poteto-mode/SKILL.md` と `tsumi-mode/SKILL.md` の両方を読むか（`must_read`） |
| トリガー | 16 | 各スキルの description で、読むべき依頼で読み、近いが違う依頼で読まないか（作成済み） |
| 修正の段 | 4 | 2回目の修正を、プロンプトではなく道具、スキーマ、テンプレート、評価に移すか |
| unslop の清書と起草 | 5（上限6） | 条件の保持、段落と列挙、PR説明、造語の定義、決定事項と節の結論。入力と判定基準は prose/ に作成済み。採点は出力を読んで行う。上限は `scripts/check-skills` が確かめる |
| 振り分け | 3 | 依頼文から `playbooks/new-agent.md`、`review-triage.md`、`eval.md`（上書き）を読むか |
| pstack 不在 | 1 | pstack を外した環境で、作業を始めずに `/add-plugin pstack` を案内して止まるか |

その後は、修正ログで2回目になったクラスからお題を足す。

## 未決（DESIGN.md 10章と重なるもの）

- 顧客データの扱い（2）、合否基準と予算（5）、ハーネスの言語（8）。
