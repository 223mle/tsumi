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
        self.assertIn('class="dg-msg dg-msg-call dg-tone-blue is-done" data-key="msg:m1">', second)
        self.assertRegex(second, r'class="dg-msg dg-msg-call dg-tone-blue is-current" data-key="msg:m2"')
        # A later message fades its line and number but keeps its label legible.
        self.assertRegex(second, r'data-key="msg:m3:line"[^>]* opacity="0.26"')
        self.assertRegex(second, r'data-key="msg:m3:num"[^>]* opacity="0.26"')
        self.assertNotRegex(second, r'data-key="msg:m3:label"[^>]* opacity=')
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


class NetworkStepTests(unittest.TestCase):
    def spec(self, **extra):
        spec = {"type": "network", "columns": 3, "rows": 2,
                "nodes": [{"id": "a", "label": "A", "column": 1, "row": 1}, {"id": "b", "label": "B", "column": 2, "row": 1},
                          {"id": "c", "label": "C", "column": 3, "row": 1}],
                "edges": [{"id": "e1", "from": "a", "to": "b", "label": "① 送る", "kind": "request", "step": 1, "text": "AがBへ送ります。"},
                          {"id": "e2", "from": "b", "to": "c", "label": "② 渡す", "kind": "file", "step": 2}]}
        spec.update(extra)
        return spec

    def test_numbered_edges_become_steps_with_all_edges_drawn(self):
        scenes = render_network(self.spec())
        self.assertEqual(len(scenes), 2)
        self.assertIn('class="dg-edge dg-tone-blue is-current" opacity="1"', scenes[0])
        self.assertRegex(scenes[0], r'data-key="edge:e2:path" data-flow="file" class="dg-edge dg-tone-blue is-future" opacity="0.16"')
        self.assertNotIn(" inactive", scenes[0])
        html = render_diagram({"id": "n", "title": "t", "caption": "c", "mode": "steps", "panels": [{"spec": self.spec()}]})
        self.assertIn("<b>1. 送る</b> AがBへ送ります。", html)

    def test_step_numbers_must_be_contiguous(self):
        bad = self.spec()
        bad["edges"][1]["step"] = 3
        with self.assertRaisesRegex(ValueError, "without gaps"):
            render_network(bad)
        with self.assertRaisesRegex(ValueError, "either"):
            render_network(self.spec(variants=[]))


class CompareNotesAndMarksTests(unittest.TestCase):
    def net(self):
        return {"type": "network", "columns": 3, "rows": 2,
                "nodes": [{"id": "a", "label": "A", "column": 1, "row": 1}, {"id": "b", "label": "フルサービス\nリゾルバー", "column": 2, "row": 1}],
                "variants": [{"label": "なし", "edges": [{"id": "e", "from": "a", "to": "b", "label": "送る", "kind": "request"}]},
                             {"label": "ヒット", "edges": [], "marks": [{"node": "b", "label": "ここでヒット", "tone": "teal"}]}]}

    def test_notes_follow_each_variant(self):
        html = render_diagram({"id": "n", "title": "t", "caption": "c", "notes": ["一つ目。", "二つ目。"], "panels": [{"spec": self.net()}]})
        self.assertIn('<template data-step-text="1"><b>ヒット</b> 二つ目。</template>', html)
        self.assertIn('dg-note-bar', html)
        with self.assertRaisesRegex(ValueError, "notes"):
            render_diagram({"id": "n", "title": "t", "caption": "c", "notes": ["一つだけ"], "panels": [{"spec": self.net()}]})

    def test_marks_and_explicit_line_breaks(self):
        svgs = render_network(self.net())
        self.assertNotIn("dg-mark", svgs[0])
        self.assertIn('class="dg-mark dg-tone-teal" data-key="mark:b"', svgs[1])
        self.assertIn(">フルサービス</tspan>", svgs[0])
        self.assertIn('data-ref="フルサービスリゾルバー"', svgs[0])
        bad = self.net()
        bad["variants"][1]["marks"] = [{"node": "zz", "label": "x"}]
        with self.assertRaisesRegex(ValueError, "marks"):
            render_network(bad)

    def test_wrap_prefers_word_boundaries(self):
        from jawrap import wrap
        self.assertEqual(wrap("IPアドレスを尋ねる", 14), ["IPアドレスを", "尋ねる"])
        self.assertEqual(wrap(".comの担当を紹介", 12), [".comの", "担当を紹介"])
        self.assertIsNone(wrap("とても長いラベル" * 4, 10))


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
        self.assertEqual(html.count("data-diagram data-state"), 4)



