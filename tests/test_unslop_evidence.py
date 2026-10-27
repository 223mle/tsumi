import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        for relative in ['evals/prose', 'skills/unslop']:
            shutil.copytree(ROOT / relative, self.root / relative)
        (self.root / 'evals/bin').mkdir()
        shutil.copyfile(ROOT / 'evals/bin/summarize-prose', self.root / 'evals/bin/summarize-prose')

    def run_summary(self):
        return subprocess.run([sys.executable, str(self.root / 'evals/bin/summarize-prose')], capture_output=True, text=True)

    def test_saved_evidence_is_complete(self):
        result = self.run_summary()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('calibration: 4/4', result.stdout)

    def test_missing_trial_is_rejected(self):
        path = self.root / 'evals/prose/outputs.json'
        rows = json.loads(path.read_text())
        path.write_text(json.dumps(rows[1:]))
        self.assertNotEqual(self.run_summary().returncode, 0)

    def test_changed_skill_cannot_reuse_old_score(self):
        with (self.root / 'skills/unslop/SKILL.md').open('a') as stream:
            stream.write('\nA different rule.\n')
        self.assertNotEqual(self.run_summary().returncode, 0)

    def test_invalid_control_judgment_is_rejected(self):
        control = json.loads((self.root / 'evals/prose/controls.json').read_text())[0]
        path = self.root / 'evals/prose/judgments.json'
        rows = json.loads(path.read_text())
        for row in rows:
            if row['label'] == control['label']:
                row['pass'] = not control['expected']
        path.write_text(json.dumps(rows))
        self.assertNotEqual(self.run_summary().returncode, 0)


if __name__ == '__main__':
    unittest.main()
