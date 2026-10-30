# 図の入力

目次: [bundle](#bundle) / [比較とステップ](#比較とステップ) / [sequence](#sequence) / [timeline](#timeline) / [threshold](#threshold) / [network](#network) / [decision](#decision) / [一度の生成で確認する例](#一度の生成で確認する例)

`diagrams.py`は1つのbundleからfigureを生成する。`render.py`の文書では、`diagram`ブロックの`bundle`に同じものを入れる。`compose.py`は `{"figures": [bundle, ...]}` の順番で元HTMLの全figureを置き換える。入力はJSON。生のHTML・CSS・SVG・座標は受け付けない。検証と配置は `diagrams.py`、`charts.py`、`network.py`、`sequence.py`、`decisions.py` が行う。

## bundle

```json
{
  "id": "request-flow",
  "title": "準備を入力中へ移す",
  "caption": "同じ時間軸で比較した説明用の例です。",
  "status": "illustrative",
  "labels": ["変更前", "変更後"],
  "legend": [{"label": "準備", "tone": "blue"}],
  "motion": false,
  "panels": [{"title": "時間の並び", "spec": {}}]
}
```

`spec`には下記の種類を指定する。全panelのvariant数は同じにする。1つだけの静的panelは比較図に併用できる。`status`は `measured` / `inferred` / `proposed` / `unknown` / `illustrative` / `code`。根拠と測定条件はcaptionに書く。

## 比較とステップ

`mode` は `compare`（既定）か `steps`。

- `compare`: variantを切り替えボタンで選ぶ。前後比較や、条件ごとの違いに使う。
- `steps`: 前へ・次へ・自動で進めるボタンと、←→キーで1段階ずつ進める。各段階の説明文が図の上に出る。`steps: [{"label": "コードを渡す", "text": "ブラウザーがコードをアプリへ届けます。"}]` をscene数と同じ数だけ書く。`label` は40字以内、`text` は160字以内。panelが `sequence` なら、`steps` を省略するとメッセージから作る。

印刷とJS無効のときは、`compare` は全variantを、`steps` は最後のsceneと全段階の文章を表示する。

`tone`は `blue` / `teal` / `violet` / `amber` / `rose` / `slate` / `red`。名前は色の指定だが、作成前に文書全体で対象との対応を決め、legendでも示す。色名が同じなら明暗テーマで一貫して変わる。

## sequence

```json
{
  "type": "sequence",
  "actors": [{"id": "browser", "label": "ブラウザー", "tone": "slate"}, {"id": "api", "label": "API", "tone": "blue"}],
  "messages": [
    {"id": "req", "from": "browser", "to": "api", "label": "商品ページを要求", "text": "ブラウザーがAPIに商品情報を要求します。"},
    {"id": "res", "from": "api", "to": "browser", "label": "商品ページ", "kind": "reply"}
  ],
  "spans": [{"from": "req", "to": "res", "label": "約120ms"}]
}
```

参加者は2〜6、メッセージは1〜14。メッセージが14を超える往復は2つの図に分ける。参加者は左から順に等間隔で並び、時間は下へ進む。1メッセージが1 sceneになり、現在のメッセージを太く、済んだものを通常、これからのものを薄く描く。

- `kind`: `call`（実線・塗りの矢じり、既定）、`reply`（破線）、`async`（実線・開いた矢じり）。`from` と `to` が同じなら自己呼び出しのループになる。
- `label`: 矢印に載る短い動詞句。列の間に入らない長さは2行まで折り返し、3行になると拒否する。詳しい説明は `text` に書く。
- `step_label`: ステップ一覧で `label` と違う名前を使うときだけ指定する。
- `spans`: `from` から `to` までのメッセージにかかる時間や待ちを示す寸法線。最大3個、ラベルは全角7字まで。処理する参加者が端にいれば、その生存線の横に描く。

## timeline

```json
{
  "type": "timeline", "min": -4, "max": 8, "unit": "秒",
  "ticks": [-4, -2, 0, 2, 4, 6, 8],
  "lanes": [{"id": "prepare", "label": "準備", "tone": "blue"}],
  "variants": [
    {"label": "変更前", "segments": [{"id": "prep", "lane": "prepare", "start": 0, "duration": 3, "label": "3秒"}], "markers": [{"id": "send", "value": 0, "label": "送信", "tone": "slate"}]},
    {"label": "変更後", "segments": [{"id": "prep", "lane": "prepare", "start": -3, "duration": 3, "label": "3秒"}], "markers": [{"id": "send", "value": 0, "label": "送信", "tone": "slate"}]}
  ]
}
```

同じIDのsegmentが移動する。軸は共有し、variantごとに変えない。`start + duration`は軸の範囲に収める。表示する丸め値は `label` に与え、geometryから必要以上に細かい数値を作らない。

未測定の工程は `{"id":"classify","lane":"work","start":4,"unknown":true,"label":"分類時間は未計測"}` とする。`duration`との同時指定は拒否され、量を表す棒は描かれない。既知工程だけで完了時刻を決めない。

グループ帯は `groups: [{"label":"受信前に実行可能","summary":"約10秒","lane_ids":["a","b","c"],"tone":"teal"}]`。3行程度の関連laneをまとめると左のラベル・summaryが収まる。各variantの `group_summaries` にグループ順の文字列を渡すと、summaryも同期して切り替わる。

## threshold

```json
{
  "type": "threshold", "min": 1, "max": 100, "scale": "log", "unit": "秒",
  "ticks": [1, 10, 100],
  "rows": [{"id": "small", "label": "小規模", "value": 2, "value_label": "約2秒", "tone": "blue"}, {"id": "large", "label": "大規模", "value": 20, "value_label": "約20秒", "tone": "blue"}],
  "thresholds": [{"id": "limit", "value": 6, "label": "入力6秒", "tone": "red"}]
}
```

`scale`は `linear` または `log`。対数軸はminを正数にする。複数の閾値があれば、それぞれ線を描き、最大の閾値を超えた部分を赤で示す。値ラベルは右側の予約欄へ置く。

## network

```json
{
  "type": "network", "columns": 3, "rows": 2,
  "nodes": [
    {"id": "source", "label": "保存先", "column": 1, "row": 2, "tone": "slate"},
    {"id": "api", "label": "API", "column": 2, "row": 2, "tone": "blue"},
    {"id": "worker", "label": "処理環境", "column": 3, "row": 2, "tone": "teal"}
  ],
  "boundaries": [{"id": "runtime", "label": "隔離した領域", "node_ids": ["worker"], "tone": "violet"}],
  "variants": [{"label": "取得", "active_nodes": ["source", "api", "worker"], "edges": [
    {"id": "load", "from": "source", "to": "api", "label": "① 読む", "kind": "file", "tone": "teal"},
    {"id": "reply", "from": "api", "to": "worker", "label": "② 返す", "kind": "file", "tone": "teal"}
  ]}]
}
```

列は3または4、行は2または3。1セルに1ノード。ノードのない行は詰め、迂回経路が必要なときだけ上下に余白を足す。ノードの `label` が `glossary` の用語と同じなら、本文の用語と連動して強調される。`detail`は短い補足、`active_nodes`は当該状態で使うノードの一覧。使わないノードは薄く残す。全variantで位置を保ち、経路の変更を見せる。

`request`は破線、`file`は実線。`route`は通常省略し、必要なときだけ `above` / `below`、`label_side`は `above` / `below`を指定する。第三のノードや既存のラベルとぶつかる経路は迂回し、収まらなければ入力を拒否する。拒否時はラベルを短くするか、認可ノードを別の行へ移す。任意のトポロジーに完全自動で最適配置する道具ではない。

## decision

`{"type":"decision","columns":[{"eyebrow":"段階","title":"方針","items":["選択肢1","選択肢2"],"footer":"結果・条件"}, ...]}`。columnsは2つ、itemsも2つ。詳細な理由は本文に置く。

## 一度の生成で確認する例

[animated-example.json](../assets/animated-example.json)は架空の処理を使った例。実際のサービスの時間や制約として流用しない。

```sh
python3 scripts/diagrams.py assets/animated-example.json --output /tmp/animated.html
node scripts/check-diagrams.cjs /tmp/animated.html /tmp/animated-evidence
```
