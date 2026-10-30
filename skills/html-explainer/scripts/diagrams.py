"""Compose validated diagrams and synchronized scene controls without page-specific code."""
from __future__ import annotations
import argparse
import html
import json
import re
from pathlib import Path
from charts import render_chart
from network import render_network, network_steps
from decisions import render_decision
from sequence import render_sequence, sequence_steps

ROOT = Path(__file__).resolve().parents[1]
TONES = {'blue','teal','violet','amber','rose','slate','red'}
STATUSES = {'measured':'実測','inferred':'推測','proposed':'提案','unknown':'未検証','illustrative':'説明用','code':'コード'}

RENDERERS={'network':render_network,'decision':render_decision,'sequence':render_sequence}

def _steps(bundle,panels,count):
    steps=bundle.get('steps')
    if steps is None:
        seq=[p['spec'] for p in panels if p['spec'].get('type')=='sequence']
        net=[p['spec'] for p in panels if p['spec'].get('type')=='network' and 'edges' in p['spec']]
        if seq: steps=sequence_steps(seq[0])
        elif net: steps=network_steps(net[0])
        else: raise ValueError('steps: required unless a panel is a sequence or a network with numbered edges')
    if not isinstance(steps,list) or len(steps)!=count or count<2: raise ValueError('steps: one step per scene (at least two) required')
    out=[]
    for i,st in enumerate(steps):
        if not isinstance(st,dict) or set(st)-{'label','text'} or not isinstance(st.get('label'),str) or not st['label'].strip() or not isinstance(st.get('text',''),str): raise ValueError(f'steps[{i}]: label and optional text required')
        if len(st['label'])>40 or len(st.get('text',''))>160: raise ValueError(f'steps[{i}]: label <= 40 and text <= 160 characters; move detail to the body')
        out.append({'label':st['label'],'text':st.get('text','')})
    return out

def _scene_name(labels,steps,j,n,notes=None):
    if n<=1: return ''
    if steps:
        st=steps[j]; return f'{j+1}. {html.escape(st["label"])}'+(f'<span>{html.escape(st["text"])}</span>' if st['text'] else '')
    return html.escape(labels[j])+(f'<span>{html.escape(notes[j])}</span>' if notes else '')

def render_diagram(bundle):
    if not isinstance(bundle,dict) or set(bundle)-{'id','title','caption','status','legend','panels','labels','motion','mode','steps','notes'}:
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
        spec=panel['spec']; renderer=RENDERERS.get(spec.get('type'),render_chart)
        variants.append(renderer(spec,f"{bundle['id']}-p{i}"))
    count=max(map(len,variants))
    if any(len(v) not in (1,count) for v in variants): raise ValueError('panels: scene counts must match or be one static scene')
    mode=bundle.get('mode','compare')
    if mode not in ('compare','steps'): raise ValueError('mode: compare or steps')
    steps=_steps(bundle,panels,count) if mode=='steps' else None
    default_labels=[s['label'] for s in steps] if steps else [v['label'] for v in panels[0]['spec'].get('variants',[])]
    labels=bundle.get('labels',default_labels)
    if count>1 and (not isinstance(labels,list) or len(labels)!=count or not all(isinstance(x,str) and x.strip() for x in labels)): raise ValueError('labels: one label per scene required')
    if count==1: labels=labels or ['図']
    notes=bundle.get('notes')
    if notes is not None:
        if steps: raise ValueError('notes: use steps[].text in steps mode')
        if count<2 or not isinstance(notes,list) or len(notes)!=count or not all(isinstance(n,str) and n.strip() and len(n)<=160 for n in notes): raise ValueError('notes: one sentence (<= 160 characters) per variant required')
    if not isinstance(bundle.get('legend',[]),list): raise ValueError('legend: array required')
    if 'motion' in bundle and not isinstance(bundle['motion'],bool): raise ValueError('motion: boolean required')
    legends=[]
    for item in bundle.get('legend',[]):
        if not isinstance(item,dict) or set(item)!={'label','tone'} or not isinstance(item['label'],str) or (not isinstance(item['tone'],str) or item['tone'] not in TONES): raise ValueError('legend: label and valid tone required')
        legends.append(f'<span><i class="dg-swatch dg-tone-{item["tone"]}"></i>{html.escape(item["label"])}</span>')
    controls=''
    if steps:
        controls='<ol class="dg-steps" aria-label="手順">'+''.join(f'<li><button type="button" data-step="{i}" aria-current="{"step" if i==0 else "false"}" title="{html.escape(st["label"])}"><b>{i+1}</b><span class="dg-sr">{html.escape(st["label"])}</span></button></li>' for i,st in enumerate(steps))+'</ol>'
    elif count>1:
        controls='<fieldset class="dg-switch"><legend>比較する状態</legend>'+''.join(f'<label><input type="radio" name="{bundle["id"]}-state" value="{i}" {"checked" if i==0 else ""}><span>{html.escape(label)}</span></label>' for i,label in enumerate(labels))+'</fieldset>'
    if bundle.get('motion',False): controls+='<button class="dg-play" type="button" aria-pressed="false">流れを再生</button>'
    output=[]
    for i,scenes in enumerate(variants):
        title=panels[i].get('title',''); heading=f'<h4 class="dg-panel-title">{html.escape(title)}</h4>' if title else ''
        static=''.join(f'<div class="dg-static-scene" data-state="{j}"><p class="dg-scene-name">{_scene_name(labels,steps,j,len(scenes),notes)}</p><div class="dg-scroll" tabindex="0" role="region" aria-label="{html.escape(title or bundle["title"])}">{svg}</div></div>' for j,svg in enumerate(scenes))
        output.append(f'<div class="dg-panel">{heading}<div class="dg-live dg-scroll" tabindex="0" role="region" aria-label="{html.escape(title or bundle["title"])}"></div><div class="dg-static">{static}</div></div>')
    nav=''
    if steps:
        texts=''.join(f'<template data-step-text="{i}"><b>{i+1}. {html.escape(st["label"])}</b>{(" "+html.escape(st["text"])) if st["text"] else ""}</template>' for i,st in enumerate(steps))
        nav=f'<div class="dg-step-bar"><p class="dg-step-text" aria-live="polite"></p><div class="dg-step-nav"><button type="button" data-go="-1" aria-label="前の手順">←</button><span class="dg-step-count" aria-hidden="true">1 / {count}</span><button type="button" data-autoplay aria-pressed="false">自動で進める</button><button type="button" data-go="1" aria-label="次の手順">→</button></div>{texts}</div>'
    if notes:
        texts=''.join(f'<template data-step-text="{i}"><b>{html.escape(labels[i])}</b> {html.escape(n)}</template>' for i,n in enumerate(notes))
        nav=f'<div class="dg-step-bar dg-note-bar"><p class="dg-step-text" aria-live="polite"></p>{texts}</div>'
    if steps:
        nav+='<ol class="dg-step-notes">'+''.join(f'<li><b>{html.escape(st["label"])}</b>{(" "+html.escape(st["text"])) if st["text"] else ""}</li>' for st in steps)+'</ol>'
    mode_attr=' data-mode="steps"' if steps else ''
    return f'<figure class="dg-figure" id="{bundle["id"]}" data-diagram data-state="0"{mode_attr}><h3 class="dg-title">{html.escape(bundle["title"])}</h3><div class="dg-toolbar">{controls}</div><div class="dg-legend">{"".join(legends)}</div>{nav}{"".join(output)}<figcaption><span class="status status-{status}">{STATUSES[status]}</span>{html.escape(bundle["caption"])}</figcaption></figure>'

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
