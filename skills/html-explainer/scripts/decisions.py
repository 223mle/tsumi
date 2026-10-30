"""A compact two-track decision overview; content stays separate from layout."""
import sys as _sys
from html import escape
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent))  # loadable by file path as well as by name
from jawrap import wrap  # noqa: E402

# (field, CSS class, line height, gap after) in reading order
ROWS = (("eyebrow", "axis-label", 16, 10), ("title", "group-label", 20, 16), ("item0", "lane-label", 19, 8),
        ("item1", "lane-label", 19, 18), ("footer", "group-label", 20, 0))


def _validate(spec):
    if not isinstance(spec, dict) or set(spec) - {'type', 'columns'} or not isinstance(spec.get('columns'), list) or len(spec['columns']) != 2:
        raise ValueError('decision: exactly two columns required')
    for col in spec['columns']:
        if not isinstance(col, dict) or set(col) - {'title', 'eyebrow', 'items', 'footer'}:
            raise ValueError('decision column: unknown fields')
        for k in ('title', 'eyebrow', 'footer'):
            if not isinstance(col.get(k), str) or len(col[k]) > 45:
                raise ValueError(f'decision.{k}: short text required')
        items = col.get('items')
        if not isinstance(items, list) or len(items) != 2 or not all(isinstance(s, str) and len(s) < 35 for s in items):
            raise ValueError('decision.items: two short labels required')


def _lines(col, width):
    """Each field wrapped to the column width; 13px text is about 6.5px per unit."""
    values = {"eyebrow": col["eyebrow"], "title": col["title"], "item0": col["items"][0], "item1": col["items"][1], "footer": col["footer"]}
    out = {}
    for field, *_ in ROWS:
        lines = wrap(values[field], int((width - 48) / 6.8), 3)
        if lines is None:
            raise ValueError(f'decision.{field}: too long for the column; shorten it')
        out[field] = lines
    return out


def _height(lines):
    return 30 + sum(len(lines[f]) * lh + gap for f, _, lh, gap in ROWS) + 14


def render_decision(spec, prefix, narrow=False):
    """Two columns side by side, or stacked on the phone layout."""
    _validate(spec)
    W = 420 if narrow else 960
    col_w = W - 24 if narrow else (W - 24 - 20) / 2
    texts = [_lines(col, col_w) for col in spec['columns']]
    heights = [_height(t) for t in texts]
    box_h = max(heights)
    H = (heights[0] + heights[1] + 36) if narrow else box_h + 16
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:g}" role="img" aria-label="対応方針の比較"><title>対応方針の比較</title>']
    for i, (col, lines) in enumerate(zip(spec['columns'], texts)):
        tone = 'blue' if i == 0 else 'violet'
        x, top = (12, 8 + i * (heights[0] + 20)) if narrow else (12 + i * (col_w + 20), 8)
        h = heights[i] if narrow else box_h
        out.append(f'<rect x="{x:g}" y="{top:g}" width="{col_w:g}" height="{h:g}" rx="8" class="group-band group-{tone}" data-key="column-{i}"/>')
        y = top + 26
        for j, (field, cls, lh, gap) in enumerate(ROWS):
            spans = ''.join(f'<tspan x="{x + 24:g}" dy="{0 if k == 0 else lh}">{escape(line)}</tspan>' for k, line in enumerate(lines[field]))
            out.append(f'<text x="{x + 24:g}" y="{y:g}" class="{cls}" data-label="true" data-key="column-{i}-text-{j}">{spans}</text>')
            y += len(lines[field]) * lh + gap
    return [''.join(out) + '</svg>']
