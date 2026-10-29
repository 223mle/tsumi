# 入力JSON

`scripts/render.py input.json --output output.html`で、入力JSONから自己完結したHTMLを作ります。文章は文字列として渡し、HTMLを埋め込まないでください。レンダラーがエスケープします。

必須のトップレベル項目は`title`、`lead`、`sections`です。`sources`は根拠です。各根拠は`id`と`title`に加えて、`url`（外部リンク）または`note`（添付ファイル・ユーザー提供資料などの説明）の少なくとも一方を指定します。セクションには`paragraphs`と`figures`を置けます。

図には`id`、`kind`、`title`、`summary`、`caption`、`status`を必ず付けます。`status`は`measured`（計測値）、`inferred`（根拠からの推定）、`proposed`（提案）、`unknown`（未確定）、`illustrative`（説明用）から選びます。`measured`と`inferred`には、対応する`source_ids`を付けてください。

図の種類は次の4つです。

- `flow`: `steps`に`label`と`detail`を順番に並べます。
- `bars`: `rows`に`label`と`value`を並べます。`unit`と必要なら`axis_max`を付けます。
- `timeline`: `rows`に`label`、`start`、`duration`を並べます。`unit`と必要なら`axis_max`を付けます。開始時刻は0以上、期間は正数です。
- `table`: `columns`と`rows`を並べます。各行のセル数は列数と一致させます。

すべての図は`summary`を図の外にも表示します。数値の図は入力値から棒幅、軸、目盛りを算出します。値を図の座標へ直接書かないでください。
