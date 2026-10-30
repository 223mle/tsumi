"""Compose validated diagrams and synchronized scene controls without page-specific code."""
from __future__ import annotations
import argparse
import html
import json
import re
from pathlib import Path
from charts import render_chart
from network import render_network
from decisions import render_decision

ROOT = Path(__file__).resolve().parents[1]
TONES = {'blue','teal','violet','amber','rose','slate','red'}
STATUSES = {'measured':'実測','inferred':'推測','proposed':'提案','unknown':'未検証','illustrative':'説明用','code':'コード'}

def render_diagram(bundle):
    if not isinstance(bundle,dict) or set(bundle)-{'id','title','caption','status','legend','panels','labels','motion'}:
        raise ValueError('diagram: unknown fields or not an object')
    for key in ('id','title','caption'):
        if not isinstance(bundle.get(key),str) or not bundle[key].strip(): raise ValueError(f'diagram.{key}: text required')
    if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_-]*',bundle['id']): raise ValueError('diagram.id: invalid identifier')
    status=bundle.get('status','illustrative')
    if not isinstance(status,str) or status not in STATUSES: raise ValueError('diagram.status: unknown status')
    panels=bundle.get('panels')
    if not isinstance(panels,list) or not panels: raise ValueError('diagram.panels: non-empty array required')
    variants=[]
    for i,panel in enumerate(panels):
        if not isinstance(panel,dict) or set(panel)-{'title','spec'} or not isinstance(panel.get('spec'),dict): raise ValueError(f'panels[{i}]: title and spec required')
        if 'title' in panel and not isinstance(panel['title'],str): raise ValueError(f'panels[{i}].title: text required')
        spec=panel['spec']; renderer=render_network if spec.get('type')=='network' else render_decision if spec.get('type')=='decision' else render_chart
        variants.append(renderer(spec,f"{bundle['id']}-p{i}"))
    count=max(map(len,variants))
    if any(len(v) not in (1,count) for v in variants): raise ValueError('panels: scene counts must match or be one static scene')
    labels=bundle.get('labels',[v['label'] for v in panels[0]['spec'].get('variants',[])])
    if count>1 and (not isinstance(labels,list) or len(labels)!=count or not all(isinstance(x,str) and x.strip() for x in labels)): raise ValueError('labels: one label per scene required')
    if count==1: labels=labels or ['図']
    if not isinstance(bundle.get('legend',[]),list): raise ValueError('legend: array required')
    if 'motion' in bundle and not isinstance(bundle['motion'],bool): raise ValueError('motion: boolean required')
    legends=[]
    for item in bundle.get('legend',[]):
        if not isinstance(item,dict) or set(item)!={'label','tone'} or not isinstance(item['label'],str) or (not isinstance(item['tone'],str) or item['tone'] not in TONES): raise ValueError('legend: label and valid tone required')
        legends.append(f'<span><i class="dg-swatch dg-tone-{item["tone"]}"></i>{html.escape(item["label"])}</span>')
    controls=''
    if count>1:
        controls='<fieldset class="dg-switch"><legend>比較する状態</legend>'+''.join(f'<label><input type="radio" name="{bundle["id"]}-state" value="{i}" {"checked" if i==0 else ""}><span>{html.escape(label)}</span></label>' for i,label in enumerate(labels))+'</fieldset>'
    if bundle.get('motion',False): controls+='<button class="dg-play" type="button" aria-pressed="false">流れを再生</button>'
    output=[]
    for i,scenes in enumerate(variants):
        title=panels[i].get('title',''); heading=f'<h4 class="dg-panel-title">{html.escape(title)}</h4>' if title else ''
        static=''.join(f'<div class="dg-static-scene" data-state="{j}"><p class="dg-scene-name">{html.escape(labels[j] if len(scenes)>1 else "")}</p><div class="dg-scroll" tabindex="0" role="region" aria-label="{html.escape(title or bundle["title"])}">{svg}</div></div>' for j,svg in enumerate(scenes))
        output.append(f'<div class="dg-panel">{heading}<div class="dg-live dg-scroll" tabindex="0" role="region" aria-label="{html.escape(title or bundle["title"])}"></div><div class="dg-static">{static}</div></div>')
    return f'<figure class="dg-figure" id="{bundle["id"]}" data-diagram data-state="0"><div class="dg-toolbar">{controls}</div><h3 class="dg-title">{html.escape(bundle["title"])}</h3><div class="dg-legend">{"".join(legends)}</div>{"".join(output)}<figcaption><span class="status status-{status}">{STATUSES[status]}</span>{html.escape(bundle["caption"])}</figcaption></figure>'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--fragment',action='store_true');a=ap.parse_args()
    try:
        bundle=json.loads(a.input.read_text());result=render_diagram(bundle)
        if not a.fragment:
            css=(ROOT/'assets/style.css').read_text()+(ROOT/'assets/diagrams.css').read_text()
            js=(ROOT/'assets/behavior.js').read_text()+(ROOT/'assets/diagrams.js').read_text()
            result=f'<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(bundle["title"])}</title><style>{css}</style><main style="max-width:1100px;margin:auto;padding:24px"><h1>{html.escape(bundle["title"])}</h1>{result}</main><script>{js}</script></html>'
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(result)
    except (ValueError,OSError) as exc: ap.exit(2,f'{exc}\n')
if __name__=='__main__':main()
