# /correct への上書き

pstack の `correct/SKILL.md` を先に読み、そのまま従う。足すのは次の一点。

- 直す対象が開発中のエージェントの出力（プロンプト、スキル、ツール定義、スキーマ、テンプレートで決まるもの）なら、`/correct` ではなく tsumi-mode の `playbooks/harden.md` を使う。リポジトリのコードの誤りは `/correct` のまま。
