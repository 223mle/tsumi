"""Line charts for how a quantity changes with another, such as cost against headcount.

Callers pass series of (x, y) points, optional crossing points to annotate,
vertical markers and x ranges. Scales, ticks, direct series labels and the
text alternative come from the data, as in charts.py.
"""
from __future__ import annotations

import re
from typing import Any

from charts import (_axis_label, _esc, _fail, _id, _marker_layout, _num, _svg_text, _text, _text_width,
                    _tick, _tick_stride, _tone, ID_RE, NARROW_WIDTH)
from jawrap import plain


def _axis(spec: Any, path: str) -> dict[str, Any]:
    if not isinstance(spec, dict) or set(spec) - {"min", "max", "unit", "ticks", "label"}:
        _fail(path, "min, max, unit, ticks and an optional label required")
    lo, hi = _num(spec.get("min"), path + ".min"), _num(spec.get("max"), path + ".max")
    if not lo < hi:
        _fail(path, "min must be less than max")
    _text(spec.get("unit"), path + ".unit", required=False)
    ticks = spec.get("ticks")
    if not isinstance(ticks, list) or not 2 <= len(ticks) <= 12:
        _fail(path + ".ticks", "2 to 12 ticks required")
    prev = None
    for i, tick in enumerate(ticks):
        value = tick["value"] if isinstance(tick, dict) else tick
        if isinstance(tick, dict) and (set(tick) != {"value", "label"} or not isinstance(tick["label"], str) or len(tick["label"]) > 10):
            _fail(f"{path}.ticks[{i}]", "a number, or value and a label of at most 10 characters")
        v = _num(value, f"{path}.ticks[{i}]")
        if not lo <= v <= hi or (prev is not None and v <= prev):
            _fail(f"{path}.ticks[{i}]", "ticks must be increasing and inside the axis")
        prev = v
    if "label" in spec:
        _text(spec["label"], path + ".label")
    return spec


def _scene(spec: dict[str, Any], scene: dict[str, Any], path: str, x: dict[str, Any], y: dict[str, Any]) -> None:
    series = scene.get("series")
    if not isinstance(series, list) or not 1 <= len(series) <= 4:
        _fail(path + ".series", "1 to 4 series required")
    ids: set[str] = set()
    for i, s in enumerate(series):
        p = f"{path}.series[{i}]"
        if not isinstance(s, dict) or set(s) - {"id", "label", "tone", "points", "dashed"}:
            _fail(p, "id, label, points; optional tone, dashed")
        _id(s.get("id"), p + ".id", ids)
        _text(s.get("label"), p + ".label")
        if len(s["label"]) > 16:
            _fail(p + ".label", "at most 16 characters; it is written at the end of the line")
        _tone(s.get("tone"), p + ".tone")
        pts = s.get("points")
        if not isinstance(pts, list) or len(pts) < 2:
            _fail(p + ".points", "at least two [x, y] points")
        last = None
        for j, pt in enumerate(pts):
            if not isinstance(pt, list) or len(pt) != 2:
                _fail(f"{p}.points[{j}]", "[x, y] required")
            px, py = _num(pt[0], f"{p}.points[{j}][0]"), _num(pt[1], f"{p}.points[{j}][1]")
            if not (float(x["min"]) <= px <= float(x["max"]) and float(y["min"]) <= py <= float(y["max"])):
                _fail(f"{p}.points[{j}]", "outside the axes")
            if last is not None and px <= last:
                _fail(f"{p}.points[{j}]", "x must increase")
            last = px
        if "dashed" in s and not isinstance(s["dashed"], bool):
            _fail(p + ".dashed", "true or false")
    for i, pt in enumerate(scene.get("points", [])):
        p = f"{path}.points[{i}]"
        if not isinstance(pt, dict) or set(pt) - {"id", "x", "y", "label", "tone"} or not {"id", "x", "y", "label"} <= set(pt):
            _fail(p, "id, x, y and label required")
        _num(pt["x"], p + ".x"); _num(pt["y"], p + ".y"); _text(pt["label"], p + ".label")
        _tone(pt.get("tone", "red"), p + ".tone")
    for i, m in enumerate(scene.get("markers", [])):
        p = f"{path}.markers[{i}]"
        if not isinstance(m, dict) or set(m) - {"id", "x", "label", "tone"} or not {"id", "x", "label"} <= set(m):
            _fail(p, "id, x and label required")
        _num(m["x"], p + ".x"); _text(m["label"], p + ".label"); _tone(m.get("tone", "slate"), p + ".tone")
    for i, b in enumerate(scene.get("bands", [])):
        p = f"{path}.bands[{i}]"
        if not isinstance(b, dict) or set(b) - {"id", "from", "to", "label"} or not {"id", "from", "to", "label"} <= set(b):
            _fail(p, "id, from, to and label required")
        if not _num(b["from"], p + ".from") < _num(b["to"], p + ".to"):
            _fail(p, "from must be less than to")
        _text(b["label"], p + ".label")


