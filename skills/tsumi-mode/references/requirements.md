# 前提プラグイン

tsumi は pstack の上に乗る。作業の前に確かめる。

| プラグイン | 入っているかの見分け方 | ファイルの場所 |
|---|---|---|
| `pstack` | スキル一覧に `setup-pstack` がある | pstack のスキルの多くはスラッシュ専用で一覧に出ない。`setup-pstack` と同じ階層にある。`<setup-pstack のディレクトリ>/../poteto-mode/SKILL.md`、`../poteto-mode/playbooks/<名前>.md`、`../principle-<名前>/SKILL.md`、`../unslop/SKILL.md`、`../technical-writing/SKILL.md`、`../correct/SKILL.md`、`../reflect/SKILL.md`。 |

見つからなければ止まる。ユーザーに `/add-plugin pstack` を案内する。足りない部分を自分で作らない。

pstack が複数の版で見つかったら、`.cursor-plugin/plugin.json` の `version` が一番大きいものを使う。