class ComposeLinkTests(unittest.TestCase):
    def test_href_allowlist_rejects_obfuscated_schemes(self):
        from compose import safe_href
        for bad in ["java\tscript:alert(1)", " JavaScript:alert(1)", "data:text/html,x", "vbscript:x", "//evil.example"]:
            with self.assertRaises(ValueError):
                safe_href(bad)
        for good in ["https://example.com/a", "#section", "notes.html", "mailto:a@example.com"]:
            self.assertEqual(safe_href(good), good)


class NetworkVocabularyTests(unittest.TestCase):
    def base(self):
        return {"type": "network", "columns": 3, "rows": 2,
                "nodes": [{"id": "a", "label": "A", "column": 1, "row": 1}, {"id": "b", "label": "B", "column": 2, "row": 1},
                          {"id": "c", "label": "C", "column": 3, "row": 1}]}

    def test_unlabelled_edges_hidden_nodes_and_conflicts(self):
        spec = self.base()
        spec["variants"] = [{"label": "前", "hidden_nodes": ["c"], "edges": [{"id": "ab", "from": "a", "to": "b", "kind": "file"}]},
                            {"label": "後", "edges": [{"id": "ab", "from": "a", "to": "b", "kind": "file"},
                                                     {"id": "bc", "from": "b", "to": "c", "kind": "conflict", "label": "衝突"}]}]
        before, after = render_network(spec)
        self.assertNotIn('data-key="edge:ab:label"', before)
        self.assertRegex(before, r'data-key="node:c" class="[^"]*" opacity="0" aria-hidden="true"')
        self.assertNotRegex(after, r'data-key="node:c" class="[^"]*" opacity="0"')
        self.assertIn("dg-edge-conflict", after)
        self.assertIn('data-key="edge:bc:cross"', after)
        self.assertNotIn('edge:bc:path" data-flow', after)

    def test_step_marks_attach_to_their_step(self):
        spec = self.base()
        spec["edges"] = [{"id": "ab", "from": "a", "to": "b", "kind": "file", "step": 1},
                         {"id": "bc", "from": "b", "to": "c", "kind": "file", "step": 2}]
        spec["marks"] = [{"node": "c", "label": "新しいID", "step": 2}]
        first, second = render_network(spec)
        self.assertNotIn("dg-mark", first)
        self.assertIn('data-key="mark:c"', second)
        html = render_diagram({"id": "n", "title": "t", "caption": "c", "mode": "steps", "panels": [{"spec": spec}]})
        self.assertIn("<b>1. 手順1</b>", html)
        bad = self.base()
        bad["variants"] = [{"label": "v", "edges": []}]
        bad["marks"] = [{"node": "a", "label": "x", "step": 1}]
        with self.assertRaisesRegex(ValueError, "numbered edges"):
            render_network(bad)

    def test_document_markup_reaches_figure_captions_and_steps(self):
        bundle = {"id": "seq", "title": "往復", "caption": "**説明用**の図", "mode": "steps",
                  "steps": [{"label": "一", "text": "[[TTL]]を記録"}, {"label": "二"}, {"label": "三"}, {"label": "四"}],
                  "panels": [{"spec": sequence_spec()}]}
        doc = {"title": "題", "lead": "導入", "glossary": [{"term": "TTL", "definition": "有効期間"}],
               "sections": [{"id": "s", "title": "節", "blocks": [{"type": "diagram", "bundle": bundle}]}]}
        p, html = render_doc(doc)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("<strong>説明用</strong>の図", html)
        self.assertIn('data-term="TTL"', html)
        bundle["caption"] = "[[未定義]]"
        p, _ = render_doc(doc)
        self.assertIn("not in glossary", p.stderr)


