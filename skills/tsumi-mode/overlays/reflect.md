# /reflect への上書き

pstack の `reflect/SKILL.md` を先に読み、そのまま従う。足すのは次の二点。

- synthesizer の Accepted の各行に `eval case` 欄を足す。値は `yes: <お題 id 案と一行の中身>` か `no: <理由>`。`yes` の行は、スキルを直す前に tsumi の `evals/cases/` にお題を足す。
- ユーザーの修正が transcript にあれば、修正ログに同じクラスの行があるかを見る。2回目なら tsumi-mode の「同じ修正の2回目」を当て、プロンプトへの追記ではなく Backlog か Harden に回す。
