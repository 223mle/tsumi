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
