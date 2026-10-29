# 参照したスキルと設計の採否

2026-10-29 JSTにGitHub APIでスター数とHEADを確認し、各SKILL.mdを読んだ。スターは調査候補を選ぶために使い、図の読みやすさの証明には使っていない。数値はリポジトリ全体のスナップショットであり、個別スキルの利用者数ではない。

| リポジトリ | スター | 読んだ固定版 |
| --- | ---: | --- |
| nicobailon/visual-explainer | 10,676 | [SKILL.md](https://github.com/nicobailon/visual-explainer/blob/5f378868e0ea745a6284b51e710c390f0c76f72c/plugins/visual-explainer/SKILL.md) |
| cathrynlavery/diagram-design | 62,607 | [リポジトリ](https://github.com/cathrynlavery/diagram-design/tree/0cf73c3fcc56667ad91a9a04c439ac6ccfabc9d1) |
| anthropics/skills | 184,602 | [frontend-design](https://github.com/anthropics/skills/blob/ca45fc496a3436251f191354091d557da31c15b5/skills/frontend-design/SKILL.md) |

visual-explainerからは、図一つに一つの主張、動作の分かる矢印、比較時の同じ構図、描画後の確認を採った。diagram-designからは、問いに応じた図選択と一貫したデザイン部品を採った。frontend-designからは、読者と用途を決めてから配色・文字・配置を選ぶ順序を採った。本文・コード・テンプレートの転載は行っていない。前二者はMIT。frontend-designはSKILL.mdがそのディレクトリのLICENSE.txtを参照しており、リポジトリ全体のライセンスを推定しない。

## 比較検討

参照HTMLの分析担当と外部スキルの調査担当が、自由形式SVG、定型HTML/CSS、Mermaidを比較した。

| 方式 | 利点 | 今回の判断 |
| --- | --- | --- |
| 自由形式SVG | 特殊な経路、境界、注釈を精密に描ける | 特殊図に使う。すべての図で座標を生成すると、数値更新や長い日本語で破綻しやすい |
| 構造化データからHTML/CSSを生成 | 軸・値・ラベルを一元化し、文字を折り返せる | 直列フロー、棒、時系列、表の既定にする |
| Mermaid | 既存のグラフ記法を再利用できる | 既存入力や明示した指定に使う。数値の軸や細かな注釈の既定にはしない |

visual-explainerの「SVGを既定にする」と、今回の「繰り返し使って初回から安定させる」は別の目的である。図の語彙を多数増やすより、繰り返す図の計算を固定し、残りの図だけ自由に描く。

依頼者が示したHTMLからは、左目次、紙面の余白、章の階層、caption、確度の表示、明暗テーマを参考にした。社内の本文、固有名詞、計測値、図の画像はパッケージへ収録していない。見本にあった小画面でのラベル非表示は採用せず、折り返しと外側ラベルにした。