class SliderTests(unittest.TestCase):
    def timeline(self, n):
        return {"type": "timeline", "min": 0, "max": 10, "unit": "秒", "ticks": [0, 5, 10],
                "lanes": [{"id": "a", "label": "待ち", "tone": "blue"}],
                "variants": [{"label": f"{i}秒", "segments": [{"id": "w", "lane": "a", "start": 0, "duration": i + 1, "label": f"{i + 1}秒"}]} for i in range(n)]}

    def test_slider_renders_range_with_initial_state(self):
        html = render_diagram({"id": "s", "title": "t", "caption": "c", "mode": "slider", "slider": "入力時間", "initial": 2,
                               "panels": [{"spec": self.timeline(4)}]})
        self.assertIn('type="range" min="0" max="3" step="1" value="2"', html)
        self.assertIn('data-state="2" data-mode="slider"', html)
        self.assertIn(">2秒</output>", html)

    def test_slider_rules(self):
        base = {"id": "s", "title": "t", "caption": "c", "panels": [{"spec": self.timeline(4)}]}
        with self.assertRaisesRegex(ValueError, "slider"):
            render_diagram({**base, "mode": "slider"})
        with self.assertRaisesRegex(ValueError, "at least three"):
            render_diagram({**base, "mode": "slider", "slider": "x", "panels": [{"spec": self.timeline(2)}]})
        with self.assertRaisesRegex(ValueError, "initial"):
            render_diagram({**base, "initial": 1})


