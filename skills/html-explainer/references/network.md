# 経路図コンポーネント

`scripts/network.py`は、ノードのグリッド位置と、処理の種類だけから、前後比較用のSVGを生成します。入力にSVG座標・パス・色のCSSを書かないため、図の大きさやラベルが変わっても共通の余白と経路を保てます。

```python
from scripts.network import render_network
svgs = render_network(spec, "transfer")
```

`spec`は`type: "network"`、`columns`（3または4）、`rows`（2または3）、`nodes`、任意の`boundaries`、`variants`を持ちます。ノードは`id`、`label`、`column`、`row`と、任意の`detail`・`tone`を指定します。`boundaries.node_ids`は囲むノードを列挙します。variantごとに同じedge IDを使うと、外側のアニメーション実装が`data-key`で同じ要素を対応付けられます。

辺の`kind`は`request`または`file`です。前者は破線、後者は実線になります。`route`は`direct`、`above`、`below`から選びます。これは意味のある経路の選択で、ピクセル座標ではありません。`label_side`でラベルを線の上・下へ避けられます。

生成されたSVGは`title`、`desc`、`role="img"`、`aria-labelledby`を持ちます。全ノード、辺、境界、ラベルに安定した`data-key`を付け、ノードには`data-obstacle`を付けます。`diagrams.py`が同梱のJSと組み合わせ、同じキーの属性を補間します。`prefers-reduced-motion`では選んだvariantへ即時切替し、JavaScript無効時と印刷時は全variantを静止表示します。

CSSは`--diagram-blue`、`--diagram-teal`、`--diagram-violet`、`--diagram-amber`、`--diagram-rose`、`--diagram-slate`、`--diagram-red`と、共通の`--text`、`--muted`、`--surface`、`--subtle`、`--line`を定義します。コンポーネントはテーマ値を上書きしません。
