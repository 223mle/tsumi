"""Compose validated diagrams and synchronized scene controls without page-specific code."""
from __future__ import annotations
import argparse
import html
import json
import re
from pathlib import Path
from charts import render_chart, has_narrow_layout
from network import render_network, network_steps
from decisions import render_decision
from sequence import NOTES as sequence_notes, render_sequence, sequence_steps
from charts import NOTES as chart_notes
from linechart import render_line

ROOT = Path(__file__).resolve().parents[1]
TONES = {'blue','teal','violet','amber','rose','slate','red'}
STATUS_HELP = {'measured':'実際に測った値です。','inferred':'根拠となる資料や条件から計算・推定した値です。','planned':'決まっている予定や手順で、まだ実施していません。','proposed':'これから行う案で、まだ実施していません。','unknown':'まだ決まっていない、または確かめていない部分です。','illustrative':'仕組みを説明するための例で、実際の値ではありません。','code':'コードから読み取った内容です。'}
STATUSES = {'measured':'計測値','inferred':'推定','planned':'予定','proposed':'提案','unknown':'未確定','illustrative':'説明用','code':'コード'}  # same words as render.py's basic figures

RENDERERS={'network':render_network,'decision':render_decision,'sequence':render_sequence,'line':render_line}

def _used_tones(spec):
    """Every colour a panel draws in: tones written in the spec, plus the defaults its parts fall back to."""
    found=set()
    def walk(o):
        if isinstance(o,dict):
            if isinstance(o.get('tone'),str): found.add(o['tone'])
            for v in o.values(): walk(v)
        elif isinstance(o,list):
            for v in o: walk(v)
    walk(spec)
    if spec.get('type')=='network':
        edges=spec.get('edges',[])+[e for v in spec.get('variants',[]) for e in v.get('edges',[])]
        found|={('red' if e.get('kind')=='conflict' else 'blue') for e in edges if 'tone' not in e}
        found|={'slate' for n in spec.get('nodes',[]) if 'tone' not in n}
    else:
        found|={'blue','slate','red'}  # defaults of bars, messages and thresholds
    return found


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

def _scene_name(labels,steps,j,n,notes=None,prose=html.escape):
    if n<=1: return ''
    if steps:
        st=steps[j]; return f'{j+1}. {html.escape(st["label"])}'+(f'<span>{prose(st["text"])}</span>' if st['text'] else '')
    return html.escape(labels[j])+(f'<span>{prose(notes[j])}</span>' if notes else '')

