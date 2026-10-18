### Eval（tsumi の上書き）

pstack の `poteto-mode/playbooks/eval.md` を先に読む。blinding の規則と、判定を transcript から取る規則はそのまま使う。

tsumi のリポジトリでスキル、プロンプト、スキーマを変えたときは、次を足す。

1. 変更前の版で、tsumi リポジトリの `evals/` を回す（手順は `evals/README.md`）。baseline があれば使う。
2. 変える。
3. 同じお題、同じ pstack の版、同じモデルで回す。
4. 比べる。`must-pass` のお題が1件でも落ちたら出さない。落ちた理由を transcript から説明する。
5. 新しく足したお題は、変更前の版で落ちることも記録する。

**Reply:** pstack の Eval の返信に加えて、通過率の前後、回帰したお題、不安定なお題、使った pstack の版。
