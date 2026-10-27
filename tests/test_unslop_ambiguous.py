import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/unslop/scripts/find-ambiguous.py'
spec = importlib.util.spec_from_file_location('ambiguous', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AmbiguousTests(unittest.TestCase):
    def test_generic_ambiguity_has_actionable_review_questions(self):
        rows = list(module.findings('これを保存し、それを削除する。\n工具などを使い、適宜対応する。'))
        self.assertEqual({r['term'] for r in rows}, {'これ', 'それ', 'など', '適宜'})
        self.assertEqual({r['kind'] for r in rows}, {'referent', 'scope', 'criterion'})
        for row in rows:
            self.assertTrue(row['question'])
        self.assertEqual(rows[0]['line'], 1)

    def test_domain_terms_are_not_findings(self):
        text = '共有ファイルの接続先と起動ファイルを確認する。同梱ツールを使う。'
        self.assertEqual(list(module.findings(text)), [])

    def test_connectives_are_not_demonstrative_references(self):
        self.assertEqual(list(module.findings('これまでの記録をそれぞれ確認する。それでも処理は続く。')), [])

    def test_explicit_examples_and_source_need_no_word_warning(self):
        text = 'インストール済みのツールを使えます（例：`imginfo`、`zip`）。全内容は [Containerfile](runtime/Containerfile) で確認できます。'
        self.assertEqual(list(module.findings(text)), [])

    def test_known_referent_still_requires_human_or_model_judgment(self):
        rows = list(module.findings('設定を保存します。これを配布します。'))
        self.assertEqual(rows[0]['term'], 'これ')

    def test_code_and_destinations_are_not_rewritten(self):
        text = '```sh\necho これなど\n```\n`それ`\n[一覧](https://example.org/など)\nこれを保存'
        rows = list(module.findings(text))
        self.assertEqual([(r['line'], r['term']) for r in rows], [(6, 'これ')])

    def test_cli_does_not_modify_input_and_reports_failures(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'article.md'
            path.write_text('これを保存', encoding='utf-8')
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)['review_candidates'][0]['line'], 1)
            self.assertEqual(path.read_text(), 'これを保存')
            missing = subprocess.run([sys.executable, str(SCRIPT), str(path.parent / 'missing')], capture_output=True, text=True)
            self.assertEqual(missing.returncode, 2)


if __name__ == '__main__':
    unittest.main()
