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


class FuzzTests(unittest.TestCase):
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
                series.append({"id": f"s{k}", "label": rnd.choice(["スタンダード", "案A", "エンタープライズ年額"]), "points": [[x, rnd.uniform(0, ymax)] for x in xs]})
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
