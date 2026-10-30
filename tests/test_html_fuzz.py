"""Random small diagrams must render or be refused with a ValueError, never crash.

A refusal names the field to change; any other exception is a traceback for
the author. The seeds are fixed so a failure reproduces.
"""
import random
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "skills/html-explainer/scripts"))

from charts import _text_width, render_chart  # noqa: E402
from linechart import render_line  # noqa: E402
from network import render_network  # noqa: E402
from sequence import render_sequence  # noqa: E402

LABELS = ["送る", "返す", "問い合わせる", "結果を返す", "書き込む", "フルサービス\nリゾルバー", "HTTPS POST", ""]


def inside(svg):
    """Every node and actor box lies inside the viewBox."""
    w, h = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups())
    for x, y, bw, bh in re.findall(r'<rect data-key="(?:node|actor):[^"]+" x="(-?[\d.]+)" y="(-?[\d.]+)" width="([\d.]+)" height="([\d.]+)"', svg):
        if float(x) < -0.5 or float(y) < -0.5 or float(x) + float(bw) > w + 0.5 or float(y) + float(bh) > h + 0.5:
            return False
    return True


TICK_RE = re.compile(r'<text x="(-?[\d.]+)" y="[\d.]+" class="axis-label" text-anchor="(\w+)" data-label="true" data-key="x?tick-label-([^"]+)">([^<]*)</text>')


def tick_spans(svg):
    """(left, right, value) of every drawn x tick label, as anchored."""
    out = []
    for x, anchor, value, text in TICK_RE.findall(svg):
        x, w = float(x), _text_width(text)
        left = x - w / 2 if anchor == "middle" else x - w if anchor == "end" else x
        out.append((left, left + w, value))
    return out


