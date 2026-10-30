import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "skills/html-explainer/scripts"
sys.path.insert(0, str(SCRIPTS))

from blocks import inline  # noqa: E402
from diagrams import render_diagram  # noqa: E402
from network import render_network  # noqa: E402
from sequence import render_sequence  # noqa: E402


def sequence_spec(**extra):
    spec = {
        "type": "sequence",
        "actors": [{"id": "a", "label": "ブラウザー"}, {"id": "b", "label": "API"}, {"id": "c", "label": "データベース"}],
        "messages": [
            {"id": "m1", "from": "a", "to": "b", "label": "要求", "text": "ブラウザーが要求します。"},
            {"id": "m2", "from": "b", "to": "c", "label": "読む"},
            {"id": "m3", "from": "c", "to": "b", "label": "行", "kind": "reply"},
            {"id": "m4", "from": "b", "to": "b", "label": "整形"},
        ],
    }
    spec.update(extra)
    return spec


def render_doc(doc):
    with TemporaryDirectory() as d:
        src, out = Path(d) / "in.json", Path(d) / "out.html"
        src.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        p = subprocess.run([sys.executable, str(SCRIPTS / "render.py"), str(src), "--output", str(out)], capture_output=True, text=True)
        return p, (out.read_text(encoding="utf-8") if out.exists() else "")


class SequenceTests(unittest.TestCase):
    def test_one_scene_per_message_marks_current_and_future(self):
        scenes = render_sequence(sequence_spec())
        self.assertEqual(len(scenes), 4)
        second = scenes[1]
        self.assertRegex(second, r'class="dg-msg dg-msg-call dg-tone-blue is-done" data-key="msg:m1" opacity="1"')
        self.assertRegex(second, r'class="dg-msg dg-msg-call dg-tone-blue is-current" data-key="msg:m2"')
        self.assertRegex(second, r'data-key="msg:m3" opacity="0.16"')
        keys = re.findall(r'data-key="([^"]+)"', second)
        self.assertEqual(len(keys), len(set(keys)))

    def test_current_actors_are_highlighted(self):
        scene = render_sequence(sequence_spec())[1]
        self.assertIn('dg-actor dg-tone-slate is-current" data-key="actor:b"', scene)
        self.assertIn('dg-actor dg-tone-slate is-current" data-key="actor:c"', scene)
        self.assertNotIn('is-current" data-key="actor:a"', scene)

    def test_rejects_unknown_actor_and_overlong_label(self):
        with self.assertRaisesRegex(ValueError, "from/to"):
            render_sequence(sequence_spec(messages=[{"id": "x", "from": "a", "to": "zz", "label": "要求"}]))
        long = "とても長いラベル" * 10
        with self.assertRaisesRegex(ValueError, "too long"):
            render_sequence(sequence_spec(messages=[{"id": "x", "from": "a", "to": "b", "label": long}]))

    def test_span_requires_order(self):
        with self.assertRaisesRegex(ValueError, "after"):
            render_sequence(sequence_spec(spans=[{"from": "m3", "to": "m1", "label": "1秒"}]))
        scene = render_sequence(sequence_spec(spans=[{"from": "m2", "to": "m3", "label": "約1秒"}]))[-1]
        self.assertIn("約1秒", scene)


