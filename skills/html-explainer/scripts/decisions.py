"""A compact two-track decision overview; content stays separate from layout."""
from html import escape

def render_decision(spec,prefix):
    if not isinstance(spec,dict)or set(spec)-{'type','columns'} or not isinstance(spec.get('columns'),list)or len(spec['columns'])!=2:raise ValueError('decision: exactly two columns required')
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 268" role="img" aria-label="対応方針の比較"><title>対応方針の比較</title>']
    for i,col in enumerate(spec['columns']):
        if not isinstance(col,dict)or set(col)-{'title','eyebrow','items','footer'}:raise ValueError('decision column: unknown fields')
        for k in ('title','eyebrow','footer'):
            if not isinstance(col.get(k),str)or len(col[k])>45:raise ValueError(f'decision.{k}: short text required')
        items=col.get('items');x=12+i*478;tone='blue'if i==0 else'violet'
        if not isinstance(items,list)or len(items)!=2 or not all(isinstance(s,str)and len(s)<35 for s in items):raise ValueError('decision.items: two short labels required')
        out.append(f'<rect x="{x}" y="8" width="458" height="250" rx="8" class="group-band group-{tone}" data-key="column-{i}"/>')
        for j,(y,value,cls)in enumerate([(35,col['eyebrow'],'axis-label'),(67,col['title'],'group-label'),(116,items[0],'lane-label'),(155,items[1],'lane-label'),(222,col['footer'],'group-label')]):
            out.append(f'<text x="{x+24}" y="{y}" class="{cls}" data-label="true" data-key="column-{i}-text-{j}">{escape(value)}</text>')
    return [''.join(out)+'</svg>']