class FuzzTests(unittest.TestCase):
    def assert_ticks_readable(self, svg, ticks_have_zero, spec):
        w = float(re.search(r'viewBox="0 0 ([\d.]+) ', svg).group(1))
        spans = sorted(tick_spans(svg))
        for (a, b, _), (c, d, _) in zip(spans, spans[1:]):
            self.assertLessEqual(b, c + 0.5, (spans, spec))
        self.assertTrue(all(a >= -0.5 and b <= w + 0.5 for a, b, _ in spans), (spans, spec))
        if ticks_have_zero:
            self.assertIn("0", [v for _, _, v in spans], spec)

    def test_tick_labels_never_touch_and_keep_zero(self):
        rnd = random.Random(11)
        for _ in range(200):
            lo = rnd.choice([0, -4, -60])
            hi = lo + rnd.choice([8, 12, 100, 240])
            n = rnd.randint(3, 13)
            values = sorted({round(lo + (hi - lo) * i / (n - 1)) for i in range(n)} | ({0} if lo < 0 else set()))
            ticks = [{"value": v, "label": rnd.choice(["審査", "最終締め日の翌営業日", f"{v}日"])} if rnd.random() < 0.2 else v for v in values]
            markers = [{"id": f"m{k}", "value": rnd.choice(values), "label": "目印"} for k in range(rnd.randint(0, 2))]
            spec = {"type": "timeline", "min": lo, "max": hi, "unit": "秒", "ticks": ticks,
                    "lanes": [{"id": "a", "label": "処理"}],
                    "variants": [{"label": "v", "segments": [{"id": "s", "lane": "a", "start": lo, "duration": (hi - lo) / 2, "label": "半分"}], "markers": markers}]}
            line = {"type": "line", "x": {"min": lo, "max": hi, "unit": "人", "ticks": ticks},
                    "y": {"min": 0, "max": 10, "unit": "", "ticks": [0, 10], "label": "月額費用（税込・円）"},
                    "series": [{"id": "s", "label": "エンタープライズ年額", "points": [[lo, 5], [hi, 5]]}],
                    "markers": [{"id": m["id"], "x": m["value"], "label": "今"} for m in markers]}
            for narrow in (False, True):
                for render, sp in ((render_chart, spec), (render_line, line)):
                    try:
                        svg = render(sp, "t", narrow=narrow)[0]
                    except ValueError:
                        continue
                    self.assert_ticks_readable(svg, 0 in values, sp)

    def test_unknown_label_clears_its_question_mark(self):
        for start, before in [(s, b) for s in (2, 5, 8, 9) for b in (True, False)]:
            segments = [{"id": "s", "lane": "a", "start": 0, "duration": start, "label": "コピー"}] if before else []
            segments.append({"id": "u", "lane": "a", "start": start, "unknown": True, "label": "次の移行日は未定"})
            spec = {"type": "timeline", "min": 0, "max": 10, "unit": "日", "ticks": [0, 5, 10], "lanes": [{"id": "a", "label": "作業"}],
                    "variants": [{"label": "v", "segments": segments}]}
            for narrow in (False, True):
                try:
                    svg = render_chart(spec, "t", narrow=narrow)[0]
                except ValueError:
                    self.assertTrue(narrow, spec)  # only the phone layout may give up; the page then scrolls the wide one
                    continue
                q = float(re.search(r'<text x="([\d.]+)"[^>]*data-key="unknown-marker-u"', svg).group(1))
                label = re.search(r'<text x="([\d.]+)"[^>]*text-anchor="(\w+)"[^>]*data-key="segment-label-u">([^<]*)<', svg)
                if label:
                    x, anchor, text = float(label.group(1)), label.group(2), label.group(3)
                    left = x if anchor == "start" else x - _text_width(text)
                    self.assertTrue(left >= q + 6 or left + _text_width(text) <= q - 6, (start, narrow, svg))

    def test_timeline_row_labels_never_overlap(self):
        rnd = random.Random(5)
        text_re = re.compile(r'<text x="(-?[\d.]+)" y="([\d.]+)" class="(bar-label|external-label|unknown-duration)" text-anchor="(\w+)"[^>]*>([^<]+)</text>')
        wrapped_re = re.compile(r'<text transform="translate\((-?[\d.]+),([\d.]+)\)" class="external-label" text-anchor="(\w+)"[^>]*>(.*?)</text>')
        for _ in range(300):
            segs, t = [], 0
            for k in range(rnd.randint(1, 4)):
                d = rnd.choice([0.5, 1, 1.4, 2, 5, 20])
                segs.append({"id": f"s{k}", "lane": "a", "start": t, "duration": d, "label": rnd.choice(["コピー", "照合", "読み書き", "読み取り専用", "待ち6分"])})
                t += d + rnd.choice([0, 1])
            if rnd.random() < 0.5:
                segs.append({"id": "u", "lane": "a", "start": t, "unknown": True, "label": rnd.choice(["未定", "次の移行日は未定"])})
            hi = t + rnd.choice([1, 4, 10])
            spec = {"type": "timeline", "min": 0, "max": hi, "unit": "日", "ticks": [0, hi], "lanes": [{"id": "a", "label": "作業"}],
                    "variants": [{"label": "v", "segments": segs, "markers": [{"id": "m", "value": round(rnd.uniform(0, hi), 1), "label": "今"}] if rnd.random() < 0.5 else []}]}
            for narrow in (False, True):
                try:
                    svg = render_chart(spec, "t", narrow=narrow)[0]
                except ValueError:
                    continue
                spans = []
                for x, y, _, anchor, text in text_re.findall(svg):
                    x, w = float(x), _text_width(text)
                    left = x - w / 2 if anchor == "middle" else x - w if anchor == "end" else x
                    spans.append((round(float(y) / 5), left, left + w, text))  # the ? sits 1px lower than labels on its row
                for x, y, anchor, inner in wrapped_re.findall(svg):  # labels moved to the column right of the plot
                    for i, line in enumerate(re.findall(r">([^<]*)</tspan>", inner)):
                        w = _text_width(line)
                        left = float(x) if anchor == "start" else float(x) - w
                        spans.append((round((float(y) + 1 + 15 * i) / 5), left, left + w, line))
                spans.sort()
                for (y1, a1, b1, t1), (y2, a2, b2, t2) in zip(spans, spans[1:]):
                    if y1 == y2:
                        # 2px: a full-width ？ has wide side bearings, so its box may graze a neighbour without the ink touching.
                        self.assertLessEqual(b1, a2 + 2, (t1, t2, narrow, spec))

    def test_series_with_the_same_label_are_refused(self):
        spec = {"type": "line", "x": {"min": 0, "max": 10, "unit": "人", "ticks": [0, 10]}, "y": {"min": 0, "max": 10, "unit": "円", "ticks": [0, 10]},
                "series": [{"id": "a", "label": "案A", "points": [[0, 1], [10, 9]]}, {"id": "b", "label": "案A", "points": [[0, 9], [10, 1]]}]}
        with self.assertRaisesRegex(ValueError, "same label"):
            render_line(spec, "l")

    def test_a_path_colour_missing_from_the_legend_is_refused(self):
        sys.path.insert(0, str(Path(__file__).parents[1] / "skills/html-explainer/scripts"))
        from diagrams import render_diagram
        net = {"type": "network", "columns": 3, "rows": 2, "nodes": [{"id": "a", "label": "API", "column": 1, "row": 1}, {"id": "b", "label": "DB", "column": 3, "row": 1}],
               "variants": [{"label": "v", "edges": [{"id": "e", "from": "a", "to": "b", "kind": "file", "tone": "violet", "label": "読む"}]}]}
        bundle = {"id": "f", "title": "経路", "caption": "説明用。", "status": "illustrative", "legend": [{"label": "要求", "tone": "blue"}], "panels": [{"spec": net}]}
        with self.assertRaisesRegex(ValueError, "legend does not name"):
            render_diagram(bundle)
        bundle["legend"].append({"label": "読み出し", "tone": "violet"})
        with self.assertRaisesRegex(ValueError, "nothing in the figure is drawn in \\['blue'\\]"):
            render_diagram(bundle)  # the blue entry names nothing on the page
        bundle["legend"] = [{"label": "読み出し", "tone": "violet"}]
        render_diagram(bundle)

    def test_a_removed_step_keeps_a_labelled_outline(self):
        spec = {"type": "timeline", "min": 0, "max": 130, "unit": "ms", "ticks": [0, 120], "baseline": True,
                "lanes": [{"id": "app", "label": "API"}, {"id": "sql", "label": "DB"}],
                "variants": [{"label": "導入前", "segments": [{"id": "q", "lane": "sql", "start": 5, "duration": 110, "label": "110ms"}]},
                             {"label": "ヒット", "segments": [{"id": "p", "lane": "app", "start": 0, "duration": 2, "label": "2ms"}]}]}
        before, after = render_chart(spec, "t")
        self.assertNotIn("ghost-label", before)
        self.assertIn(">導入前 110ms<", after)

    def test_a_span_clears_a_self_call_beside_it(self):
        spec = {"type": "sequence", "actors": [{"id": "w", "label": "書き手"}, {"id": "r", "label": "実行者"}, {"id": "l", "label": "台帳"}, {"id": "n", "label": "次の実行者"}],
                "messages": [{"id": "m1", "from": "w", "to": "r", "label": "起動契約を渡す"}, {"id": "m2", "from": "r", "to": "r", "label": "シナリオを実行"},
                             {"id": "m3", "from": "r", "to": "w", "label": "成果物と申告", "kind": "reply"}],
                "spans": [{"from": "m1", "to": "m3", "label": "白紙で実行"}]}
        for narrow in (False, True):
            svg = render_sequence(spec, "s", narrow=narrow)[0]
            span_x = float(re.search(r'data-key="span:0:label"[^>]*x="([\d.]+)"', svg).group(1))
            label = re.search(r'data-key="msg:m2:label" x="([\d.]+)"[^>]*>(.*?)</text>', svg)
            right = float(label.group(1)) + max(_text_width(t) for t in re.findall(r">([^<]+)</tspan>", label.group(2)))
            self.assertGreater(span_x, right, narrow)

    def test_a_span_with_no_room_on_the_right_moves_left(self):
        spec = {"type": "sequence", "actors": [{"id": "b", "label": "ブラウザー"}, {"id": "w", "label": "Webアプリ"}, {"id": "a", "label": "認可サーバー"}, {"id": "api", "label": "APIサーバー"}],
                "messages": [{"id": "m1", "from": "b", "to": "w", "label": "ログイン"}, {"id": "m2", "from": "w", "to": "a", "label": "コードと検証値"},
                             {"id": "m3", "from": "a", "to": "a", "label": "チャレンジと照合"}, {"id": "m4", "from": "a", "to": "w", "label": "トークン", "kind": "reply"}],
                "spans": [{"from": "m2", "to": "m4", "label": "直接の通信"}]}
        svg = render_sequence(spec, "s", narrow=True)[0]
        self.assertRegex(svg, r'data-key="span:0:label"[^>]*text-anchor="end"')
        self.assertTrue(inside(svg))

    def test_a_long_unit_moves_to_the_axis_name_on_phones(self):
        spec = {"type": "line", "x": {"min": 0, "max": 28, "unit": "か月", "ticks": [0, 14, 28]},
                "y": {"min": 0, "max": 1200, "unit": "接続", "ticks": [0, 600, 1200], "label": "ピーク時の接続数"},
                "series": [{"id": "p", "label": "見込み", "points": [[0, 80], [28, 1150]]}]}
        phone, wide = render_line(spec, "l", narrow=True)[0], render_line(spec, "l")[0]
        self.assertIn(">1200<", phone)
        self.assertIn("ピーク時の接続数（接続）", phone)
        self.assertIn(">1200接続<", wide)

    def test_one_line_needs_no_phone_key(self):
        spec = {"type": "line", "x": {"min": 0, "max": 4, "unit": "回", "ticks": [0, 4]}, "y": {"min": 0, "max": 6, "unit": "件", "ticks": [0, 6], "label": "新しい不明瞭点"},
                "series": [{"id": "a", "label": "新しい不明瞭点", "points": [[0, 5], [4, 0]]}]}
        self.assertNotIn("series-key", render_line(spec, "l", narrow=True)[0])
        self.assertIn("series-label-a", render_line(spec, "l")[0])

    def test_an_empty_lane_can_say_so(self):
        spec = {"type": "timeline", "min": -6, "max": 12, "unit": "分", "ticks": [-6, 0, 6, 12], "baseline": True,
                "lanes": [{"id": "scale", "label": "台数を増やす"}, {"id": "slow", "label": "応答の遅れ"}],
                "variants": [{"label": "現状", "segments": [{"id": "boot", "lane": "scale", "start": 3, "duration": 4, "label": "起動4分"},
                                                          {"id": "late", "lane": "slow", "start": 0, "duration": 9, "label": "9分"}]},
                             {"label": "A", "segments": [{"id": "boot", "lane": "scale", "start": -4, "duration": 4, "label": "起動4分"}], "empty": {"slow": "なし（計算）"}}]}
        for narrow in (False, True):
            svg = render_chart(spec, "t", narrow=narrow)[1]
            empty = re.search(r'<text x="([\d.]+)"[^>]*data-key="empty-label-slow">([^<]+)<', svg)
            ghost = re.search(r'<text x="([\d.]+)"[^>]*data-key="ghost-label-late">([^<]+)<', svg)
            self.assertTrue(empty and ghost)
            self.assertLessEqual(float(empty.group(1)) + _text_width(empty.group(2)), float(ghost.group(1)) - _text_width(ghost.group(2)) / 2)
        spec["variants"][1]["empty"] = {"scale": "なし"}
        with self.assertRaisesRegex(ValueError, "no segment"):
            render_chart(spec, "t")

    def test_labels_keep_a_word_and_its_kana_ending_together(self):
        sys.path.insert(0, str(Path(__file__).parents[1] / "skills/html-explainer/scripts"))
        from jawrap import wrap
        self.assertEqual(wrap("支払い済みに更新", 11, 3), ["支払い", "済みに更新"])
        self.assertEqual(wrap("もう一度更新", 11, 3), ["もう", "一度更新"])
        for text in ("もう一度更新", "結果を返す", "問い合わせる", "支払い済みに更新"):
            for width in (6, 8, 10):
                lines = wrap(text, width, 3)
                if lines and len(lines) > 1:
                    self.assertTrue(all(len(x) > 1 for x in lines), (text, width, lines))

    def test_networks(self):
        rnd = random.Random(20261030)
        for _ in range(250):
            cols, rows = rnd.choice([3, 4]), rnd.choice([2, 3])
            cells = rnd.sample([(c, r) for c in range(1, cols + 1) for r in range(1, rows + 1)], rnd.randint(2, 5))
            nodes = [{"id": f"n{i}", "label": rnd.choice(LABELS[:6]) or "ノード", "column": c, "row": r} for i, (c, r) in enumerate(cells)]
            edges = []
            for k in range(rnd.randint(1, 4)):
                a, b = rnd.sample(range(len(nodes)), 2)
                e = {"id": f"e{k}", "from": f"n{a}", "to": f"n{b}", "kind": rnd.choice(["file", "request", "conflict"])}
                if rnd.random() < 0.8:
                    e["label"] = rnd.choice(LABELS[:-1])
                edges.append(e)
            variant = {"label": "v", "edges": edges}
            if rnd.random() < 0.3:
                variant["marks"] = [{"node": "n0", "label": "ここ"}]
            spec = {"type": "network", "columns": cols, "rows": rows, "nodes": nodes, "variants": [variant]}
            for narrow in (False, True):
                try:
                    svgs = render_network(spec, "f", narrow=narrow)
                except ValueError:
                    continue
                self.assertTrue(all(inside(s) for s in svgs), spec)

    def test_sequences(self):
        rnd = random.Random(7)
        for _ in range(150):
            actors = [{"id": f"a{i}", "label": rnd.choice(["ブラウザー", "API", "認証サーバー", "DB"])} for i in range(rnd.randint(2, 6))]
            msgs = [{"id": f"m{k}", "from": rnd.choice(actors)["id"], "to": rnd.choice(actors)["id"], "label": rnd.choice(LABELS[:-1]),
                     "kind": rnd.choice(["call", "reply", "async"])} for k in range(rnd.randint(1, 8))]
            spec = {"type": "sequence", "actors": actors, "messages": msgs}
            if len(msgs) > 1 and rnd.random() < 0.4:
                spec["spans"] = [{"from": msgs[0]["id"], "to": msgs[-1]["id"], "label": "約1秒"}]
            for narrow in (False, True):
                try:
                    svgs = render_sequence(spec, "s", narrow=narrow)
                except ValueError:
                    continue
                self.assertTrue(all(inside(s) for s in svgs), spec)

    def test_line_charts(self):
        rnd = random.Random(3)
        for _ in range(150):
            ymax = rnd.choice([10, 1000, 2_000_000])
            series = []
            for k in range(rnd.randint(1, 4)):
                xs = sorted(rnd.sample(range(0, 101, 10), rnd.randint(2, 6)))
                series.append({"id": f"s{k}", "label": ["スタンダード", "案A", "エンタープライズ年額", "案B"][k], "points": [[x, rnd.uniform(0, ymax)] for x in xs]})
            spec = {"type": "line", "x": {"min": 0, "max": 100, "unit": "人", "ticks": [0, 50, 100]},
                    "y": {"min": 0, "max": ymax, "unit": "円", "ticks": [0, ymax]}, "series": series,
                    "points": [{"id": "p", "x": rnd.uniform(0, 100), "y": rnd.uniform(0, ymax), "label": "ここで逆転"}],
                    "markers": [{"id": "m", "x": rnd.uniform(0, 100), "label": "今"}],
                    "bands": [{"id": "b", "from": 60, "to": 80, "label": "見込み"}]}
            for narrow in (False, True):
                try:
                    render_line(spec, "l", narrow=narrow)
                except ValueError:
                    pass


if __name__ == "__main__":
    unittest.main()
