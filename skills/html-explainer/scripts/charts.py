"""Small, deterministic SVG charts for explanatory HTML.

The caller supplies semantic data. This module owns scale, coordinates, labels,
and stable ``data-key`` attributes so two variants can be animated by a page.
"""
from __future__ import annotations

import html
import math
import re
from typing import Any

import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent))  # loadable by file path as well as by name
from jawrap import plain, wrap

TONES = {"blue", "teal", "violet", "amber", "rose", "slate", "red"}
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")


def _fail(path: str, message: str) -> None:
    raise ValueError(f"{path}: {message}")


def _num(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(path, "finite number required")
    try:
        result = float(value)
    except (OverflowError, ValueError):
        _fail(path, "finite number required")
    if not math.isfinite(result):
        _fail(path, "finite number required")
    return result


def _id(value: Any, path: str, seen: set[str]) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        _fail(path, "valid identifier required")
    if value in seen:
        _fail(path, f"duplicate id {value}")
    seen.add(value)
    return value


def _text(value: Any, path: str, required: bool = True) -> str:
    if not isinstance(value, str) or (required and not value.strip()):
        _fail(path, "non-empty text required")
    return value


def _tone(value: Any, path: str) -> str:
    if value is None:
        return "blue"
    if not isinstance(value, str) or value not in TONES:
        _fail(path, f"tone must be one of {sorted(TONES)}")
    return value


def validate_chart(spec: dict[str, Any]) -> None:
    if not isinstance(spec, dict):
        _fail("chart", "object required")
    allowed = {"type", "min", "max", "unit", "ticks", "lanes", "groups", "variants", "rows", "thresholds", "scale", "baseline"}
    if set(spec) - allowed: _fail("chart", "unknown fields")
    if "baseline" in spec and (not isinstance(spec["baseline"], bool) or spec.get("type") != "timeline"):
        _fail("chart.baseline", "boolean for a timeline required")
    kind = spec.get("type")
    if kind == "timeline":
        _validate_timeline(spec)
    elif kind == "threshold":
        _validate_threshold(spec)
    else:
        _fail("chart.type", "timeline or threshold required")


def _domain(spec: dict[str, Any], path: str) -> tuple[float, float]:
    lo, hi = _num(spec.get("min"), f"{path}.min"), _num(spec.get("max"), f"{path}.max")
    if not lo < hi:
        _fail(path, "min must be less than max")
    _text(spec.get("unit"), f"{path}.unit")
    ticks = spec.get("ticks")
    if not isinstance(ticks, list) or not ticks:
        _fail(f"{path}.ticks", "non-empty array required")
    prev = None
    for i, tick in enumerate(ticks):
        if isinstance(tick, dict):
            # {"value": 30, "label": "5/1"} names a tick, for dates or other non-numeric axes.
            if set(tick) != {"value", "label"} or not isinstance(tick["label"], str) or not tick["label"].strip() or len(tick["label"]) > 10:
                _fail(f"{path}.ticks[{i}]", "a number, or value and a label of at most 10 characters")
            tick = tick["value"]
        val = _num(tick, f"{path}.ticks[{i}]")
        if not lo <= val <= hi or (prev is not None and val <= prev):
            _fail(f"{path}.ticks[{i}]", "ticks must be increasing and inside the domain")
        prev = val
    return lo, hi


def _validate_timeline(spec: dict[str, Any]) -> None:
    lo, hi = _domain(spec, "chart")
    lanes = spec.get("lanes")
    if not isinstance(lanes, list) or not lanes:
        _fail("chart.lanes", "non-empty array required")
    lane_ids: set[str] = set()
    for i, lane in enumerate(lanes):
        if not isinstance(lane, dict):
            _fail(f"chart.lanes[{i}]", "object required")
        _id(lane.get("id"), f"chart.lanes[{i}].id", lane_ids)
        _text(lane.get("label"), f"chart.lanes[{i}].label")
        _tone(lane.get("tone"), f"chart.lanes[{i}].tone")
    groups = spec.get("groups", [])
    if not isinstance(groups, list):
        _fail("chart.groups", "array required")
    for gi, group in enumerate(groups):
        if not isinstance(group, dict):
            _fail(f"chart.groups[{gi}]", "object required")
        allowed = {"label", "lane_ids", "tone", "summary"}
        if set(group) - allowed:
            _fail(f"chart.groups[{gi}]", f"unknown fields {sorted(set(group) - allowed)}")
        _text(group.get("label"), f"chart.groups[{gi}].label")
        members = group.get("lane_ids")
        if not isinstance(members, list) or not members:
            _fail(f"chart.groups[{gi}].lane_ids", "non-empty array required")
        if any(not isinstance(member,str) or member not in lane_ids for member in members):
            _fail(f"chart.groups[{gi}].lane_ids", "unknown lane")
        _tone(group.get("tone"), f"chart.groups[{gi}].tone")
        if "summary" in group:
            _text(group["summary"], f"chart.groups[{gi}].summary", False)
    variants = spec.get("variants")
    if not isinstance(variants, list) or not variants:
        _fail("chart.variants", "non-empty array required")
    for vi, variant in enumerate(variants):
        if not isinstance(variant, dict):
            _fail(f"chart.variants[{vi}]", "object required")
        _text(variant.get("label"), f"chart.variants[{vi}].label")
        if set(variant) - {"label", "summary", "segments", "markers", "group_summaries"}: _fail(f"chart.variants[{vi}]", "unknown fields")
        if "summary" in variant: _text(variant["summary"], f"chart.variants[{vi}].summary")
        if "group_summaries" in variant:
            if not isinstance(variant["group_summaries"],list) or len(variant["group_summaries"]) != len(spec.get("groups",[])) or not all(isinstance(x,str)for x in variant["group_summaries"]): _fail("variant.group_summaries","one string per group required")
        seen: set[str] = set()
        segments = variant.get("segments", [])
        if not isinstance(segments, list):
            _fail(f"chart.variants[{vi}].segments", "array required")
        for si, seg in enumerate(segments):
            if not isinstance(seg, dict):
                _fail(f"chart.variants[{vi}].segments[{si}]", "object required")
            _id(seg.get("id"), f"chart.variants[{vi}].segments[{si}].id", seen)
            if not isinstance(seg.get("lane"),str) or seg.get("lane") not in lane_ids:
                _fail(f"chart.variants[{vi}].segments[{si}].lane", "unknown lane")
            start = _num(seg.get("start"), "segment.start")
            if seg.get("unknown") is True:
                if "duration" in seg: _fail("segment.duration", "unknown segment cannot have a numeric duration")
                if not lo <= start <= hi: _fail("segment.start", "outside domain")
                _text(seg.get("label"), "segment.label")
                continue
            if "unknown" in seg and not isinstance(seg["unknown"],bool): _fail("segment.unknown", "boolean required")
            duration = _num(seg.get("duration"), "segment.duration")
            if duration <= 0 or start < lo or start + duration > hi:
                _fail(f"chart.variants[{vi}].segments[{si}]", "segment must fit the shared domain")
            if "label" in seg:
                _text(seg["label"], "segment.label", False)
            _tone(seg.get("tone"), f"chart.variants[{vi}].segments[{si}].tone")
        markers = variant.get("markers", [])
        if not isinstance(markers, list):
            _fail(f"chart.variants[{vi}].markers", "array required")
        for mi, marker in enumerate(markers):
            if not isinstance(marker, dict):
                _fail(f"chart.variants[{vi}].markers[{mi}]", "object required")
            _id(marker.get("id"), f"chart.variants[{vi}].markers[{mi}].id", seen)
            value = _num(marker.get("value"), "marker.value")
            if not lo <= value <= hi:
                _fail(f"chart.variants[{vi}].markers[{mi}].value", "outside shared domain")
            _text(marker.get("label"), "marker.label")
            _tone(marker.get("tone"), "marker.tone")


def _validate_threshold(spec: dict[str, Any]) -> None:
    lo, hi = _domain(spec, "chart")
    if not isinstance(spec.get("scale","linear"),str) or spec.get("scale", "linear") not in {"linear", "log"}:
        _fail("chart.scale", "linear or log required")
    if spec.get("scale", "linear") == "log" and lo <= 0:
        _fail("chart.min", "log scale requires a positive minimum")
    ids: set[str] = set()
    rows = spec.get("rows")
    if not isinstance(rows, list) or not rows:
        _fail("chart.rows", "non-empty array required")
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            _fail(f"chart.rows[{i}]", "object required")
        _id(row.get("id"), f"chart.rows[{i}].id", ids)
        _text(row.get("label"), f"chart.rows[{i}].label")
        value = _num(row.get("value"), f"chart.rows[{i}].value")
        if not lo <= value <= hi:
            _fail(f"chart.rows[{i}].value", "outside domain")
        _tone(row.get("tone"), f"chart.rows[{i}].tone")
        if "value_label" in row: _text(row["value_label"], f"chart.rows[{i}].value_label")
    if not isinstance(spec.get("thresholds", []), list): _fail("chart.thresholds", "array required")
    for i, threshold in enumerate(spec.get("thresholds", [])):
        if not isinstance(threshold, dict):
            _fail(f"chart.thresholds[{i}]", "object required")
        _id(threshold.get("id"), f"chart.thresholds[{i}].id", ids)
        value = _num(threshold.get("value"), f"chart.thresholds[{i}].value")
        if not lo <= value <= hi:
            _fail(f"chart.thresholds[{i}].value", "outside domain")
        _text(threshold.get("label"), f"chart.thresholds[{i}].label")
        _tone(threshold.get("tone"), f"chart.thresholds[{i}].tone")


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _scale(value: float, lo: float, hi: float, x0: float, width: float, log: bool = False) -> float:
    if log:
        value, lo, hi = math.log10(value), math.log10(lo), math.log10(hi)
    return x0 + (value - lo) / (hi - lo) * width


def _tick(tick: Any, unit: str) -> tuple[float, str]:
    """A tick's value and its axis text."""
    if isinstance(tick, dict):
        return float(tick["value"]), tick["label"]
    return float(tick), f"{_number(float(tick))}{unit}"


def _number(v: float) -> str:
    """Plain digits for readers: 1,000,000 rather than 1e+06; up to six significant digits otherwise."""
    if v.is_integer() and abs(v) < 1e15:
        return f"{int(v):,}" if abs(v) >= 10000 else str(int(v))
    return f"{v:.6g}"


def _tick_stride(spec: dict[str, Any], lo: float, hi: float, width: float, log: bool = False) -> int:
    """Label every n-th tick so that tick texts never touch; gridlines stay on every tick."""
    texts=[_tick(t,spec['unit']) for t in spec['ticks']]
    xs=[_scale(v,lo,hi,0,width,log) for v,_ in texts]
    need=max(sum(12 if ord(c)>255 else 7 for c in t) for _,t in texts)+8
    gap=min((b-a for a,b in zip(xs,xs[1:])),default=need)
    return max(1,math.ceil(need/max(gap,1)))


def _text_width(text: str) -> float:
    return sum(12 if ord(c) > 255 else 7 for c in text)


def _marker_layout(markers, lo, hi, x0, width, W, log=False):
    """Place marker labels on as few rows as needed so that no two labels touch."""
    rows, placed = [], []
    for m in sorted(markers, key=lambda m: float(m['value'])):
        x = _scale(float(m['value']), lo, hi, x0, width, log); tw = _text_width(m['label'])
        anchor, l, r = ('start', x + 5, x + 5 + tw) if x + 5 + tw <= W - 4 else ('end', x - 5 - tw, x - 5)
        if l < 4:
            raise ValueError(f"marker label is too long for the canvas: {m['label']}")
        row = next((i for i, used in enumerate(rows) if all(r + 8 <= a or l - 8 >= b for a, b in used)), len(rows))
        if row == len(rows): rows.append([])
        rows[row].append((l, r)); placed.append((m['id'], x, anchor, row))
    return {mid: (x, anchor, row) for mid, x, anchor, row in placed}, len(rows)


def _label_span(x: float, text: str, W: float) -> tuple[float, float]:
    """Where _axis_label actually draws a tick label: centred, or pulled inside the canvas at either end."""
    tw = _text_width(text)
    left = min(max(x - tw / 2, 2), W - 2 - tw)
    return left, left + tw


def choose_ticks(ticks: list[tuple[float, str]], to_x, W: float, marked: set) -> set:
    """Tick values to label so no two labels touch: zero, the two ends, marked values, then the rest in order."""
    first, last = ticks[0][0], ticks[-1][0]
    order = sorted(ticks, key=lambda t: (t[0] != 0, t[0] not in (first, last), t[0] not in marked, t[0]))
    spans: list[tuple[float, float]] = []
    keep = set()
    for value, text in order:
        a, b = _label_span(to_x(value), text, W)
        if all(b + 6 <= c or a - 6 >= d for c, d in spans):
            spans.append((a, b)); keep.add(value)
    return keep


def _axis_label(x: float, y: float, text: str, W: float, key: str) -> str:
    """A tick label centred on its tick, pulled inside the canvas at either end."""
    tw = _text_width(text)
    if x + tw / 2 > W - 2: return _svg_text(W - 2, y, text, 'axis-label', 'end', key)
    if x - tw / 2 < 2: return _svg_text(2, y, text, 'axis-label', 'start', key)
    return _svg_text(x, y, text, 'axis-label', 'middle', key)


def _svg_text(x: float, y: float, value: str, cls: str = "label", anchor: str = "start", key: str = "") -> str:
    return f'<text x="{x:.2f}" y="{y:.2f}" class="{cls}" text-anchor="{anchor}" data-label="true" data-key="{_esc(key)}">{_esc(value)}</text>'


def _svg_wrapped_text(x, y, value, cls, key, max_chars=18, anchor="start", max_lines=3):
    # max_chars counts 12px CJK glyphs; jawrap counts them as two units.
    lines=wrap(value,max_chars*2,max_lines) if value else [value]
    if lines is None: _fail(key,"label exceeds three lines; shorten it, mark the break with \\n, or move detail to the caption")
    spans="".join(f'<tspan x="0" dy="{0 if i==0 else 15}">{_esc(line)}</tspan>' for i,line in enumerate(lines))
    return f'<text transform="translate({x:.2f},{y:.2f})" class="{cls}" text-anchor="{anchor}" data-label="true" data-key="{_esc(key)}">{spans}</text>'


NARROW_WIDTH=420  # viewBox width of the phone layout: about 0.8x scale at 340px, so 13px text stays near 11px


def _timeline_svg(spec, variant, index, prefix, narrow=False):
    lo,hi=float(spec["min"]),float(spec["max"])
    grouped=bool(spec.get("groups"))
    if narrow:
        W=NARROW_WIDTH;x0=90.0;width=W-x0-16;limit=W-6;lane_chars=5
    else:
        W=960;x0=330.0 if grouped else 200.0;width=800-x0;limit=940;lane_chars=12 if grouped else 14
    ext_x=W-144
    # Every variant shares the label rows so the canvas height stays fixed while switching.
    label_rows=max([_marker_layout(v.get('markers',[]),lo,hi,x0,width,W)[1] for v in spec['variants']]+[0])
    lift=(label_rows-2)*17 if label_rows else -34  # no marker labels: no empty band above the first lane
    lanes=spec["lanes"];row_height=38;top=58+lift;h=top+len(lanes)*row_height+34
    title=variant["label"]
    # The text alternative carries the data itself, not a description of the chart type.
    lane_names={l['id']:plain(l['label']) for l in lanes}
    parts_desc=[f"{lane_names[g['lane']]} {plain(g.get('label') or '')}".strip() for g in variant.get('segments',[])]
    parts_desc+=[plain(m['label']) for m in variant.get('markers',[])]
    desc=variant.get("summary") or f"{plain(title)}: "+"、".join(parts_desc)
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" role="img" aria-labelledby="{prefix}-{index}-title" aria-describedby="{prefix}-{index}-desc"><title id="{prefix}-{index}-title">{_esc(title)}</title><desc id="{prefix}-{index}-desc">{_esc(desc)}</desc>']
    for gi,group in enumerate(spec.get("groups", [])):
        members=[i for i,lane in enumerate(lanes)if lane['id'] in group['lane_ids']]
        gy=top+min(members)*row_height-7;gh=(max(members)-min(members)+1)*row_height-1;tone=group.get('tone','slate');cy=gy+gh/2
        out.append(f'<rect x="10" y="{gy}" width="936" height="{gh}" rx="7" class="group-band group-{tone}" data-key="group-{gi}"/>')
        out.append(f'<rect x="10" y="{gy}" width="140" height="{gh}" rx="7" class="group-heading group-{tone}" data-key="group-heading-{gi}"/>')
        out.append(_svg_wrapped_text(24,cy-13,group['label'],'group-label',f'group-label-{gi}',9))
        summary=variant.get('group_summaries',[g.get('summary','')for g in spec.get('groups',[])])[gi]
        if summary:out.append(_svg_wrapped_text(24,cy+(12 if gh<60 else 22),summary,'group-summary',f'group-summary-{gi}',9))
    ticks=[_tick(t,spec['unit']) for t in spec['ticks']]
    marked={float(m['value']) for v in spec['variants'] for m in v.get('markers',[])}
    keep=choose_ticks(ticks,lambda v:_scale(v,lo,hi,x0,width),W,marked)
    for value,text in ticks:
        x=_scale(value,lo,hi,x0,width)
        out.append(f'<line x1="{x:.2f}" y1="{48+lift}" x2="{x:.2f}" y2="{h-28}" class="axis-grid" data-key="tick-{value:g}"/>')
        if value in keep:out.append(_axis_label(x,h-9,text,W,f'tick-label-{value:g}'))
    for i,lane in enumerate(lanes):
        y=top+i*row_height
        # Rows are 38px apart, so a phone-width lane name may take two lines at most.
        lines=len(wrap(lane['label'],lane_chars*2,2) or [1]) if narrow else 1
        out.append(_svg_wrapped_text(x0-12,y+15-(lines-1)*7.5,lane['label'],'lane-label',f"lane-label-{lane['id']}",lane_chars,'end',2 if narrow else 3))
    external={}
    marker_xs=[_scale(float(m['value']),lo,hi,x0,width) for m in variant.get('markers',[])]
    ghosts={};placed={}
    if spec.get('baseline') and index>0:
        # The first variant stays as a faint outline so the reader sees what each change removed.
        for seg in spec['variants'][0].get('segments',[]):
            if seg.get('unknown'):continue
            li=next(i for i,lane in enumerate(lanes)if lane['id']==seg['lane']);y=top+li*row_height
            gx=_scale(float(seg['start']),lo,hi,x0,width);gw=float(seg['duration'])/(hi-lo)*width
            out.append(f'<rect x="{gx:.2f}" y="{y}" width="{gw:.2f}" height="23" rx="3" class="bar-ghost" data-key="ghost-{_esc(seg["id"])}"/>')
            ghosts.setdefault(seg['lane'],[]).append((gx,gx+gw))

    def place_beside(seg,left_edge,right_edge,y,label):
        """Put a label just beside a mark on its own row, clear of bars, ghosts and marker lines."""
        text_width=sum(12 if ord(c)>255 else 6.8 for c in label)
        bounds=[(_scale(float(o['start']),lo,hi,x0,width),_scale(float(o['start'])+float(o.get('duration',0)),lo,hi,x0,width)) for o in variant.get('segments',[]) if o['lane']==seg['lane'] and o is not seg and not o.get('unknown')]
        bounds+=[(mx-3,mx+3) for mx in marker_xs]+ghosts.get(seg['lane'],[])
        free=lambda l,r:l>=x0-4 and r<=limit and all(not(a<r+4 and b>l-4) for a,b in bounds)
        bounds+=placed.get(seg['lane'],[])
        for sx,anchor in [(right_edge+6,'start'),(left_edge-6,'end')]:
            l,r=(sx,sx+text_width) if anchor=='start' else (sx-text_width,sx)
            if free(l,r):
                placed.setdefault(seg['lane'],[]).append((l,r))
                out.append(_svg_text(sx,y+16,label,'external-label',anchor,f"segment-label-{seg['id']}"));return True
        return False

    under_bars=len(out)  # marker lines go here, beneath the bars, so they never cut through a bar's label
    def question_x(seg):
        x=_scale(float(seg['start']),lo,hi,x0,width)
        return x+(11 if any(abs(x-mx)<8 for mx in marker_xs) else 0)  # keep the ? off a marker line
    for seg in variant.get('segments',[]):
        # Reserve every ? first, so a label placed earlier on the row cannot sit where a ? is drawn later.
        if seg.get('unknown'):placed.setdefault(seg['lane'],[]).append((question_x(seg)-9,question_x(seg)+9))
    for seg in variant.get('segments',[]):
        li=next(i for i,lane in enumerate(lanes)if lane['id']==seg['lane']);y=top+li*row_height
        x=_scale(float(seg['start']),lo,hi,x0,width)
        if seg.get('unknown'):
            qx=question_x(seg)
            out.append(_svg_text(qx,y+17,'？','unknown-duration','middle',f"unknown-marker-{seg['id']}"))
            if not place_beside(seg,qx-8,qx+8,y,seg['label']):
                out.append(_svg_wrapped_text(ext_x,y+15,seg['label'],'external-label',f"segment-unknown-{seg['id']}",10))
            continue
        w=float(seg['duration'])/(hi-lo)*width;tone=seg.get('tone') or lanes[li].get('tone') or 'blue'
        start,end=float(seg['start']),float(seg['start'])+float(seg['duration']);unit=spec['unit']
        tip=f"{lanes[li]['label']}: {start:g}〜{end:g}{unit}（{float(seg['duration']):g}{unit}）"
        out.append(f'<rect x="{x:.2f}" y="{y}" width="{w:.2f}" height="23" rx="3" class="bar bar-{tone}" data-key="segment-{_esc(seg["id"])}" data-tip="{_esc(tip)}"/>')
        label=seg.get('label','');text_width=sum(12 if ord(c)>255 else 6.8 for c in label)
        if label and w>=text_width+12:
            out.append(_svg_text(x+w/2,y+16,label,'bar-label','middle',f"segment-label-{seg['id']}"))
        elif label and not place_beside(seg,x,x+w,y,label):
            # Last resort before the crowded value column: keep only the trailing amount ("気づくまで6分" -> "6分").
            short=re.search(r'[約~〜]?[0-9][0-9.,]*\s*[^0-9\s/／・、]{0,3}$',label)
            short=short.group(0) if short and short.group(0)!=label else None
            if short and w>=_text_width(short)+8:
                out.append(_svg_text(x+w/2,y+16,short,'bar-label','middle',f"segment-label-{seg['id']}"))
            elif not (short and place_beside(seg,x,x+w,y,short)):
                external.setdefault(li,[]).append((seg['id'],label))
    for li,labels in external.items():
        # Labels that found no room beside their own bar go, in bar order, just past everything else on the row.
        lane=lanes[li]['id'];text=' / '.join(x[1]for x in labels);text_width=sum(12 if ord(c)>255 else 6.8 for c in text)
        ends=[_scale(float(o['start'])+float(o.get('duration',0)),lo,hi,x0,width) for o in variant.get('segments',[]) if o['lane']==lane and not o.get('unknown')]
        ends+=[mx+3 for mx in marker_xs]+[b for a,b in ghosts.get(lane,[])+placed.get(lane,[])]
        sx=max(ends)+8
        if sx+text_width<=limit:out.append(_svg_text(sx,top+li*row_height+16,text,'external-label','start',f"external-{lane}"))
        else:out.append(_svg_wrapped_text(ext_x,top+li*row_height+15,text,'external-label',f"external-{lane}",10))
    layout,_=_marker_layout(variant.get('markers',[]),lo,hi,x0,width,W)
    for marker in variant.get('markers',[]):
        x,anchor,row=layout[marker['id']];tone=marker.get('tone')or'red';key=_esc(marker['id'])
        out.insert(under_bars,f'<line x1="{x:.2f}" y1="{44+lift}" x2="{x:.2f}" y2="{h-26}" class="marker marker-{tone}" data-key="marker-{key}"/>')
        out.append(_svg_text(x-5 if anchor=='end' else x+5,18+row*17,marker['label'],'marker-label marker-label-'+tone,anchor,f'marker-label-{key}'))
    return ''.join(out)+'</svg>'


def _threshold_svg(spec,prefix,narrow=False):
    lo,hi=float(spec['min']),float(spec['max']);log=spec.get('scale')=='log';h=90+44*len(spec['rows'])
    values=[plain(r['label'])+' '+plain(r.get('value_label') or f"{r['value']:g}{spec['unit']}") for r in spec['rows']]
    desc='、'.join(values+[plain(t['label']) for t in spec.get('thresholds',[])])
    W,x0,width,row_chars=(NARROW_WIDTH,96.0,NARROW_WIDTH-96-74,6) if narrow else (960,210.0,580.0,14)
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" role="img" aria-labelledby="{prefix}-title" aria-describedby="{prefix}-desc"><title id="{prefix}-title">値と閾値</title><desc id="{prefix}-desc">{_esc(desc)}</desc>']
    every=_tick_stride(spec,lo,hi,width,log)
    for ti,tick in enumerate(spec['ticks']):
        value,text=_tick(tick,spec['unit']);x=_scale(value,lo,hi,x0,width,log)
        out.append(f'<line x1="{x:.2f}" y1="42" x2="{x:.2f}" y2="{h-26}" class="axis-grid" data-key="tick-{value:g}"/>')
        if ti%every==0:out.append(_axis_label(x,h-9,text,W,f'tick-label-{value:g}'))
    thresholds=spec.get('thresholds',[]);limit=max(float(t['value'])for t in thresholds)if thresholds else None
    for i,row in enumerate(spec['rows']):
        y=53+i*44;x=_scale(float(row['value']),lo,hi,x0,width,log);tone=row.get('tone','blue')
        out.append(_svg_wrapped_text(x0-16,y+16,row['label'],'lane-label',f"row-label-{row['id']}",row_chars,'end'))
        value_label=row.get('value_label',f"{row['value']:g}{spec['unit']}");tip=f"{row['label']}: {value_label}"
        out.append(f'<rect x="{x0}" y="{y}" width="{max(0,x-x0):.2f}" height="23" rx="3" class="bar bar-{tone}" data-key="row-{_esc(row["id"])}" data-tip="{_esc(tip)}"/>')
        if limit is not None and row['value']>limit:
            tx=_scale(limit,lo,hi,x0,width,log)
            out.append(f'<rect x="{tx:.2f}" y="{y}" width="{x-tx:.2f}" height="23" rx="3" class="bar-excess" data-key="excess-{_esc(row["id"])}"/>')
        out.append(_svg_wrapped_text(x+8,y+15,value_label,'external-label',f"row-value-{row['id']}",10))  # the value sits at the end of its own bar
    layout,_=_marker_layout(thresholds,lo,hi,x0,width,W,log)
    for threshold in thresholds:
        x,anchor,row=layout[threshold['id']];key=_esc(threshold['id']);tone=threshold.get('tone','red')
        out.append(f'<line x1="{x:.2f}" y1="42" x2="{x:.2f}" y2="{h-25}" class="marker marker-{tone}" data-key="threshold-{key}"/>')
        out.append(_svg_text(x-5 if anchor=='end' else x+5,18+17*row,threshold['label'],'marker-label marker-label-'+tone,anchor,f'threshold-label-{key}'))
    return ''.join(out)+'</svg>'


def render_chart(spec: dict[str, Any], prefix: str = "chart", narrow: bool = False) -> list[str]:
    """One SVG per variant. `narrow` lays the same data out for a phone-width viewBox."""
    validate_chart(spec)
    if not isinstance(prefix, str) or not ID_RE.fullmatch(prefix):
        _fail("prefix", "valid identifier required")
    if spec["type"] == "timeline":
        return [_timeline_svg(spec, variant, i, prefix, narrow) for i, variant in enumerate(spec["variants"])]
    return [_threshold_svg(spec, prefix, narrow)]


def has_narrow_layout(spec: dict[str, Any]) -> bool:
    """Grouped timelines need their summary column, so they keep the wide layout and scroll."""
    return spec.get("type") in {"timeline", "threshold"} and not spec.get("groups")
