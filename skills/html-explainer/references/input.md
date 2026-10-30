# 文書の入力

`scripts/render.py input.json --output output.html` で、文書JSONから自己完結したHTMLを作る。文章は文字列で渡し、HTMLを書かない。レンダラーがエスケープする。全部品を使った例は [showcase.json](../assets/showcase.json)、最小の例は [example.json](../assets/example.json)。

## トップレベル

| 項目 | 必須 | 内容 |
| --- | --- | --- |
| `title` | ○ | 文書の題。何が分かる資料かを書く。390px幅では1行に約12字なので、25字程度までにすると2行に収まり、最初の画面に要点まで入る |
| `lead` | ○ | 題の下の1〜2文。対象と範囲、数値の確度を書く |
| `takeaways` | | 要点を2〜4文。各90字以内。最初の画面に番号付きで出る。390×844pxの最初の画面に題・lead・要点がすべて入るのは、leadが100字程度、要点が3つで各60字程度まで |
| `glossary` | | `[{"term": "TTL", "definition": "…"}]`。定義は120字以内。末尾に用語の節も出る |
| `sections` | ○ | 節の配列。節の `id` は図の `id` と同じ名前空間なので重ねない |
| `sources` | | 根拠。`id`、`title` と、`url`（外部リンク）または `note`（提供資料の説明）の少なくとも一方 |

読了の目安は本文の文字数から自動で表示する。

## 節

節は `id`、`title` と `blocks` を持つ。`title` は節の要点を書く。`blocks` は上から順に表示する。以前の形式の `paragraphs`・`callout`・`figures` も使え、`paragraphs`、`callout`、`blocks`、`figures` の順に並ぶ。

| `type` | 項目 | 使う場面 |
| --- | --- | --- |
| `p` | `text` | 段落。1〜3文 |
| `list` | `items`（2〜9個）、`ordered` | 独立した事実の列挙。読み手が順に行う操作は `ordered: true` |
| `callout` | `tone`（`note` / `key` / `warn` / `example`）、`text`、任意の `title` | 読み落とすと困る注意・要点。1節に1つまで |
| `stats` | `items`（2〜4個の `value`・`label`・任意の `note`） | 大きく見せたい数値。`value` は12字以内で単位を含める |
| `compare` | `columns`（2〜3列の `title`・`items`・任意の `label`・`verdict`・`tone`）、任意の `caption` | 選択肢を同じ観点で並べる。`tone` は `good` / `bad` / `accent` / `neutral` |
| `code` | `code`（40行以内）、任意の `language`・`caption` | 説明に必要な部分だけのコード |
| `details` | `summary`、`paragraphs` | 本筋から外れる理由・例外。初期状態で閉じる |
| `figure` | `figure` | 下の基本図 |
| `diagram` | `bundle` | [図の入力](diagram-input.md)のbundle。シーケンス図・経路図・時間軸・閾値 |

## 文中の記法

`lead`・`takeaways`、ブロックの `text`・`items`・`note`・`verdict`・`caption`・`paragraphs`、節の `paragraphs` では、次の記法だけを解釈する。それ以外の記号はそのまま表示する。

- `**強調**`: 太字と薄い下線。1段落に1か所までにする
- `` `code` ``: コード書式。実在するファイル名・コマンド・設定キーに使う
- `[[用語]]`、`[[表示|用語]]`: `glossary` の用語。存在しない用語は生成時に拒否する
- `[表示](https://…)`: 外部リンク。http(s)の絶対URLだけを受け付ける

## 基本図

`figure` ブロックと `figures` の要素には、`id`、`kind`、`title`、`summary`、`caption`、`status` を必ず付ける。`status` は `measured`（計測値）、`inferred`（根拠からの推定）、`planned`（決まった予定や手順）、`proposed`（提案）、`unknown`（未確定）、`illustrative`（説明用）から選ぶ。`measured` と `inferred` には対応する `source_ids` を付ける。広く知られた一般的な仕組みを簡略化した図や表は `illustrative` にし、captionで簡略化していることを書く。依頼に書かれた条件から計算した値（料金の合計、損益分岐の人数）は `inferred` にし、`sources` に依頼の条件を `note` 付きで置いて `source_ids` で結ぶ。captionに計算式を書く。依頼者が決めた作業手順や日程は、書き手の案ではないので `proposed` ではなく `planned` にする。

- `flow`: `steps` に `label`・`detail` を順に並べ、最後以外に `to_next` を付ける
- `bars`: `rows` に `label`・`value`。`unit` と必要なら `axis_max`
- `timeline`: `rows` に `label`・`start`・`duration`。`unit` と必要なら `axis_max`。開始は0以上、期間は正数
- `table`: `columns` と `rows`。各行のセル数を列数と一致させる。セルは記法を解釈しないので、`**` や `[[用語]]`、リンクを書くと生成時に拒否される。強調やリンクは表の前後の本文に置く。4列以上の表は、幅600px以下で1行ずつのカード（左に列名）に変わる。1列目には行の名前（人数、案の名前）を置く

数値の図は入力値から棒幅・軸・目盛りを算出する。値を座標へ直接書かない。往復・分岐・前後比較・重なりがある図は、基本図ではなく `diagram` を使う。
