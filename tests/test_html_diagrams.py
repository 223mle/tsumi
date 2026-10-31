import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'skills/html-explainer/scripts'))
from diagrams import render_diagram
from compose import compose
from charts import render_chart

class DiagramTests(unittest.TestCase):
    def example(self):return json.loads((ROOT/'skills/html-explainer/assets/animated-example.json').read_text())
    def test_bundle_rejects_mismatched_variants(self):
        bundle=self.example();bundle['panels'][1]['spec']['variants'].append(copy.deepcopy(bundle['panels'][1]['spec']['variants'][0]))
        with self.assertRaisesRegex(ValueError,'counts'):render_diagram(bundle)
    def test_unknown_duration_is_not_rendered_as_a_quantitative_bar(self):
        spec=self.example()['panels'][0]['spec'];seg=spec['variants'][1]['segments'][1];seg.pop('duration');seg.update(unknown=True,label='分類時間は未計測')
        result=render_chart(spec,'unknown')[1]
        self.assertIn('分類時間は未計測',result)
        self.assertNotRegex(result,r'<rect[^>]+data-key="segment-r"')
        seg['duration']=2
        with self.assertRaisesRegex(ValueError,'numeric duration'):render_chart(spec)
    def test_composer_preserves_rich_prose_and_removes_source_runtime(self):
        source='<main><h1>説明</h1><p>条件は<strong>未確認</strong>です。</p><h2 id="a">章</h2><figure>old graphic</figure><script>bad()</script></main>'
        result=compose(source,{'figures':[self.example()]})
        self.assertIn('<strong>未確認</strong>',result)
        self.assertNotIn('bad()',result);self.assertNotIn('old graphic',result)
        self.assertIn('data-diagram',result)
    def test_figure_sources_survive_replacement(self):
        source='<main><figure><a href="https://example.com/source">資料</a></figure></main>'
        result=compose(source,{"figures":[self.example()]})
        self.assertIn('href="https://example.com/source"',result)
    def test_composer_never_silently_drops_unmapped_figures(self):
        with self.assertRaisesRegex(ValueError,'every figure'):compose('<main><figure>A</figure><figure>B</figure></main>',{'figures':[self.example()]})
    def test_source_tooltips_are_readable_without_javascript(self):
        source='<main><h1>説明</h1><table><tr><td data-tip="条件付きで使う">△</td></tr></table></main>'
        result=compose(source,{'figures':[]})
        self.assertIn('<li>条件付きで使う</li>',result)
    def test_wrapper_rejects_bad_optional_types(self):
        for field,value in [('legend',None),('motion',[])]:
            d=self.example();d[field]=value
            with self.assertRaises(ValueError):render_diagram(d)
if __name__=='__main__':unittest.main()
