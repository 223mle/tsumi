"""Restyle an existing explanatory HTML, replacing every figure with validated components."""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
import argparse, html, json, re
from urllib.parse import urlparse
from diagrams import render_diagram

def safe_href(value):
    """Allow only http(s), mailto and in-page or relative links; browsers ignore whitespace and control characters inside a scheme."""
    norm=re.sub(r'[\x00-\x20\x7f]','',value or '')
    p=urlparse(norm)
    if p.scheme.lower() in {'http','https','mailto'} or (not p.scheme and not norm.startswith('//')):return norm
    raise ValueError('source: unsafe link')

ROOT=Path(__file__).resolve().parents[1]
VOID={'br','hr','img','meta','link','input','source','wbr'}
ALLOWED={'main','section','article','aside','div','span','h1','h2','h3','h4','h5','h6','p','a','strong','em','b','i','small','code','pre','ul','ol','li','table','thead','tbody','tfoot','tr','td','th','caption','details','summary','footer','br','hr','sup','sub'}
class Node:
    def __init__(self,tag,attrs=()):self.tag=tag;self.attrs=dict(attrs);self.children=[]
    def text(self):return ''.join(c if isinstance(c,str) else c.text() for c in self.children)
    def find(self,tag):
        result=[self] if self.tag==tag else []
        for c in self.children:
            if isinstance(c,Node):result.extend(c.find(tag))
        return result
class Parser(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.root=Node('root');self.stack=[self.root]
    def handle_starttag(self,tag,attrs):
        n=Node(tag,attrs);self.stack[-1].children.append(n)
        if tag not in VOID:self.stack.append(n)
    def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:self.stack=self.stack[:i];break
    def handle_data(self,data):self.stack[-1].children.append(data)

def compose(source,manifest):
    if not isinstance(manifest,dict) or set(manifest)-{'figures','notice'}:raise ValueError('manifest: figures and optional notice only')
    figures=manifest.get('figures')
    if not isinstance(figures,list):raise ValueError('manifest.figures: array required')
    p=Parser();p.feed(source);mains=p.root.find('main')
    if len(mains)!=1:raise ValueError('source: exactly one main required')
    main=mains[0];original_figs=main.find('figure')
    if len(original_figs)!=len(figures):raise ValueError(f'figures: source has {len(original_figs)}, manifest has {len(figures)}; every figure must be replaced')
    ids=[n.attrs['id'] for n in main.find('h2')+main.find('h3') if 'id'in n.attrs]+[f.get('id')for f in figures]
    if len(ids)!=len(set(ids)):raise ValueError('source headings and diagram IDs must be unique')
    rendered=iter(render_diagram(f) for f in figures)
    def emit(node):
        if isinstance(node,str):return html.escape(node)
        if node.tag=='figure':
            result=next(rendered)
            links=node.find('a')
            if links:result=result.replace('</figcaption>',' <span class="dg-original-sources">原図の出典：'+ '、'.join(emit(a)for a in links)+'</span></figcaption>')
            return result
        if node.tag in {'script','style','iframe','object','embed'}:return ''
        if node.tag not in ALLOWED:return ''.join(emit(c) for c in node.children)
        attrs=[]
        for key,value in node.attrs.items():
            if key not in {'id','class','href','scope','colspan','rowspan','open','title','data-tip'}:continue
            if key=='href':value=safe_href(value)
            attrs.append(f'{key}="{html.escape(value or "",quote=True)}"')
        if node.tag=='th' and 'scope' not in node.attrs:attrs.append('scope="col"')
        body=''.join(emit(c)for c in node.children)
        if node.tag=='table':
            tips=[]
            for row in node.find('tr'):
                def collect(n):
                    if isinstance(n,str):return
                    if n.attrs.get('data-tip'):tips.append(n.attrs['data-tip'])
                    for c in n.children:collect(c)
                collect(row)
            tip_html='<details class="tip-notes"><summary>記号の判断理由</summary><ul>'+''.join('<li>'+html.escape(t)+'</li>'for t in tips)+'</ul></details>'if tips else ''
            if not node.find('caption'):body='<caption class="visually-hidden">比較・参考資料</caption>'+body
            body='<table '+ ' '.join(attrs)+'>'+body+'</table>'
            return '<div class="table-wrap" tabindex="0" role="region" aria-label="横にスクロールできる表">'+body+'</div>'+tip_html
        return '<'+node.tag+(' '+' '.join(attrs)if attrs else '')+'>'+body+(''if node.tag in VOID else '</'+node.tag+'>')
    content=''.join(emit(n)for n in main.children)
    heads=[]
    for c in main.children:
        if isinstance(c,Node)and c.tag in ('h2','h3')and c.attrs.get('id'):
            heads.append(f'<li class="toc-{c.tag}"><a href="#{html.escape(c.attrs["id"])}">{html.escape(" ".join(c.text().split()))}</a></li>')
    titles=main.find('h1');title=titles[0].text()if titles else '解説資料'
    notice=manifest.get('notice','')
    if not isinstance(notice,str):raise ValueError('notice: text required')
    notice_html=f'<p class="edition-note">{html.escape(notice)}</p>'if notice else ''
    css='\n'.join((ROOT/'assets'/n).read_text()for n in ['style.css','paper.css','diagrams.css'])
    js='\n'.join((ROOT/'assets'/n).read_text()for n in ['behavior.js','diagrams.js'])
    return f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>{css}</style></head><body><a class="skip-link" href="#main">本文へ移動</a><div class="layout"><nav class="toc" aria-label="目次"><div class="theme-controls"><button data-theme-set="system">自動</button><button data-theme-set="light">ライト</button><button data-theme-set="dark">ダーク</button></div><div class="toc-title">目次</div><ol>{"".join(heads)}</ol></nav><main id="main">{notice_html}{content}</main></div><script>{js}</script></body></html>'

def main():
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('manifest',type=Path);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
    try:
        result=compose(args.source.read_text(),json.loads(args.manifest.read_text()))
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(result)
    except (ValueError,OSError)as exc:a.exit(2,f'{exc}\n')
if __name__=='__main__':main()
