import importlib.util
import pathlib
import unittest

_path = pathlib.Path(__file__).parents[1] / "skills/html-explainer/scripts/charts.py"
_spec = importlib.util.spec_from_file_location("charts", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
render_chart, validate_chart = _module.render_chart, _module.validate_chart


def timeline():
    return {"type": "timeline", "min": -2, "max": 10, "unit": "秒", "ticks": [-2, 0, 5, 10],
            "lanes": [{"id": "work", "label": "準備", "tone": "teal"}],
            "variants": [{"label": "今", "segments": [{"id": "send", "lane": "work", "start": 0, "duration": 4, "label": "4秒"}]},
                         {"label": "改善案", "segments": [{"id": "send", "lane": "work", "start": -1, "duration": 2, "label": "2秒"}]}]}


class ChartTests(unittest.TestCase):
    def test_timeline_variants_have_stable_keys_and_accessibility(self):
        variants = render_chart(timeline(), "demo")
        self.assertEqual(len(variants), 2)
        for svg in variants:
            self.assertIn('role="img"', svg)
            self.assertIn('data-key="segment-send"', svg)
            self.assertIn('data-label="true"', svg)
            self.assertIn('viewBox="0 0 960', svg)

    def test_duration_controls_width_independent_of_start_and_groups_are_named(self):
        spec = timeline(); spec["groups"] = [{"label": "受信前に実行可能", "lane_ids": ["work"], "summary": "入力中に進める", "tone": "teal"}]
        svg = render_chart(spec, "grouped")[0]
        self.assertIn('class="group-band group-teal"', svg)
        self.assertIn("group-label-0", svg)
        spec["variants"][1]["segments"][0]["duration"] = 4
        import xml.etree.ElementTree as ET
        pictures=[ET.fromstring(v)for v in render_chart(spec,"grouped")]
        widths=[float(next(e for e in tree.iter()if e.get('data-key')=='segment-send').get('width'))for tree in pictures]
        self.assertGreater(widths[0],0)
        self.assertAlmostEqual(widths[0],widths[1])

    def test_rejects_unknown_lane_and_out_of_domain_segment(self):
        bad = timeline(); bad["variants"][0]["segments"][0]["lane"] = "missing"
        with self.assertRaises(ValueError): validate_chart(bad)
        bad = timeline(); bad["variants"][0]["segments"][0]["start"] = 9
        with self.assertRaises(ValueError): validate_chart(bad)

    def test_threshold_marks_exceeding_rows_on_shared_axis(self):
        spec = {"type": "threshold", "min": 0, "max": 100, "unit": "件", "ticks": [0, 50, 100],
                "rows": [{"id": "now", "label": "現在", "value": 40, "value_label": "40件", "tone": "blue"}],
                "thresholds": [{"id": "limit", "value": 60, "label": "上限", "tone": "red"}]}
        svg = render_chart(spec, "capacity")[0]
        self.assertIn('data-key="row-now"', svg)
        self.assertIn('data-key="threshold-limit"', svg)
        self.assertIn("40件", svg)

    def test_rejects_duplicate_ids_and_log_nonpositive_domain(self):
        bad = timeline(); bad["variants"][0]["segments"].append({"id": "send", "lane": "work", "start": 5, "duration": 1})
        with self.assertRaises(ValueError): validate_chart(bad)
        bad = {"type": "threshold", "min": 0, "max": 10, "scale": "log", "unit": "秒", "ticks": [0, 10], "rows": [], "thresholds": []}
        with self.assertRaises(ValueError): validate_chart(bad)


if __name__ == "__main__":
    unittest.main()
