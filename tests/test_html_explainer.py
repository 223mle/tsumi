import json
import unittest
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
RENDER = ROOT / "skills/html-explainer/scripts/render.py"
EXAMPLE = ROOT / "skills/html-explainer/assets/example.json"

def run(tmp_path, doc):
    src, out = tmp_path / "in.json", tmp_path / "out.html"
    src.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    p = subprocess.run([sys.executable, str(RENDER), str(src), "--output", str(out)], capture_output=True, text=True)
    return p, out

class RendererTests(unittest.TestCase):
  def base_doc(self, **figure):
    default = {"id": "f", "kind": "bars", "title": "f", "summary": "s", "caption": "c", "status": "illustrative", "unit": "u", "rows": [{"label": "a", "value": 1}]}
    default.update(figure)
    return {"title": "x", "lead": "y", "sections": [{"id": "s", "title": "t", "figures": [default]}]}

  def test_example_renders_all_kinds(self):
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
      p, out = run(Path(d), json.loads(EXAMPLE.read_text(encoding="utf-8")))
      self.assertEqual(p.returncode, 0, p.stderr)
      text = out.read_text(encoding="utf-8")
      self.assertIn('data-kind="flow"', text); self.assertIn('data-kind="timeline"', text); self.assertIn('data-kind="bars"', text); self.assertIn('data-kind="table"', text)
      self.assertIn('<script>', text); self.assertIn('<style>', text)

  def test_text_is_escaped(self):
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
      tmp_path = Path(d)
      doc = {"title": "<script>alert(1)</script>", "lead": "<b>x</b>", "sections": [{"id": "s", "title": "T", "paragraphs": ["<img src=x onerror=alert(1)>"]}]}
      p, out = run(tmp_path, doc)
      self.assertEqual(p.returncode, 0)
      text = out.read_text(encoding="utf-8")
      self.assertNotIn("<script>alert(1)</script>", text)
      self.assertIn("&lt;script&gt;", text)

  def test_invalid_measured_without_source_does_not_replace_output(self):
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
      tmp_path = Path(d)
      old = tmp_path / "out.html"
      old.write_text("previous", encoding="utf-8")
      doc = {"title": "x", "lead": "y", "sections": [{"id": "s", "title": "t", "figures": [{"id": "f", "kind": "bars", "title": "f", "summary": "s", "caption": "c", "status": "measured", "rows": [{"label": "a", "value": 1}]}]}]}
      src = tmp_path / "bad.json"; src.write_text(json.dumps(doc), encoding="utf-8")
      p = subprocess.run([sys.executable, str(RENDER), str(src), "--output", str(old)], capture_output=True, text=True)
      self.assertNotEqual(p.returncode, 0); self.assertEqual(old.read_text(encoding="utf-8"), "previous")

  def test_rejects_unsafe_url(self):
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
      tmp_path = Path(d)
      doc = {"title": "x", "lead": "y", "sources": [{"id": "s", "title": "x", "url": "javascript:alert(1)"}], "sections": [{"id": "a", "title": "A"}]}
      p, _ = run(tmp_path, doc)
      self.assertNotEqual(p.returncode, 0); self.assertIn("URL", p.stderr)

  def test_rejects_ids_colliding_with_generated_anchors(self):
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
      doc = self.base_doc()
      doc["sources"] = [{"id": "main", "title": "x", "url": "https://example.com"}]
      p, _ = run(Path(d), doc)
      self.assertNotEqual(p.returncode, 0); self.assertIn("duplicate id main", p.stderr)

  def test_rejects_unhashable_kind_and_status_without_traceback(self):
    from tempfile import TemporaryDirectory
    for field, value in (("kind", []), ("status", {})):
      with self.subTest(field=field), TemporaryDirectory() as d:
        p, _ = run(Path(d), self.base_doc(**{field: value}))
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)

  def test_rejects_blank_table_column(self):
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
      doc = self.base_doc(kind="table", columns=["", "value"], rows=[["a", "b"]])
      p, _ = run(Path(d), doc)
      self.assertNotEqual(p.returncode, 0); self.assertIn("columns", p.stderr)

  def test_rejects_timeline_end_overflow(self):
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
      doc = self.base_doc(kind="timeline", unit="s", rows=[{"label": "a", "start": 1e308, "duration": 1e308}])
      p, _ = run(Path(d), doc)
      self.assertNotEqual(p.returncode, 0); self.assertIn("must be finite", p.stderr)

  def test_tiny_bar_value_keeps_full_scale(self):
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
      doc = self.base_doc(rows=[{"label": "tiny", "value": 1e-320}])
      p, out = run(Path(d), doc)
      self.assertEqual(p.returncode, 0, p.stderr)
      self.assertIn('style="width:100.0000%"', out.read_text(encoding="utf-8"))

  def test_source_note_without_url_renders_title_and_note(self):
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
      doc = self.base_doc(status="measured", source_ids=["attachment"])
      doc["sources"] = [{"id": "attachment", "title": "添付資料", "note": "ユーザー提供の計測表"}]
      p, out = run(Path(d), doc)
      self.assertEqual(p.returncode, 0, p.stderr)
      text = out.read_text(encoding="utf-8")
      self.assertIn("添付資料", text); self.assertIn("ユーザー提供の計測表", text)
      self.assertIn('class="source-ref" href="#attachment">添付資料</a>', text)

  def test_flow_arrow_text_remains_accessible(self):
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
      doc = self.base_doc(kind="flow", steps=[{"label": "A", "detail": "a", "to_next": "次へ"}, {"label": "B", "detail": "b"}])
      p, out = run(Path(d), doc)
      self.assertEqual(p.returncode, 0, p.stderr)
      text = out.read_text(encoding="utf-8")
      self.assertIn('<span class="arrow" aria-hidden="true">→</span><span>次へ</span>', text)
      self.assertNotIn('<li class="flow-arrow" aria-hidden="true">', text)

  def test_table_is_keyboard_scroll_region(self):
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
      doc = self.base_doc(kind="table", columns=["列"], rows=[["値"]])
      p, out = run(Path(d), doc)
      self.assertEqual(p.returncode, 0, p.stderr)
      text = out.read_text(encoding="utf-8")
      self.assertIn('class="table-wrap" tabindex="0" role="region"', text)
      self.assertIn("横にスクロールして表全体を確認できます。", text)

  def test_rejects_integer_that_overflows_float(self):
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
      doc = self.base_doc(rows=[{"label": "huge", "value": 10**400}])
      p, _ = run(Path(d), doc)
      self.assertNotEqual(p.returncode, 0)
      self.assertIn("finite number required", p.stderr)
      self.assertNotIn("Traceback", p.stderr)

if __name__ == "__main__": unittest.main()
