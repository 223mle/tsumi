# HTML解説スキルの確認記録

2026-10-29 JST。新規スキルの最初の実装確認であり、初回成功率を測る統計評価ではない。

## 実行条件

- 変更前: tsumi `141b44c`。unslopで文章を整え、自由にHTMLを作成。
- 変更後: html-explainerとunslop。同じ架空サービスの依頼を、前の会話を持たない別エージェントへ渡した。
- pstack: `0.15.25`。実行エージェントに採点基準は渡していない。
- 別のレビュー担当が生成主体を伏せたA/BのHTMLを読んだ。BのPC・スマートフォン・印刷・JS無効の画像も確認した。Aの全表示条件は実描画していないため、見た目の優劣を全面的には判定していない。

## 結果

| 検査 | 観測 |
| --- | --- |
| 既存を含むunittest | 33件成功 |
| check-skills / quick_validate | 成功 |
| 描画 | 1440px、390px、明暗テーマ、印刷、JS無効を確認 |
| 検査器の確認 | 初稿で実際に発生した棒の非表示を拒否。CSS修正後は成功。幅2000pxの合成不良例も拒否 |
| 内容の保持 | A/Bとも2秒・4秒・1秒と合計7秒、未定の受付、未測定の改善後総時間、容量制約を保持 |
| 図の数値表現 | Aは軸なしのため部分不合格。Bは実値から軸と幅を生成し、区間を表示 |
| 重複 | A/Bとも現状の図と本文の重複が残った。納品見本では重複するフローと表の行を削除し、比較の尺度もそろえた |
| トリガー評価 | 変更前後ともClaude CLIのauthentication_failedで実行不能。Cursor CLIは未導入。通過率・回帰・flakyは判定不能 |

通常の全件3試行は未実施。トリガーのモデル判断に到達していないため、0%の品質評価として集計しない。全件の回帰評価が終わるまでPRはドラフトとする。

## 再実行

```sh
python3 -m unittest discover -s tests
scripts/check-skills
python3 skills/html-explainer/scripts/render.py skills/html-explainer/assets/example.json --output /tmp/document.html
node skills/html-explainer/scripts/check-render.cjs /tmp/document.html /tmp/document-evidence
```

Playwrightのパスが必要ならNODE_PATH、既存Chromeを使う場合はCHROME_PATHを指定する。検査用に一時プロファイルを使う。スクリーンショットとreport.jsonは最後の引数のディレクトリへ保存される。実行時の証拠はローカルの `/private/tmp/html-final-evidence`、`/private/tmp/html-overflow-evidence`、`/private/tmp/html-explainer-reproduced` に保存した。生成依頼と判定基準は同じディレクトリのrequests.json、rubric.mdにある。

Claude CLIへログイン後、同一のpstack版とモデルで旧版・新版のトリガー評価を再実行する。追加した3つのケースを先に1回ずつ回し、最後に全件を3回ずつ回す。ログイン状態は本作業では変更していない。
