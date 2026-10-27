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
    def test_past_failure_is_reviewed(self):
        text = '共有ファイルを変更します。\n同梱ツールなどを使えます。接続先の環境変数を引き継ぎます。'
        rows = list(module.findings(text))
        self.assertEqual({r['term'] for r in rows}, {'共有ファイル', '同梱', 'など', '接続先'})
        self.assertEqual(rows[0]['line'], 1)

    def test_explicit_examples_and_source_need_no_word_warning(self):
        text = 'インストール済みのツールを使えます（例：`imginfo`、`zip`）。全内容は [Containerfile](runtime/Containerfile) で確認できます。'
        self.assertEqual(list(module.findings(text)), [])

    def test_known_referent_still_requires_human_or_model_judgment(self):
        rows = list(module.findings('文書 API の接続先を設定します。'))
        self.assertEqual(rows[0]['term'], '接続先')

    def test_code_and_destinations_are_not_rewritten(self):
        text = '```sh\necho 同梱など\n```\n`同梱`\n[一覧](https://example.org/など)\n共有ファイル'
        rows = list(module.findings(text))
        self.assertEqual([(r['line'], r['term']) for r in rows], [(6, '共有ファイル')])

    def test_cli_does_not_modify_input_and_reports_failures(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'article.md'
            path.write_text('共有ファイル', encoding='utf-8')
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)['review_candidates'][0]['line'], 1)
            self.assertEqual(path.read_text(), '共有ファイル')
            missing = subprocess.run([sys.executable, str(SCRIPT), str(path.parent / 'missing')], capture_output=True, text=True)
            self.assertEqual(missing.returncode, 2)


if __name__ == '__main__':
    unittest.main()