def validate_line(spec: Any) -> dict[str, Any]:
    if not isinstance(spec, dict) or spec.get("type") != "line":
        _fail("line", "type line required")
    extra = set(spec) - {"type", "x", "y", "series", "points", "markers", "bands", "variants"}
    if extra:
        _fail("line", f"unknown fields {sorted(extra)}")
    x, y = _axis(spec.get("x"), "line.x"), _axis(spec.get("y"), "line.y")
    variants = spec.get("variants")
    if variants is None:
        _scene(spec, spec, "line", x, y)
    else:
        if not isinstance(variants, list) or not variants:
            _fail("line.variants", "non-empty array required")
        for i, v in enumerate(variants):
            if not isinstance(v, dict) or set(v) - {"label", "series", "points", "markers", "bands", "summary"}:
                _fail(f"line.variants[{i}]", "label and series; optional points, markers, bands, summary")
            _text(v.get("label"), f"line.variants[{i}].label")
            _scene(spec, {**{k: spec[k] for k in ("series", "points", "markers", "bands") if k in spec}, **v}, f"line.variants[{i}]", x, y)
    return spec


def _scale(v: float, lo: float, hi: float, a: float, b: float) -> float:
    return a + (v - lo) / (hi - lo) * (b - a)


def _line_svg(spec: dict[str, Any], scene: dict[str, Any], index: int, prefix: str, narrow: bool) -> str:
    x, y = spec["x"], spec["y"]
    xlo, xhi, ylo, yhi = float(x["min"]), float(x["max"]), float(y["min"]), float(y["max"])
    W = NARROW_WIDTH if narrow else 960
    x0, x1 = (64.0, W - 78.0) if narrow else (110.0, W - 190.0)
    marker_layout, rows = _marker_layout([{"id": m["id"], "value": m["x"], "label": m["label"]} for m in scene.get("markers", [])], xlo, xhi, x0, x1 - x0, W)
    lift = max(0, rows - 1) * 17
    y0, y1 = 40.0 + lift, (230.0 if narrow else 270.0) + lift  # plot top and bottom
    H = y1 + 46
    px = lambda v: _scale(float(v), xlo, xhi, x0, x1)  # noqa: E731
    py = lambda v: _scale(float(v), ylo, yhi, y1, y0)  # noqa: E731
    title = scene.get("label", "")
    desc = scene.get("summary") or "、".join(
        [f'{plain(s["label"])}: ' + "→".join(f'{_tick(p[0], x.get("unit", ""))[1]} {_tick(p[1], y.get("unit", ""))[1]}' for p in (s["points"][0], s["points"][-1])) for s in scene["series"]]
        + [plain(p["label"]) for p in scene.get("points", [])])
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" class="dg-line" viewBox="0 0 {W} {H:g}" role="img" aria-labelledby="{prefix}-{index}-title" aria-describedby="{prefix}-{index}-desc">'
           f'<title id="{prefix}-{index}-title">{_esc(title or "折れ線グラフ")}</title><desc id="{prefix}-{index}-desc">{_esc(desc)}</desc>']
    taken = []  # label boxes already drawn, for the callouts to avoid
    for b in scene.get("bands", []):
        bx0, bx1 = px(max(xlo, float(b["from"]))), px(min(xhi, float(b["to"])))
        out.append(f'<rect class="line-band" x="{bx0:.2f}" y="{y0:g}" width="{bx1 - bx0:.2f}" height="{y1 - y0:g}" data-key="band-{_esc(b["id"])}"/>')
        out.append(_svg_text((bx0 + bx1) / 2, y0 + 14, b["label"], "band-label", "middle", f"band-label-{b['id']}"))
        tw = _text_width(b["label"]); taken.append(((bx0 + bx1 - tw) / 2, y0 + 2, (bx0 + bx1 + tw) / 2, y0 + 18))
    xs = {"ticks": x["ticks"], "unit": x.get("unit", "")}
    every = _tick_stride(xs, xlo, xhi, x1 - x0)
    for i, t in enumerate(x["ticks"]):
        v, text = _tick(t, x.get("unit", ""))
        gx = px(v)
        out.append(f'<line class="axis-grid" x1="{gx:.2f}" y1="{y0:g}" x2="{gx:.2f}" y2="{y1:g}" data-key="xtick-{v:g}"/>')
        if i % every == 0:
            out.append(_axis_label(gx, y1 + 18, text, W, f"xtick-label-{v:g}"))
    for t in y["ticks"]:
        v, text = _tick(t, y.get("unit", ""))
        gy = py(v)
        out.append(f'<line class="axis-grid" x1="{x0:g}" y1="{gy:.2f}" x2="{x1:g}" y2="{gy:.2f}" data-key="ytick-{v:g}"/>')
        out.append(_svg_text(x0 - 8, gy + 4, text, "axis-label", "end", f"ytick-label-{v:g}"))
    if x.get("label"):
        out.append(_svg_text((x0 + x1) / 2, H - 6, x["label"], "axis-label", "middle", "x-axis-label"))
    if y.get("label"):
        out.append(_svg_text(x0 - 8, y0 - 14 - lift, y["label"], "axis-label", "end", "y-axis-label"))
    for m in scene.get("markers", []):
        mx, anchor, row = marker_layout[m["id"]]
        tone = m.get("tone", "slate")
        out.append(f'<line class="marker marker-{tone}" x1="{mx:.2f}" y1="{y0 - 4:g}" x2="{mx:.2f}" y2="{y1:g}" data-key="marker-{_esc(m["id"])}"/>')
        out.append(_svg_text(mx - 5 if anchor == "end" else mx + 5, 18 + row * 17, m["label"], f"marker-label marker-label-{tone}", anchor, f"marker-label-{m['id']}"))
    # Series are labelled at their right end; labels that would touch are pushed apart vertically.
    ends = sorted(((py(s["points"][-1][1]), s) for s in scene["series"]), key=lambda e: e[0])
    placed: list[float] = []
    label_y = {}
    for ey, s in ends:
        ly = max(ey, placed[-1] + 16) if placed else ey
        placed.append(ly)
        label_y[s["id"]] = ly
    for s in scene["series"]:
        tone = s.get("tone") or "blue"
        d = "M" + " L".join(f"{px(p[0]):.2f} {py(p[1]):.2f}" for p in s["points"])
        dash = ' stroke-dasharray="6 4"' if s.get("dashed") else ""
        out.append(f'<path class="line-series dg-tone-{tone}" d="{d}"{dash} data-key="series-{_esc(s["id"])}"/>')
        lx, ly = px(s["points"][-1][0]), label_y[s["id"]]
        if lx + 30 + _text_width(s["label"]) > W - 4:
            # No room after the line's end (phone layout): label it above its first point instead.
            lx, ly = px(s["points"][0][0]) - 18, py(s["points"][0][1]) - 12
        out.append(f'<path class="series-key dg-tone-{tone}" d="M{lx + 6:.2f} {ly:.2f}h16"{dash} data-key="series-key-{_esc(s["id"])}"/>')
        out.append(_svg_text(lx + 26, ly + 4, s["label"], f"series-label series-label-{tone}", "start", f"series-label-{s['id']}"))
        taken.append((lx + 6, ly - 8, lx + 26 + _text_width(s["label"]), ly + 8))
        for p in s["points"]:
            tip = f'{plain(s["label"])}: {_tick(p[0], x.get("unit", ""))[1]} → {_tick(p[1], y.get("unit", ""))[1]}'
            out.append(f'<circle class="line-point dg-tone-{tone}" cx="{px(p[0]):.2f}" cy="{py(p[1]):.2f}" r="3.5" data-tip="{_esc(tip)}" data-key="pt-{_esc(s["id"])}-{p[0]:g}"/>')
    line_samples = []  # points along every series, every few pixels, for label placement
    for s in scene["series"]:
        for a, b in zip(s["points"], s["points"][1:]):
            ax, ay, bx, by = px(a[0]), py(a[1]), px(b[0]), py(b[1])
            n = max(1, int(max(abs(bx - ax), abs(by - ay)) / 4))
            line_samples += [(ax + (bx - ax) * k / n, ay + (by - ay) * k / n) for k in range(n + 1)]
    for p in scene.get("points", []):
        tone = p.get("tone", "red")
        cx, cy = px(p["x"]), py(p["y"])
        tw = _text_width(p["label"])
        # Try above, below, right and left of the point; keep clear of other labels and of every line.
        def clear(lx, ty):
            l, r, t, b = lx - tw / 2, lx + tw / 2, ty - 12, ty + 3
            if l < x0 - 4 or r > W - 4 or t < 4:
                return False
            return not any(l < q[2] and r > q[0] and t < q[3] and b > q[1] for q in taken) and \
                not any(l - 2 <= sx <= r + 2 and t - 2 <= sy <= b + 2 for sx, sy in line_samples)
        mid = min(max(cx, x0 + tw / 2), x1 - tw / 2)
        spots = [(mid, cy - 28, True), (mid, cy + 36, False), (cx + 12 + tw / 2, cy + 4, None), (cx - 12 - tw / 2, cy + 4, None),
                 (cx - 12 - tw / 2, cy - 22, None), (cx + 12 + tw / 2, cy - 22, None), (cx - 12 - tw / 2, cy + 30, None),
                 (cx + 12 + tw / 2, cy + 30, None), (mid, cy - 50, True), (mid, cy + 58, False)]
        lx, ty, above = next((sp for sp in spots if clear(sp[0], sp[1])), spots[0])
        leader = "" if above is None else f'<path d="M{cx:.2f} {cy - 8 if above else cy + 8:.2f}V{cy - 22 if above else cy + 22:.2f}" data-key="callout-{_esc(p["id"])}-leader"/>'
        out.append(f'<g class="line-callout dg-tone-{tone}" data-key="callout-{_esc(p["id"])}"><circle cx="{cx:.2f}" cy="{cy:.2f}" r="6" data-key="callout-{_esc(p["id"])}-dot"/>{leader}</g>')
        out.append(_svg_text(lx, ty, p["label"], f"callout-label marker-label-{tone}", "middle", f"callout-label-{p['id']}"))
        taken.append((lx - tw / 2, ty - 12, lx + tw / 2, ty + 3))
    return "".join(out) + "</svg>"


def render_line(spec: Any, prefix: str = "line", narrow: bool = False) -> list[str]:
    """One SVG per variant (or one for a single scene); `narrow` gives the phone layout."""
    data = validate_line(spec)
    safe = re.sub(r"[^A-Za-z0-9_-]", "-", prefix)
    if not ID_RE.fullmatch(safe):
        _fail("prefix", "valid identifier required")
    base = {k: data[k] for k in ("series", "points", "markers", "bands") if k in data}
    scenes = [{**base, **v} for v in data["variants"]] if "variants" in data else [base]
    return [_line_svg(data, scene, i, safe, narrow) for i, scene in enumerate(scenes)]