def render_diagram(bundle,prose=html.escape,source_titles=None,warnings=None):
    """Render a bundle as a figure. `prose` renders caption, notes and step texts; documents pass their inline markup."""
    if not isinstance(bundle,dict): raise ValueError('diagram: object required')
    extra=set(bundle)-{'id','title','caption','status','legend','panels','labels','motion','mode','steps','notes','slider','initial','source_ids'}
    if extra: raise ValueError(f'diagram: unknown fields {sorted(extra)} (chart options such as baseline go in panels[].spec)')
    for key in ('id','title','caption'):
        if not isinstance(bundle.get(key),str) or not bundle[key].strip(): raise ValueError(f'diagram.{key}: text required')
    if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_-]*',bundle['id']): raise ValueError('diagram.id: invalid identifier')
    refs=bundle.get('source_ids',[])
    if not isinstance(refs,list) or not all(isinstance(r,str) for r in refs): raise ValueError('source_ids: list of source ids required')
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
    if mode not in ('compare','steps','slider'): raise ValueError('mode: compare, steps or slider')
    slider=bundle.get('slider')
    if mode=='slider':
        if count<3: raise ValueError('slider: at least three variants required; use compare for two')
        if not isinstance(slider,str) or not slider.strip() or len(slider)>20: raise ValueError('slider: the name of the quantity (<= 20 characters) required')
    elif slider is not None: raise ValueError('slider: only with mode slider')
    initial=bundle.get('initial',0)
    if not isinstance(initial,int) or isinstance(initial,bool) or not 0<=initial<max(count,1) or (initial and mode!='slider'): raise ValueError('initial: a variant index, only with mode slider')
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
    named={item['tone'] for item in bundle.get('legend',[])}
    if named:
        # A path colour the legend does not name leaves the reader guessing what it means.
        for panel in panels:
            spec=panel['spec']
            if spec.get('type')!='network': continue
            for edge in spec.get('edges',[])+[e for v in spec.get('variants',[]) for e in v.get('edges',[])]:
                if spec.get('edges') and 'step' not in edge: continue  # context edges in a step figure are drawn grey
                tone=edge.get('tone','blue')
                if edge.get('kind')!='conflict' and tone!='slate' and tone not in named:  # grey reads as neutral
                    raise ValueError(f"legend: edge {edge.get('id')} is drawn in {tone}, which the legend does not name; add it to the legend or reuse a named colour")
        # An edge left at the default blue takes on whatever the legend says blue means.
        blue=next((item['label'] for item in bundle.get('legend',[]) if item['tone']=='blue'),None)
        defaulted=[e.get('id') for p in panels if p['spec'].get('type')=='network' for e in p['spec'].get('edges',[])+[x for v in p['spec'].get('variants',[]) for x in v.get('edges',[])] if 'tone' not in e and e.get('kind')!='conflict' and not (p['spec'].get('edges') and 'step' not in e)]
        if blue and defaulted and warnings is not None:
            warnings.append(f"{bundle['id']}: edges without a tone ({', '.join(dict.fromkeys(defaulted))}) are drawn blue, which the legend calls 「{blue}」; give them a tone")
        # A legend entry nothing is drawn in sends the reader looking for a colour that is not there.
        unused=named-set().union(*(_used_tones(p['spec']) for p in panels))
        if unused: raise ValueError(f"legend: nothing in the figure is drawn in {sorted(unused)}; drop the entry or use the colour")
    controls=''
    if steps:
        controls='<ol class="dg-steps" aria-label="手順">'+''.join(f'<li><button type="button" data-step="{i}" aria-current="{"step" if i==0 else "false"}"><b>{i+1}</b><span class="dg-sr">{html.escape(st["label"])}</span></button></li>' for i,st in enumerate(steps))+'</ol>'
    elif mode=='slider':
        # Each stop is labelled under the track, so the reader sees every value the figure can show.
        ticks=''.join(f'<span style="left:calc(9px + (100% - 18px) * {i}/{count-1})">{html.escape(l)}</span>' for i,l in enumerate(labels))
        controls=(f'<div class="dg-slider"><span class="dg-slider-name" id="{bundle["id"]}-slider">{html.escape(slider)}</span>'
                  f'<div class="dg-slider-track"><input type="range" min="0" max="{count-1}" step="1" value="{initial}" aria-labelledby="{bundle["id"]}-slider" aria-valuetext="{html.escape(labels[initial])}" data-labels="{html.escape(json.dumps(labels,ensure_ascii=False))}">'
                  f'<div class="dg-slider-ticks" aria-hidden="true">{ticks}</div></div><output aria-hidden="true">{html.escape(labels[initial])}</output></div>')
    elif count>1:
        controls='<fieldset class="dg-switch"><legend>比較する状態</legend>'+''.join(f'<label><input type="radio" name="{bundle["id"]}-state" value="{i}" {"checked" if i==0 else ""}><span>{html.escape(label)}</span></label>' for i,label in enumerate(labels))+'</fieldset>'
    if bundle.get('motion',False): controls+='<button class="dg-play" type="button" aria-pressed="false">流れを再生</button>'
    if count>2 and mode=='compare': controls+='<button class="dg-grid-toggle" type="button" aria-pressed="false">すべて並べる</button>'
    controls+='<button class="dg-fit-toggle" type="button" aria-pressed="false">全体を縮小表示</button>'
    output=[]
    for i,scenes in enumerate(variants):
        title=panels[i].get('title',''); heading=f'<h4 class="dg-panel-title">{html.escape(title)}</h4>' if title else ''
        # Charts also get a phone layout; CSS shows one of the two and the script keeps both in step.
        spec=panels[i]['spec']
        narrow=None
        phone=(render_chart if has_narrow_layout(spec) else RENDERERS.get(spec.get('type')) if spec.get('type') in ('line','network','sequence','decision') else None)
        if phone:
            sequence_notes.clear();chart_notes.clear()
            try: narrow=phone(spec,f"{bundle['id']}-p{i}n",narrow=True)
            except ValueError as exc:
                narrow=None  # something does not fit the phone layout; keep scrolling the wide one
                if warnings is not None: warnings.append(f"{bundle['id']}: no phone layout, so phones scroll it sideways ({exc})")
        if warnings is not None: warnings.extend(f"{bundle['id']}: {n}" for n in dict.fromkeys(sequence_notes+chart_notes))
        sequence_notes.clear();chart_notes.clear()
        layouts=[(' dg-wide',scenes),(' dg-narrow',narrow)] if narrow else [('',scenes)]
        for cls,svgs in layouts:
            static=''.join(f'<div class="dg-static-scene" data-state="{j}"><p class="dg-scene-name">{_scene_name(labels,steps,j,len(svgs),notes,prose)}</p><div class="dg-scroll" tabindex="0" role="region" aria-label="{html.escape(title or bundle["title"])}">{svg}</div></div>' for j,svg in enumerate(svgs))
            output.append(f'<div class="dg-panel{cls}">{heading}<div class="dg-live dg-scroll" tabindex="0" role="region" aria-label="{html.escape(title or bundle["title"])}"></div><div class="dg-static">{static}</div></div>')
    nav=''
    if steps:
        texts=''.join(f'<template data-step-text="{i}"><b>{i+1}. {html.escape(st["label"])}</b>{(" "+prose(st["text"])) if st["text"] else ""}</template>' for i,st in enumerate(steps))
        nav=f'<div class="dg-step-bar"><p class="dg-step-text" aria-live="polite"></p><div class="dg-step-nav"><button type="button" data-go="-1" aria-label="前の手順">← 前へ</button><span class="dg-step-count" aria-hidden="true">1 / {count}</span><button type="button" data-autoplay aria-pressed="false">自動で進める</button><button type="button" data-go="1" aria-label="次の手順">次へ →</button></div>{texts}</div>'
    if notes:
        texts=''.join(f'<template data-step-text="{i}"><b>{html.escape(labels[i])}</b> {prose(n)}</template>' for i,n in enumerate(notes))
        nav=f'<div class="dg-step-bar dg-note-bar"><p class="dg-step-text" aria-live="polite"></p>{texts}</div>'
    if steps:
        nav+='<ol class="dg-step-notes">'+''.join(f'<li><b>{html.escape(st["label"])}</b>{(" "+prose(st["text"])) if st["text"] else ""}</li>' for st in steps)+'</ol>'
    mode_attr=f' data-mode="{mode}"' if mode!='compare' else ''
    titles=source_titles or {}
    source_links=''.join(' <a class="source-ref" href="#'+html.escape(r)+'">'+html.escape(titles.get(r,r))+'</a>' for r in refs)
    return f'<figure class="dg-figure" id="{bundle["id"]}" data-diagram data-state="{initial}"{mode_attr}><h3 class="dg-title">{html.escape(bundle["title"])}</h3><div class="dg-toolbar">{controls}</div><div class="dg-legend">{"".join(legends)}</div>{nav}{"".join(output)}<figcaption><span class="term status-term" tabindex="0" aria-describedby="{bundle["id"]}-status"><span class="status status-{status}">{STATUSES[status]}</span><span class="term-tip" role="tooltip" id="{bundle["id"]}-status" aria-hidden="true"><b>{STATUSES[status]}</b>{STATUS_HELP[status]}</span></span>{prose(bundle["caption"])}{source_links}</figcaption></figure>'

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
