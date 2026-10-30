# 図の入力

`diagrams.py`は1つのbundleからfigureを生成する。`compose.py`は `{"figures": [bundle, ...]}` の順番で元HTMLの全figureを置き換える。入力はJSON。生のHTML・CSS・SVG・座標は受け付けない。検証と配置は `diagrams.py`、`charts.py`、`network.py`、`decisions.py` が行う。

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

`tone`は `blue` / `teal` / `violet` / `amber` / `rose` / `slate` / `red`。名前は色の指定だが、作成前に文書全体で対象との対応を決め、legendでも示す。色名が同じなら明暗テーマで一貫して変わる。

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

列は3または4、行は2または3。1セルに1ノード。`detail`は短い補足、`active_nodes`は当該状態で使うノードの一覧。使わないノードは薄く残す。全variantで位置を保ち、経路の変更を見せる。

`request`は破線、`file`は実線。`route`は通常省略し、必要なときだけ `above` / `below`、`label_side`は `above` / `below`を指定する。第三のノードや既存のラベルとぶつかる経路は迂回し、収まらなければ入力を拒否する。拒否時はラベルを短くするか、認可ノードを別の行へ移す。任意のトポロジーに完全自動で最適配置する道具ではない。

## decision

`{"type":"decision","columns":[{"eyebrow":"段階","title":"方針","items":["選択肢1","選択肢2"],"footer":"結果・条件"}, ...]}`。columnsは2つ、itemsも2つ。詳細な理由は本文に置く。

## 一度の生成で確認する例

[animated-example.json](../assets/animated-example.json)は架空の処理を使った例。実際のサービスの時間や制約として流用しない。

```sh
python3 scripts/diagrams.py assets/animated-example.json --output /tmp/animated.html
node scripts/check-diagrams.cjs /tmp/animated.html /tmp/animated-evidence
```