class StepModeTests(unittest.TestCase):
    def bundle(self, **extra):
        b = {"id": "seq", "title": "往復", "caption": "説明用", "mode": "steps", "panels": [{"spec": sequence_spec()}]}
        b.update(extra)
        return b

    def test_sequence_derives_steps_and_controls(self):
        html = render_diagram(self.bundle())
        self.assertIn('data-mode="steps"', html)
        self.assertEqual(html.count('data-step="'), 4)
        self.assertIn('data-go="1"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('class="dg-step-notes"', html)
        self.assertIn("ブラウザーが要求します。", html)

    def test_explicit_steps_must_match_scene_count(self):
        with self.assertRaisesRegex(ValueError, "one step per scene"):
            render_diagram(self.bundle(steps=[{"label": "a"}]))

    def test_network_steps_need_explicit_steps(self):
        net = {"type": "network", "columns": 3, "rows": 2,
               "nodes": [{"id": "a", "label": "A", "column": 1, "row": 1}, {"id": "b", "label": "B", "column": 2, "row": 1}],
               "variants": [{"label": "1", "edges": [{"id": "e", "from": "a", "to": "b", "label": "送る", "kind": "request"}]},
                            {"label": "2", "edges": [{"id": "e", "from": "b", "to": "a", "label": "返す", "kind": "file"}]}]}
        with self.assertRaisesRegex(ValueError, "steps"):
            render_diagram({"id": "n", "title": "t", "caption": "c", "mode": "steps", "panels": [{"spec": net}]})
        html = render_diagram({"id": "n", "title": "t", "caption": "c", "mode": "steps", "panels": [{"spec": net}],
                               "steps": [{"label": "送る"}, {"label": "返す", "text": "BがAへ返します。"}]})
        self.assertIn("BがAへ返します。", html)


class NetworkLayoutTests(unittest.TestCase):
    def test_single_row_without_detours_is_compact(self):
        spec = {"type": "network", "columns": 3, "rows": 3,
                "nodes": [{"id": "a", "label": "A", "column": 1, "row": 3}, {"id": "b", "label": "B", "column": 2, "row": 3}],
                "variants": [{"label": "v", "edges": [{"id": "e", "from": "a", "to": "b", "label": "送る", "kind": "request"}]}]}
        svg = render_network(spec)[0]
        height = float(re.search(r'viewBox="0 0 960 ([\d.]+)"', svg).group(1))
        self.assertLess(height, 160)

    def test_label_is_vertically_centred_without_detail(self):
        spec = {"type": "network", "columns": 3, "rows": 2,
                "nodes": [{"id": "a", "label": "A", "column": 1, "row": 1}, {"id": "b", "label": "B", "column": 2, "row": 1}],
                "variants": [{"label": "v", "edges": []}]}
        svg = render_network(spec)[0]
        rect_y = float(re.search(r'data-key="node:a:rect" x="[\d.]+" y="([\d.]+)"', svg).group(1))
        label_y = float(re.search(r'data-key="node:a:label" x="[\d.]+" y="([\d.]+)"', svg).group(1))
        self.assertAlmostEqual(label_y, rect_y + 36 + 5)


class DocumentBlockTests(unittest.TestCase):
    def doc(self, blocks, **extra):
        d = {"title": "題", "lead": "[[TTL]]の説明", "glossary": [{"term": "TTL", "definition": "有効期間"}],
             "takeaways": ["要点の文。"], "sections": [{"id": "s", "title": "節", "blocks": blocks}]}
        d.update(extra)
        return d

    def test_all_block_types_render(self):
        blocks = [
            {"type": "p", "text": "**強調**と`code`と[リンク](https://example.com)"},
            {"type": "list", "items": ["一", "二"], "ordered": True},
            {"type": "callout", "tone": "warn", "text": "注意"},
            {"type": "stats", "items": [{"value": "8ms", "label": "応答"}, {"value": "94%", "label": "ヒット率"}]},
            {"type": "compare", "columns": [{"title": "A", "items": ["a"], "tone": "good"}, {"title": "B", "items": ["b"]}]},
            {"type": "code", "code": "print(1)", "language": "python"},
            {"type": "details", "summary": "詳しく", "paragraphs": ["中身"]},
            {"type": "diagram", "bundle": {"id": "seq", "title": "往復", "caption": "説明用", "mode": "steps", "panels": [{"spec": sequence_spec()}]}},
        ]
        p, html = render_doc(self.doc(blocks))
        self.assertEqual(p.returncode, 0, p.stderr)
        for needle in ['class="takeaways"', "<strong>強調</strong>", "<code>code</code>", 'href="https://example.com"', "<ol class=\"prose-list\">",
                       "callout-warn", 'class="stats"', "compare-good", "print(1)", "<details class=\"more\">",
                       'data-mode="steps"', 'class="term"', 'id="glossary"', "読了の目安", ".dg-step-bar"]:
            self.assertIn(needle, html)

    def test_unknown_glossary_term_is_rejected(self):
        p, _ = render_doc(self.doc([{"type": "p", "text": "[[未定義]]"}]))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("not in glossary", p.stderr)

    def test_inline_markup_escapes_html(self):
        out = inline("<b>x</b> **<i>y</i>** [a](javascript:alert(1))", {})
        self.assertNotIn("<b>", out)
        self.assertNotIn("<i>", out)
        self.assertNotIn('href="javascript', out)

    def test_bad_block_fields_are_rejected(self):
        p, _ = render_doc(self.doc([{"type": "stats", "items": [{"value": "1", "label": "a"}]}]))
        self.assertNotEqual(p.returncode, 0)
        p, _ = render_doc(self.doc([{"type": "p", "text": "x", "html": "<b>"}]))
        self.assertNotEqual(p.returncode, 0)

    def test_duplicate_diagram_id_is_rejected(self):
        bundle = {"id": "dup", "title": "往復", "caption": "説明用", "mode": "steps", "panels": [{"spec": sequence_spec()}]}
        p, _ = render_doc(self.doc([{"type": "diagram", "bundle": bundle}, {"type": "diagram", "bundle": bundle}]))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("duplicate", p.stderr)

    def test_showcase_renders(self):
        doc = json.loads((ROOT / "skills/html-explainer/assets/showcase.json").read_text(encoding="utf-8"))
        p, html = render_doc(doc)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(html.count("data-diagram data-state"), 3)


if __name__ == "__main__":
    unittest.main()
