import importlib.util
import pathlib
import re
import unittest

MODULE = pathlib.Path(__file__).parents[1] / "skills/html-explainer/scripts/network.py"
spec = importlib.util.spec_from_file_location("network", MODULE)
network = importlib.util.module_from_spec(spec)
spec.loader.exec_module(network)
render_network, validate_network = network.render_network, network.validate_network


def sample():
    return {
        "type": "network", "columns": 4, "rows": 2,
        "nodes": [
            {"id": "source", "label": "Source", "detail": "original", "column": 1, "row": 1, "tone": "blue"},
            {"id": "api", "label": "API", "detail": "requests", "column": 2, "row": 1, "tone": "teal"},
            {"id": "worker", "label": "Worker", "detail": "sandbox", "column": 3, "row": 1, "tone": "violet"},
            {"id": "home", "label": "Workspace", "detail": "files", "column": 4, "row": 1, "tone": "slate"},
        ],
        "boundaries": [{"id": "sandbox", "label": "Isolated runtime", "node_ids": ["worker", "home"], "tone": "violet"}],
        "variants": [
            {"label": "before", "active_nodes": ["source", "api"], "edges": [{"id": "copy", "from": "source", "to": "api", "label": "GET file", "kind": "file", "tone": "blue"}]},
            {"label": "after", "active_nodes": ["worker", "home"], "note": "A proposed route", "edges": [{"id": "copy", "from": "worker", "to": "api", "label": "GET with token", "kind": "request", "route": "above", "tone": "teal"}]},
        ],
    }


class NetworkTests(unittest.TestCase):
    def test_renders_accessible_variant_svgs_with_stable_keys(self):
        svgs = render_network(sample(), "example")
        self.assertEqual(len(svgs), 2)
        for svg in svgs:
            self.assertIn('role="img"', svg)
            self.assertRegex(svg, r'viewBox="0 0 960 [0-9]+"')
            self.assertIn('data-key="edge:copy:path"', svg)
            self.assertIn('data-key="node:worker"', svg)
            self.assertIn('data-obstacle=', svg)
            self.assertIn('<title', svg)
            self.assertIn('<desc', svg)
            keys = [line.split('data-key="', 1)[1].split('"', 1)[0] for line in svg.split() if 'data-key="' in line]
            self.assertEqual(len(keys), len(set(keys)))
            self.assertNotIn('M 72.0', svg)

    def test_rejects_grid_collisions(self):
        bad = sample(); bad["nodes"][1]["column"] = 1
        with self.assertRaisesRegex(ValueError, "already occupied"):
            validate_network(bad)

    def test_rejects_edge_to_unknown_node(self):
        bad = sample(); bad["variants"][0]["edges"][0]["to"] = "missing"
        with self.assertRaisesRegex(ValueError, "different nodes"):
            validate_network(bad)

    def test_rejects_long_labels_before_they_overflow(self):
        bad = sample(); bad["nodes"][0]["label"] = "x" * 49
        with self.assertRaisesRegex(ValueError, "too long"):
            validate_network(bad)

    def test_rejects_boundary_with_missing_member(self):
        bad = sample(); bad["boundaries"][0]["node_ids"] = ["missing"]
        with self.assertRaisesRegex(ValueError, "existing node ids"):
            validate_network(bad)

    def test_escapes_content_and_does_not_accept_raw_coordinates(self):
        bad = sample(); bad["nodes"][0]["label"] = "<script>"
        self.assertIn("&lt;script&gt;", render_network(bad)[0])
        bad["nodes"][0]["x"] = 12
        with self.assertRaisesRegex(ValueError, "unknown fields"):
            validate_network(bad)

    def test_rejects_unhashable_ids_and_tones_at_boundary(self):
        for field, value in (("active_nodes", [["source"]]),):
            bad = sample(); bad["variants"][0][field] = value
            with self.assertRaises(ValueError):
                validate_network(bad)
        bad = sample(); bad["variants"][0]["edges"][0]["from"] = ["source"]
        with self.assertRaises(ValueError):
            validate_network(bad)
        bad = sample(); bad["nodes"][0]["tone"] = ["blue"]
        with self.assertRaises(ValueError):
            validate_network(bad)

    def test_rejects_boundary_label_that_would_overflow(self):
        bad = sample(); bad["boundaries"][0]["label"] = "境界" * 25
        with self.assertRaisesRegex(ValueError, "too long"):
            validate_network(bad)

    def test_wraps_variant_note_and_keeps_nodes_inside_canvas(self):
        bad = sample(); bad["variants"][0]["note"] = "処理の説明" * 9
        svg = render_network(bad)[0]
        self.assertIn('<tspan x="120"', svg)
        self.assertIn("処理の説明", svg)
        for x, y, w, h in re.findall(r'data-obstacle="([0-9.-]+),([0-9.-]+),([0-9]+),([0-9]+)"', svg):
            self.assertGreaterEqual(float(x), 0)
            self.assertGreaterEqual(float(y), 0)
            self.assertLessEqual(float(x) + float(w), 960)
            self.assertLessEqual(float(y) + float(h), 400)

    def test_direct_edge_routes_around_foreign_node(self):
        bad = sample()
        bad["nodes"] = [
            {"id": "a", "label": "A", "column": 1, "row": 1},
            {"id": "b", "label": "B", "column": 2, "row": 1},
            {"id": "c", "label": "C", "column": 3, "row": 1},
        ]
        bad["boundaries"] = []
        bad["variants"] = [{"label": "v", "active_nodes": ["a", "c"], "edges": [
            {"id": "jump", "from": "a", "to": "c", "label": "進む", "kind": "request"}
        ]}]
        svg = render_network(bad)[0]
        self.assertNotIn('d="M 200.0 66.0 C 480.0 66.0, 480.0 66.0, 760.0 66.0"', svg)
        import xml.etree.ElementTree as ET
        tree=ET.fromstring(svg)
        edge=next(e for e in tree.iter('path')if e.get('data-key')=='edge:jump:path')
        vals=list(map(float,re.findall(r'-?\d+(?:\.\d+)?',edge.get('d'))))
        sx,sy,c1x,c1y,c2x,c2y,tx,ty=vals
        for i in range(41):
            t=i/40;u=1-t
            x=u**3*sx+3*u*u*t*c1x+3*u*t*t*c2x+t**3*tx
            y=u**3*sy+3*u*u*t*c1y+3*u*t*t*c2y+t**3*ty
            self.assertFalse(276<=x<=444 and 61<=y<=159, 'edge must avoid the middle node')


if __name__ == "__main__":
    unittest.main()