class EvalThreeTests(unittest.TestCase):
    def test_labelled_ticks(self):
        from charts import render_chart
        spec = {"type": "timeline", "min": 0, "max": 60, "unit": "日", "ticks": [0, {"value": 30, "label": "5/1"}, 60],
                "lanes": [{"id": "a", "label": "支払い", "tone": "blue"}],
                "variants": [{"label": "v", "segments": [{"id": "s", "lane": "a", "start": 0, "duration": 25, "label": "25日"}]}]}
        svg = render_chart(spec, "t")[0]
        self.assertIn(">5/1</text>", svg)
        self.assertIn(">0日</text>", svg)
        spec["ticks"][1] = {"value": 30}
        with self.assertRaisesRegex(ValueError, "label"):
            render_chart(spec, "t")

    def base(self):
        return {"type": "network", "columns": 3, "rows": 2,
                "nodes": [{"id": "a", "label": "A", "column": 1, "row": 1}, {"id": "b", "label": "B", "column": 2, "row": 1},
                          {"id": "c", "label": "C", "column": 3, "row": 1}]}

    def test_requested_route_is_kept_or_refused(self):
        spec = self.base()
        spec["variants"] = [{"label": "v", "edges": [{"id": "e", "from": "a", "to": "b", "label": "戻す", "kind": "file", "route": "above"},
                                                    {"id": "o", "from": "b", "to": "c", "label": "5万円以上なら", "kind": "request", "optional": True}]}]
        svg = render_network(spec)[0]
        d = re.search(r'data-key="edge:e:path"[^>]* d="([^"]+)"', svg).group(1)
        ys = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", d)[1::2]]
        self.assertLess(min(ys), ys[0])  # bends above its start
        self.assertIn("dg-edge-optional", svg)

    def test_text_out_strips_markup(self):
        doc = {"title": "題", "lead": "**強調**と[[TTL]]", "glossary": [{"term": "TTL", "definition": "有効期間"}],
               "sections": [{"id": "s", "title": "節", "blocks": [{"type": "p", "text": "`code`と[リンク](https://example.com)"}]}]}
        with TemporaryDirectory() as d:
            src, out, txt = Path(d) / "in.json", Path(d) / "out.html", Path(d) / "p.txt"
            src.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            p = subprocess.run([sys.executable, str(SCRIPTS / "render.py"), str(src), "--output", str(out), "--text-out", str(txt)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            text = txt.read_text(encoding="utf-8")
        self.assertIn("強調とTTL", text)
        self.assertIn("codeとリンク", text)
        self.assertNotIn("https://", text)


class NarrowLayoutTests(unittest.TestCase):
    def spec(self):
        return {"type": "timeline", "min": 0, "max": 91, "unit": "日", "ticks": [0, 30, 61, 91],
                "lanes": [{"id": "a", "label": "申請から振込まで", "tone": "blue"}],
                "variants": [{"label": "v", "segments": [{"id": "s", "lane": "a", "start": 30, "duration": 55, "label": "55日"}],
                              "markers": [{"id": "c1", "value": 30, "label": "4月末 締め"}, {"id": "p1", "value": 55, "label": "5/25 振込"},
                                          {"id": "c2", "value": 61, "label": "5月末 締め"}, {"id": "p2", "value": 85, "label": "6/25 振込"}]}]}

    def test_charts_get_a_phone_layout(self):
        html = render_diagram({"id": "t", "title": "t", "caption": "c", "panels": [{"spec": self.spec()}]})
        self.assertIn('class="dg-panel dg-wide"', html)
        self.assertIn('class="dg-panel dg-narrow"', html)
        self.assertIn('viewBox="0 0 420 ', html)

    def test_marker_labels_never_share_a_row_when_they_would_touch(self):
        from charts import _marker_layout, NARROW_WIDTH
        layout, rows = _marker_layout(self.spec()["variants"][0]["markers"], 0, 91, 90, NARROW_WIDTH - 106, NARROW_WIDTH)
        self.assertGreaterEqual(rows, 3)
        spans = {}
        for mid, (x, anchor, row) in layout.items():
            label = next(m["label"] for m in self.spec()["variants"][0]["markers"] if m["id"] == mid)
            w = sum(12 if ord(c) > 255 else 7 for c in label)
            spans.setdefault(row, []).append((x + 5, x + 5 + w) if anchor == "start" else (x - 5 - w, x - 5))
        for row, items in spans.items():
            items.sort()
            for (a, b), (c, d) in zip(items, items[1:]):
                self.assertLessEqual(b + 8, c)


class PhoneNetworkTests(unittest.TestCase):
    def test_two_row_network_gets_a_vertical_phone_layout(self):
        spec = {"type": "network", "columns": 4, "rows": 2,
                "nodes": [{"id": "a", "label": "A", "column": 1, "row": 1}, {"id": "b", "label": "B", "column": 2, "row": 1},
                          {"id": "c", "label": "C", "column": 3, "row": 1}, {"id": "d", "label": "D", "column": 3, "row": 2}],
                "variants": [{"label": "v", "edges": [{"id": "ab", "from": "a", "to": "b", "label": "送る", "kind": "request"},
                                                     {"id": "bd", "from": "b", "to": "d", "label": "読む", "kind": "file"}]}]}
        svg = render_network(spec, "n", narrow=True)[0]
        self.assertIn('viewBox="0 0 420 ', svg)
        ya = float(re.search(r'data-key="node:a:rect" x="[\d.]+" y="([\d.]+)"', svg).group(1))
        yb = float(re.search(r'data-key="node:b:rect" x="[\d.]+" y="([\d.]+)"', svg).group(1))
        self.assertLess(ya, yb)  # left-to-right becomes top-to-bottom
        html = render_diagram({"id": "n", "title": "t", "caption": "c", "panels": [{"spec": spec}]})
        self.assertIn("dg-panel dg-narrow", html)

    def test_three_row_network_keeps_only_the_wide_layout(self):
        spec = {"type": "network", "columns": 3, "rows": 3,
                "nodes": [{"id": "a", "label": "A", "column": 1, "row": 1}, {"id": "b", "label": "B", "column": 1, "row": 2},
                          {"id": "c", "label": "C", "column": 1, "row": 3}],
                "variants": [{"label": "v", "edges": []}]}
        with self.assertRaises(ValueError):
            render_network(spec, "n", narrow=True)
        html = render_diagram({"id": "n", "title": "t", "caption": "c", "panels": [{"spec": spec}]})
        self.assertNotIn("dg-narrow", html)


class PhoneSequenceTests(unittest.TestCase):
    def test_up_to_four_actors_get_a_phone_layout(self):
        svg = render_sequence(sequence_spec(), "s", narrow=True)[0]
        self.assertIn('viewBox="0 0 420 ', svg)
        self.assertNotIn("--min-width", svg)
        html = render_diagram({"id": "s", "title": "t", "caption": "c", "mode": "steps", "panels": [{"spec": sequence_spec()}]})
        self.assertIn("dg-panel dg-narrow", html)

    def test_five_actors_keep_scrolling(self):
        spec = sequence_spec(actors=[{"id": x, "label": x.upper()} for x in "abcde"])
        with self.assertRaises(ValueError):
            render_sequence(spec, "s", narrow=True)


class EvalFourTests(unittest.TestCase):
    def test_hidden_node_is_not_also_faded_by_css(self):
        spec = {"type": "network", "columns": 3, "rows": 2,
                "nodes": [{"id": "a", "label": "A", "column": 1, "row": 1}, {"id": "b", "label": "B", "column": 2, "row": 1},
                          {"id": "c", "label": "C", "column": 3, "row": 1}],
                "variants": [{"label": "v", "active_nodes": ["a"], "hidden_nodes": ["c"], "edges": []}]}
        svg = render_network(spec)[0]
        self.assertRegex(svg, r'data-key="node:c" class="dg-node dg-tone-slate" opacity="0" aria-hidden="true"')
        self.assertRegex(svg, r'data-key="node:b" class="dg-node dg-tone-slate inactive" data-ref')
        self.assertRegex(svg, r'data-key="node:b:rect"[^>]* opacity="0.35"')

    def test_bundle_sources_and_shared_status_words(self):
        bundle = {"id": "m", "title": "t", "caption": "c", "status": "measured", "source_ids": ["log"],
                  "panels": [{"spec": sequence_spec()}], "mode": "steps"}
        html = render_diagram(bundle, source_titles={"log": "監視ログ"})
        self.assertIn('href="#log">監視ログ</a>', html)
        self.assertIn(">計測値</span>", html)
        doc = {"title": "題", "lead": "導入", "sections": [{"id": "s", "title": "節", "blocks": [{"type": "diagram", "bundle": {**bundle, "source_ids": []}}]}]}
        p, _ = render_doc(doc)
        self.assertIn("requires source_ids", p.stderr)

    def test_short_amount_replaces_a_label_with_no_room(self):
        from charts import render_chart
        spec = {"type": "timeline", "min": 0, "max": 30, "unit": "分", "ticks": [0, 10, 20, 30],
                "lanes": [{"id": "a", "label": "対応", "tone": "blue"}],
                "variants": [{"label": "v", "segments": [
                    {"id": "s1", "lane": "a", "start": 5, "duration": 6, "label": "気づくまで6分"},
                    {"id": "s2", "lane": "a", "start": 11, "duration": 7, "label": "特定まで7分"},
                    {"id": "s3", "lane": "a", "start": 18, "duration": 6, "label": "戻すまで6分"}]}]}
        svg = render_chart(spec, "t", narrow=True)[0]
        self.assertIn(">6分</text>", svg)
        self.assertIn(">7分</text>", svg)

    def test_round_axis_ticks(self):
        from render import ticks
        self.assertEqual(ticks(8), [0.0, 2.0, 4.0, 6.0, 8.0])
        self.assertEqual(ticks(120)[1], 20.0)


if __name__ == "__main__":
    unittest.main()
