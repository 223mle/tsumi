# 図部品の改善と比較

2026-10-29 JST。前版は `b2883f0`。pstackは0.15.25を固定。評価の基準は、内容を保持したまま元資料に近い情報密度、意味ごとの配色、前後の同期アニメーションを出せること。利用者の資料はローカルだけで扱い、このリポジトリには保存していない。

## 実際に失敗した点と修正先

| 失敗 | 共通部品での対策 | 確認 |
| --- | --- | --- |
| 図を別々の箱・表へ分解し、縦に長くなる | 共通軸のtimeline、群の帯、同じ場所のvariant | 同じ幅でページ長と図の画像を比較 |
| 前後切替が瞬時の図の交換になる | data-keyを使う位置・幅・透明度の補間、panel同期 | 途中フレームが両端と異なることを確認 |
| 矢印ラベルが重なる | ノードだけでなく、既存のラベル領域を避けて経路を選ぶ | 実際の重なりを再現した不良例を拒否 |
| 同じIDの辺で、切替後に古い文言が残る | g内のラベル更新と、選択sceneの文言照合 | 別ラベルへ変わる例で確認 |
| 未計測時間へ仮の秒数を置く | unknown segment。durationとの同時指定を拒否 | 新しい実行エージェントで同じ架空の依頼を再実行 |
| 再構成で原図だけの出典リンクが落ちる | compose.pyが原図のa要素をcaptionへ保持 | source link保持テスト |

## 結果

- `python3 -m unittest discover -s tests`: 55件成功。
- `scripts/check-skills`とskill-creatorのquick_validate: 成功。
- 同じ資料の図9群を、全てJSONから生成。本文66段落・表50行・外部リンク30件・ツールチップ5件を照合。
- 1440px幅で、元資料17,468px、前版23,486px、改善版17,027px。本文削除による短縮ではない。これはページの長さの比較で、読解速度の計測ではない。
- 元資料と同じ題材の図検査50項目が成功。途中補間、同期、更新後のラベル、連打、流れの再生・停止、reduced-motion、印刷、JS無効を含む。
- 架空の別題材は、最初の生成で入力時間を重複加算し、未測定工程へ仮の秒数を置いた。unknown segmentと起点の扱いを追加した後、新しいエージェントで再実行し、既知の10秒と未測定の分類時間を分けた。追加の図検査19項目が成功。
- 意図的に全edge labelを同じ場所へ寄せた合成不良HTMLは、明暗・切替後・モバイルで重なりとして検出された。

2つの題材で確認した結果であり、すべての資料で初稿が通る確率を測ったものではない。図と文章の意味は、数値と幾何の検査だけでは保証できない。

## 再実行

```sh
python3 scripts/diagrams.py assets/animated-example.json --output /tmp/animated.html
node scripts/check-diagrams.cjs /tmp/animated.html /tmp/animated-evidence
```

上のパスは `skills/html-explainer` からの相対パス。ページ全体は `scripts/check-render.cjs` でも確認する。元資料の再生成は `scripts/compose.py source.html figures.json --output rebuilt.html`。完成したHTMLへの個別座標・色の修正は行わず、同じJSONから生成し直した。

## 未実施

通常の全件3試行のトリガー回帰評価は、Claude CLIが未ログインのため実行できない。`claude auth status` の `loggedIn: false` を再確認した。Cursor CLIも前回確認時点で未導入。モデル実行に到達していない結果を、品質の0%として集計しない。PRは引き続きドラフトとする。

## 2026-10-30 読み手の理解を基準にした改善

前版は `371ad64`。visual-explainer v0.14.0、Claude の artifact-diagramming と dataviz を読み、採否を [sources.md](../../skills/html-explainer/references/sources.md) に記した。評価の基準は「新人が一度読めば仕組みを説明できるか」。

### 別エージェントでの生成と、読み手役のレビュー

前の会話を持たない実行エージェントにスキルだけを渡し、架空の2題材を生成させた。別のエージェントには、新人の読み手として完成ページを読ませた。どちらにも採点基準の内部事情は渡していない。

| 題材 | 生成時のエラー | 見つかった不足 | 共通部品での対策 |
| --- | --- | --- | --- |
| DNSの名前解決 | なし。検査49項目成功 | 比較図に状態ごとの説明文がない。カタカナ複合語が語の途中で改行。390pxで現在の矢印が画面外 | 比較の `notes`、ノードの `marks`、句と `\n` を優先する改行、画面下に固定するステップ操作 |
| 同上（新人役の読解） | — | 寸法線がブラウザー側に出て「端末が階層をたどる」と誤読。流れる点が一斉に動き並列処理に見える。時間短縮の比較で元の長さを覚えておく必要がある | 寸法線を測る区間の参加者の横へ。流れを番号順に1本ずつ再生。timelineの `baseline` で元の区間を点線で残す |
| Gitのmergeとrebase | 節と図のIDの重複1件 | 埋めるための辺ラベル、まだないノードが薄く見えて結果を先に見せる、衝突を2点の関係で描けない、390pxで変化した部分が画面外 | ラベルなしの辺、`hidden_nodes`、`kind: "conflict"`、変化した辺へ横スクロールを追従、「全体を縮小表示」 |

新人役は、読後にDNSの解決順序とキャッシュで省かれる問い合わせを正しく説明した。食い違いとして挙げた項目のうち、部品で防げないもの（ステップ名と矢印ラベルの語の不一致など）は [figure-selection.md](../../skills/html-explainer/references/figure-selection.md) の照合項目に加えた。

### 配色

dataviz の `validate_palette.js` で、図の色を明暗両方で検査した。旧配色は、`rose` と `red` の差（ΔE 9.9）と `teal` の彩度が基準を下回った。対象の区別には `blue`・`amber`・`teal` の3色を使い、この3色が全組み合わせ（`--pairs all`）で明暗とも合格する値にした。

### 検査

- `python3 -m unittest discover -s tests`: 79件成功（新規 `tests/test_html_steps.py` を含む）。
- `scripts/check-skills`: 成功。
- 作例 `assets/showcase.json`、DNS、Gitのページで `check-render.cjs` と `check-diagrams.cjs` が成功。ステップの前進・←→キー・最終段階での「次へ」の無効化・説明文の追従、すべて並べる表示、印刷時の畳んだ内容を検査に加えた。
- ステップ図の同期を壊した合成不良HTMLで、検査が4項目失敗することを確認した。
