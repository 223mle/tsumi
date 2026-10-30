# 図の入力

目次: [bundle](#bundle) / [比較とステップ](#比較とステップ) / [sequence](#sequence) / [timeline](#timeline) / [line](#line) / [threshold](#threshold) / [network](#network) / [decision](#decision) / [一度の生成で確認する例](#一度の生成で確認する例)

`diagrams.py`は1つのbundleからfigureを生成する。`render.py`の文書では、`diagram`ブロックの`bundle`に同じものを入れる。`compose.py`は `{"figures": [bundle, ...]}` の順番で元HTMLの全figureを置き換える。入力はJSON。生のHTML・CSS・SVG・座標は受け付けない。検証と配置は `diagrams.py`、`charts.py`、`network.py`、`sequence.py`、`decisions.py` が行う。

## bundle

bundleの `id` は、文書内の節の `id`、他の図の `id` と重ならない名前にする（同じページ内のアンカーになるため）。`caption`・`notes`・`steps[].text`・メッセージや辺の `text` では、`render.py` の文書に埋め込んだときに限り、文中の記法（`**強調**`、`` `code` ``、`[[用語]]`）が使える。

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

`spec`には下記の種類を指定する。全panelのvariant数は同じにする。1つだけの静的panelは比較図に併用できる。`status`は `measured` / `inferred` / `planned` / `proposed` / `unknown` / `illustrative` / `code`。根拠と測定条件はcaptionに書く。`status` は図に1つなので、確度の違うvariant（計算で出せる案Aと、推定しかできない案B）を1枚に並べるときは、低い方の確度を `status` にし、variantの `label`（「B 判定1分（推定）」）と `notes` に確度を書き、captionでどの結果が計算でどれが推定かを分ける。

`source_ids` には、文書の `sources` の `id` を並べる。`status` が `measured` か `inferred` の図では必須で、captionの後ろに出典へのリンクが付く。`legend` は図全体で1つなので、同じ色を全variantで同じ意味に使う。`legend` を書いた経路図では、辺に使う色をすべてlegendに載せる。載っていない色の辺は生成時に拒否する（中立の `slate` と、×印の付く `conflict` は除く）。

## 比較とステップ

`mode` は `compare`（既定）、`steps`、`slider`。

- `compare`: variantを切り替えボタンで選ぶ。前後比較や、条件ごとの違いに使う。`notes` にvariantと同じ数の文（各160字以内）を渡すと、選んだvariantの説明が図の上に出る。何が変わったかを1文で書く。
- `steps`: 前へ・次へ・自動で進めるボタンと、←→キーで1段階ずつ進める。各段階の説明文が図の上に出る。`steps: [{"label": "コードを渡す", "text": "ブラウザーがコードをアプリへ届けます。"}]` をscene数と同じ数だけ書く。`label` は40字以内、`text` は160字以内。panelが `sequence` か、番号付きの辺を持つ `network` なら、`steps` を省略すると図の入力から作る。

`timeline` と `threshold`（`groups` なし）は、幅600px以下で行名の列を細くした別の配置に切り替わり、横スクロールなしで全体が見える。目盛りの文字が重なる場合は1つおきに表示する。ノードの `row` が2種類以内（グリッドの2行に収まる）の `network` は、幅600px以下で行と列を入れ替えた縦向きの配置に切り替わり、左から右への流れが上から下へ読める。縦向きで経路やラベルが収まらない場合は、横向きのまま横スクロールになり、`render.py` が `render: note:` で理由を表示する。ノードの位置を入れ替えるか、ラベルを短くすると縦向きになることが多い。その他の図が画面幅に収まらないときは「全体を縮小表示」ボタンが出て、読み手が全体像と拡大表示を切り替えられる。variantが3つ以上の `compare` には「すべて並べる」ボタンが付き、全variantを小さく並べて一度に比べられる（small multiples）。

- `slider`: `timeline`・`line`・`network` に使える。量を変えたときに図がどう変わるかを、つまみを動かして見せる。`slider` に量の名前（例: `"入力時間"`）、variantに量の値ごとの状態を3つ以上、`labels` かvariantの `label` に値（例: `"3秒"`）を書く。`initial` で最初に表示するvariantの番号を選ぶ（現実の値に合わせる）。値の間は短く補間し、`notes` を付ければ値ごとの説明が出る。式は書かず、値はスクリプトか手計算で求めてvariantへ展開する。captionに計算式を書く。つまみの位置は値の大きさに比例せず等間隔に並ぶため、値も等間隔（40・50・60…人）に選ぶ。境目（96人と97人）を見せたいときは、スライダーではなく `line` の交点で示す。

`timeline` を `steps` にすると、出来事が起きた順に棒が増えていく経緯図になる（障害の振り返りなど）。最初のsceneは空にせず、最初の出来事を描く。

印刷とJS無効のときは、`compare` は全variantを、`steps` は最後のsceneと全段階の文章を表示する。

## ラベルの改行

図の中の文字は自動では折り返されないため、部品が行を分ける。空白・「・」・助詞の後・文字種の変わり目を優先して区切る。「フルサービスリゾルバー」のようなカタカナの複合語は区切りを判断できないため、`"フルサービス\nリゾルバー"` のように `\n` で区切りを指定する。`\n` は表示上の改行だけで、用語との照合やステップ名では取り除く。

`tone`は `blue` / `teal` / `violet` / `amber` / `rose` / `slate` / `red`。1つの図で対象を区別する色は `blue`・`amber`・`teal` の3色までにする。この3色は、色覚の型によらず全ての組み合わせで見分けられることを明暗両方で確かめた（dataviz の validate_palette.js、`--pairs all`）。4つ目以降の対象は `violet`・`rose` を使えるが、互いや `blue` と隣り合わせず、ラベルや凡例と必ず併用する。`slate` は中立・補助、`red` は閾値・失敗・衝突などの状態だけに使い、文字や×印と組み合わせる。攻撃者・不正な第三者のように、正規の参加者と対立する対象には `rose` を使う。ラベルと札で区別できるなら、`blue` のノードの上下に置いてよい。名前は色の指定だが、作成前に文書全体で対象との対応を決め、legendでも示す。色名が同じなら明暗テーマで一貫して変わる。

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

参加者は2〜6、メッセージは1〜14。参加者が4以下なら、幅600px以下で列を詰めた配置に切り替わり、横スクロールなしで全体が見える。参加者が5以上だと横スクロールになる。部品は現在のメッセージが見える位置まで自動でスクロールし、操作バーを画面下に固定する。メッセージが14を超える往復は2つの図に分ける。スマートフォンでは8メッセージを超えると図が画面の2倍近い高さになり、現在の矢印と前後の段階を同時に見られないため、「ブラウザー経由の往復」と「サーバー間の通信」のような区切りで2つの図に分けることを勧める。参加者は左から順に等間隔で並び、時間は下へ進む。1メッセージが1 sceneになり、現在のメッセージを太く、済んだものを通常、これからのものを薄く描く。

- `kind`: `call`（実線・塗りの矢じり、既定）、`reply`（破線）、`async`（実線・開いた矢じり）。`from` と `to` が同じなら自己呼び出しのループになる。
- `label`: 矢印に載る短い動詞句。列の間に入らない長さは2行まで折り返し、3行になると拒否する。詳しい説明は `text` に書く。
- `step_label`: ステップ一覧で `label` と違う名前を使うときだけ指定する。
- `spans`: `from` から `to` までのメッセージにかかる時間や待ちを示す寸法線。最大3個、ラベルは全角7字まで。範囲内のメッセージに関わる参加者のうち、右端の参加者の生存線の右に描く（その参加者の自己呼び出しがあれば、そのラベルのさらに右）。右に入らなければ、左端の参加者の左に描き、どちらにも入らなければ拒否する。括弧は対応する最初と最後の矢印と同じ高さに付く。ラベルは何を測ったか（「直接の通信」「約110ms」）を書き、どの参加者の時間かが紛らわしいときは本文か `text` で補う。

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

`ticks` の要素は数値か `{"value": 30, "label": "5/1"}`。日付や「締め日」のように数値と単位で書けない軸は、値を日数などに置き換え、目盛りに表示名を付ける（10字以内）。

同じIDのsegmentが移動する。1つのlaneには重ならない区間だけを置く。同時に走る処理（分割して並列にした計算など）は、laneを分けて縦に並べる。軸は共有し、variantごとに変えない。`start + duration`は軸の範囲に収める。表示する丸め値は `label` に与え、geometryから必要以上に細かい数値を作らない。

未測定の工程は `{"id":"classify","lane":"work","start":4,"unknown":true,"label":"分類時間は未計測"}` とする。`duration`との同時指定は拒否され、量を表す棒は描かれない。既知工程だけで完了時刻を決めない。

長さは分かっているが原因が分からない区間（判定3分と起動4分で7分のはずが、回復は9分後だった、の残り2分）は、`unknown` ではなく実際の長さの棒を `tone: "slate"` で描き、ラベルに「未確認」と書く。本文の未確定事項にも挙げる。

timelineのspec（bundleではない）に `baseline: true` を書くと、2番目以降のvariantに最初のvariantの区間を点線で重ね、何が減ったかを示す。そのvariantで消えた区間の点線には、入る幅があれば「最初のvariantのlabel＋長さ」（例: 導入前 110ms）を書く。

variantの `segments` は空でもよい。比較対象に存在しない工程は省く。laneが空になること自体が答え（対策後は遅れがない）なら、variantに `"empty": {"slow": "なし（計算）"}` のようにlaneのIDと短いラベル（12字以内）を書く。そのlaneに薄い文字で表示し、棒がないのはデータの欠落ではないと示す。棒のあるlaneには書けない。

グループ帯は `groups: [{"label":"受信前に実行可能","summary":"約10秒","lane_ids":["a","b","c"],"tone":"teal"}]`。3行程度の関連laneをまとめると左のラベル・summaryが収まる。各variantの `group_summaries` にグループ順の文字列を渡すと、summaryも同期して切り替わる。

## line

量が別の量につれてどう変わるか（利用者数と料金、日付と件数）を折れ線で描く。2本の線が交わる点（損益分岐）を示すのに使う。

```json
{
  "type": "line",
  "x": {"min": 0, "max": 100, "unit": "人", "ticks": [0, 20, 40, 60, 80, 100], "label": "利用者数"},
  "y": {"min": 0, "max": 160000, "unit": "円", "ticks": [0, {"value": 80000, "label": "8万円"}, {"value": 160000, "label": "16万円"}]},
  "series": [
    {"id": "std", "label": "スタンダード", "tone": "blue", "points": [[0, 50000], [50, 50000], [100, 125000]]},
    {"id": "ent", "label": "エンタープライズ", "tone": "amber", "points": [[0, 120000], [100, 120000]]}
  ],
  "points": [{"id": "even", "x": 96.67, "y": 120000, "label": "約97人で同額"}],
  "markers": [{"id": "now", "x": 40, "label": "今 40人"}],
  "bands": [{"id": "next", "from": 70, "to": 90, "label": "来年の見込み"}]
}
```

線は1〜4本、各線の `points` は x の昇順（同じxは置けない）。処理能力が20:09に切り替わるような段差は、`[8.9, 300], [9, 1200]` のように直前の点をわずかに手前に置いて描き、切り替わりの正確な時刻が分からなければcaptionに書く。`dots: true` の線は点だけを描き（訓練データなどの観測値）、線より手前に重ねる。交点や閾値の値は自分で計算して `points` に書く（部品は交点を求めない）。`points` のラベルは全角10字程度までにする。スマートフォンでは長いラベルの置き場所がなく、線に触れることがある。線名は、横幅のある画面では線の右端に書き、入らなければ始点に書く。スマートフォン用の配置では、線に重ならないよう図の下に凡例として並べる。y軸名（`y.label`）は図の上に専用の行を取る。`dashed: true` で推定や見込みの線を点線にする。`variants`（各要素に `label` と上書きする `series`・`points`・`markers`・`bands`）を渡すと比較・スライダー・ステップに使える。ステップにするときは、bundleに `steps` を明示する（`sequence` と番号付きの `network` だけが省略できる）。同じ `id` の線は、variantごとに点の数が違っても補間して動く。凡例の代わりに線名を線に直接書くので、`legend` は不要。

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

列は3または4、行は2または3。1セルに1ノード。ノードのない行は詰め、迂回経路が必要なときだけ上下に余白を足す。ノードと `sequence` の参加者の `label` が `glossary` の用語と同じなら、本文の用語と連動して強調される。`detail`は短い補足、`active_nodes`は当該状態で使うノードの一覧。使わないノードは薄く残す。全variantで位置を保ち、経路の変更を見せる。

辺の `label` は動詞句を基本にする。ノードの間に1行で入らないラベルは2行に折り返してから、それでも入らない場合だけ迂回する。コミットの親子のように動詞がない関係では省略できる。埋めるためだけのラベル（「続き」など）は付けない。

`kind` は `request`（破線）、`file`（実線）、`conflict`（向きのない赤い破線と中央の×）。条件付きでだけ通る経路（「5万円以上なら部長へ」）は `"optional": true` で点線にし、ラベルに条件を書く。条件のある経路とない経路を1枚に描ける。`conflict` は2つの変更や設定がぶつかる箇所を、片方のノードの印ではなく2点の間の関係として描く。

`hidden_nodes` に挙げたノードは、そのvariantでは描かない（位置は保ち、切り替え時にフェードする）。「まだ存在しない」「もう存在しない」ものに使い、薄く残すと結果を先に見せてしまう場合に使う。使わないが存在するノードは、`active_nodes` から外して薄く残す。

`edges` は空の配列でもよい。そのvariantで通信が起きないこと（例: 端末内のキャッシュにヒットした状態）を示す。

互いにやり取りするノードは隣のセルに置く。離れたセル同士を結ぶと、間のノードを避ける長い曲線になり、読み手が目で追いにくい。

`marks` は、そのvariantで起きることをノードに付ける短い札。札の色は凡例の色と意味を重ねない（凡例で teal を「暗号文」にしたなら、成功の札は slate か別の色にする）。`{"node": "resolver", "label": "ここでヒット", "tone": "teal"}` のように、1variantに3個まで、ラベルは全角8字まで。どこで答えが見つかるか、どこで失敗するかを、ノードの薄さだけに頼らず示す。

`route`は通常省略し、必要なときだけ `above` / `below`、`label_side`は `above` / `below`を指定する。`route` を指定した辺はその側を通し、余白が足りなければ図の上下を広げる。それでも通らなければ生成を拒否する（黙って反対側へ回さない）。第三のノードや既存のラベルとぶつかる経路は迂回し、収まらなければ入力を拒否する。拒否時はラベルを短くするか、認可ノードを別の行へ移す。任意のトポロジーに完全自動で最適配置する道具ではない。

### 番号付きの辺で1段階ずつ進める

`variants` の代わりに、トップレベルの `edges` へ `step`（1から連番）を付けると、段階ごとのsceneを作る。全sceneで全ての辺を描き、済んだ辺は通常、現在の辺は太く、これからの辺は薄くする。同じ段階に複数の辺を置ける。`text` はその段階の説明文になる。bundleを `mode: "steps"` にすれば `steps` は省略でき、辺のラベルから先頭の番号（①や1.）を除いた文字列が段階名になる。ラベルのない辺は「手順N」になる。段階ごとの札は、トップレベルの `marks` に `step` を付けて渡す（`{"node": "x2", "label": "新しいID", "step": 3}`）。

```json
{"type": "network", "columns": 4, "rows": 2, "nodes": [...],
 "edges": [
   {"id": "q1", "from": "pc", "to": "resolver", "label": "① 問い合わせ", "kind": "request", "step": 1, "text": "PCはリゾルバーに1回だけ問い合わせます。"},
   {"id": "q2", "from": "resolver", "to": "root", "label": "② .comは?", "kind": "request", "step": 2}
 ]}
```

## decision

`{"type":"decision","columns":[{"eyebrow":"段階","title":"方針","items":["選択肢1","選択肢2"],"footer":"結果・条件"}, ...]}`。columnsは2つ、itemsも2つ。詳細な理由は本文に置く。

## 一度の生成で確認する例

[animated-example.json](../assets/animated-example.json)は架空の処理を使った例。実際のサービスの時間や制約として流用しない。

```sh
python3 scripts/diagrams.py assets/animated-example.json --output /tmp/animated.html
node scripts/check-diagrams.cjs /tmp/animated.html /tmp/animated-evidence
```
