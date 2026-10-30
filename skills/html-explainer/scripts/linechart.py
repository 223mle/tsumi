"""Line charts for how a quantity changes with another, such as cost against headcount.

Callers pass series of (x, y) points, optional crossing points to annotate,
vertical markers and x ranges. Scales, ticks, direct series labels and the
text alternative come from the data, as in charts.py.
"""
from __future__ import annotations

import re
from typing import Any

from charts import (_axis_label, _esc, _fail, _id, _marker_layout, _num, _svg_text, _text, _text_width,
                    _tick, _tone, choose_ticks, ID_RE, NARROW_WIDTH)
from jawrap import units, plain


def _axis(spec: Any, path: str) -> dict[str, Any]:
    if not isinstance(spec, dict) or set(spec) - {"min", "max", "unit", "ticks", "label"}:
        _fail(path, "min, max and ticks; optional unit and label")
    lo, hi = _num(spec.get("min"), path + ".min"), _num(spec.get("max"), path + ".max")
    if not lo < hi:
        _fail(path, "min must be less than max")
    if "unit" in spec:
        _text(spec["unit"], path + ".unit", required=False)
    ticks = spec.get("ticks")
    if not isinstance(ticks, list) or not 2 <= len(ticks) <= 12:
        _fail(path + ".ticks", "2 to 12 ticks required")
    prev = None
    for i, tick in enumerate(ticks):
        if isinstance(tick, dict) and (set(tick) != {"value", "label"} or not isinstance(tick["label"], str) or len(tick["label"]) > 10):
            _fail(f"{path}.ticks[{i}]", "a number, or value and a label of at most 10 characters")
        v = _num(tick["value"] if isinstance(tick, dict) else tick, f"{path}.ticks[{i}]")
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
        if not isinstance(s, dict) or set(s) - {"id", "label", "tone", "points", "dashed", "dots", "vertices"}:
            _fail(p, "id, label, points; optional tone, dashed, dots, vertices")
        if "vertices" in s and not isinstance(s["vertices"], bool):
            _fail(p + ".vertices", "true or false")
        _id(s.get("id"), p + ".id", ids)
        _text(s.get("label"), p + ".label")
        if len(s["label"]) > 16:
            _fail(p + ".label", "at most 16 characters; it is written at the end of the line")
        if any(o is not s and o.get("label") == s["label"] for o in series[:i]):
            _fail(p + ".label", "another series has the same label, so the reader cannot tell them apart")
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
        for flag in ("dashed", "dots"):
            if flag in s and not isinstance(s[flag], bool):
                _fail(f"{p}.{flag}", "true or false")
        if s.get("dots") and s.get("dashed"):
            _fail(p, "dots draws points without a line; dashed does not apply")
    xlo, xhi, ylo, yhi = float(x["min"]), float(x["max"]), float(y["min"]), float(y["max"])
    for key in ("points", "markers", "bands"):
        if not isinstance(scene.get(key, []), list):
            _fail(f"{path}.{key}", "array required")
    pids: set[str] = set()
    for i, pt in enumerate(scene.get("points", [])):
        p = f"{path}.points[{i}]"
        if not isinstance(pt, dict) or set(pt) - {"id", "x", "y", "label", "tone"} or not {"id", "x", "y", "label"} <= set(pt):
            _fail(p, "id, x, y and label required")
        _id(pt["id"], p + ".id", pids)
        if not (xlo <= _num(pt["x"], p + ".x") <= xhi and ylo <= _num(pt["y"], p + ".y") <= yhi):
            _fail(p, "outside the axes")
        _text(pt["label"], p + ".label"); _tone(pt.get("tone", "red"), p + ".tone")
    mids: set[str] = set()
    for i, m in enumerate(scene.get("markers", [])):
        p = f"{path}.markers[{i}]"
        if not isinstance(m, dict) or set(m) - {"id", "x", "label", "tone"} or not {"id", "x", "label"} <= set(m):
            _fail(p, "id, x and label required")
        _id(m["id"], p + ".id", mids)
        if not xlo <= _num(m["x"], p + ".x") <= xhi:
            _fail(p + ".x", "outside the x axis")
        _text(m["label"], p + ".label"); _tone(m.get("tone", "slate"), p + ".tone")
    bids: set[str] = set()
    for i, b in enumerate(scene.get("bands", [])):
        p = f"{path}.bands[{i}]"
        if not isinstance(b, dict) or set(b) - {"id", "from", "to", "label"} or not {"id", "from", "to", "label"} <= set(b):
            _fail(p, "id, from, to and label required")
        _id(b["id"], p + ".id", bids)
        lo_b, hi_b = _num(b["from"], p + ".from"), _num(b["to"], p + ".to")
        if not lo_b < hi_b or hi_b <= xlo or lo_b >= xhi:
            _fail(p, "from must be less than to, and the range must overlap the x axis")
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


def _line_svg(spec: dict[str, Any], scene: dict[str, Any], index: int, prefix: str, narrow: bool, keep_ticks: set,
              spec_series_names: list[str] = ()) -> str:
    x, y = spec["x"], spec["y"]
    xlo, xhi, ylo, yhi = float(x["min"]), float(x["max"]), float(y["min"]), float(y["max"])
    W = NARROW_WIDTH if narrow else 960
    x0, x1 = (64.0, W - 78.0) if narrow else (110.0, W - 190.0)
    # A unit of two or more characters on every phone tick crowds the gutter; say it once in the axis name instead.
    y_unit = y.get("unit", "")
    unit_in_name = narrow and units(y_unit) > 2
    tick_unit = "" if unit_in_name else y_unit
    y_name = (f"{y['label']}（{y_unit}）" if y.get("label") else y_unit) if unit_in_name else y.get("label")
    x0 = max(x0, 16 + max(_text_width(_tick(t, tick_unit)[1]) for t in y["ticks"]))  # room for the longest y label
    marker_layout, rows = _marker_layout([{"id": m["id"], "value": m["x"], "label": m["label"]} for m in scene.get("markers", [])], xlo, xhi, x0, x1 - x0, W)
    lift = max(0, rows - 1) * 17
    name_row = 16.0 if y_name else 0.0  # a row of its own for the y-axis name, above the plot
    y0, y1 = 40.0 + lift + name_row, (230.0 if narrow else 270.0) + lift + name_row  # plot top and bottom
    H = y1 + 46
    # On the phone layout series names go in a key below the plot, where they cannot sit on a line.
    key_rows = []
    if narrow and len(spec_series_names) > 1:  # one line needs no key: the title and y-axis name already say what it is
        row, used = [], 0.0
        for sr in spec_series_names:
            wd = 26 + _text_width(sr) + 22
            if row and used + wd > W - 8:
                key_rows.append(row); row, used = [], 0.0
            row.append(sr); used += wd
        if row:
            key_rows.append(row)
    x_name_y = H - 6
    key_top = H + (10 if key_rows else 0)  # a clear gap, so the x-axis name does not read as part of the key
    H = key_top + len(key_rows) * 18 + (6 if key_rows else 0)
    px = lambda v: _scale(float(v), xlo, xhi, x0, x1)  # noqa: E731
    py = lambda v: _scale(float(v), ylo, yhi, y1, y0)  # noqa: E731
    title = scene.get("label") or "、".join(plain(s["label"]) for s in scene["series"])
    desc = scene.get("summary") or "、".join(
        [f'{plain(s["label"])}: ' + "→".join(f'{_tick(p[0], x.get("unit", ""))[1]} {_tick(p[1], y.get("unit", ""))[1]}' for p in (s["points"][0], s["points"][-1])) for s in scene["series"]]
        + [plain(p["label"]) for p in scene.get("points", [])])
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" class="dg-line" viewBox="0 0 {W} {H:g}" role="img" aria-labelledby="{prefix}-{index}-title" aria-describedby="{prefix}-{index}-desc">'
           f'<title id="{prefix}-{index}-title">{_esc(title or "折れ線グラフ")}</title><desc id="{prefix}-{index}-desc">{_esc(desc)}</desc>']
    taken = []  # label boxes already drawn; later labels keep clear of them
    def hit(box):
        return any(box[0] < q[2] and box[2] > q[0] and box[1] < q[3] and box[3] > q[1] for q in taken)
    for b in scene.get("bands", []):
        bx0, bx1 = px(max(xlo, float(b["from"]))), px(min(xhi, float(b["to"])))
        out.append(f'<rect class="line-band" x="{bx0:.2f}" y="{y0:g}" width="{bx1 - bx0:.2f}" height="{y1 - y0:g}" data-key="band-{_esc(b["id"])}"/>')
        tw = _text_width(b["label"])
        cxb = min(max((bx0 + bx1) / 2, x0 + tw / 2), x1 - tw / 2)
        for m in scene.get("markers", []):
            # A marker line through the label cuts it in two; slide the label off the line, inside the plot.
            mx = px(m["x"])
            if cxb - tw / 2 - 4 < mx < cxb + tw / 2 + 4:
                cxb = mx - 8 - tw / 2 if mx >= cxb and mx - 8 - tw >= x0 else mx + 8 + tw / 2 if mx + 8 + tw <= x1 else cxb
        ty = next((t for t in (y0 + 14, y0 + 32, y0 + 50) if not hit((cxb - tw / 2, t - 12, cxb + tw / 2, t + 3))), y0 + 14)
        out.append(_svg_text(cxb, ty, b["label"], "band-label", "middle", f"band-label-{b['id']}"))
        taken.append((cxb - tw / 2, ty - 12, cxb + tw / 2, ty + 3))
    # Tick labels that would touch are thinned, but ticks at a marked point or marker are kept first.
    # keep_ticks is the same for every variant, so tick labels do not jump when switching.
    ticks = [_tick(t, x.get("unit", "")) for t in x["ticks"]]
    named = {float(t["value"]) for t in x["ticks"] if isinstance(t, dict) and t.get("label")}
    keep = choose_ticks(ticks, px, W, keep_ticks, named)
    for v, text in ticks:
        gx = px(v)
        out.append(f'<line class="axis-grid" x1="{gx:.2f}" y1="{y0:g}" x2="{gx:.2f}" y2="{y1:g}" data-key="xtick-{v:g}"/>')
        if v in keep:
            out.append(_axis_label(gx, y1 + 18, text, W, f"xtick-label-{v:g}"))
    taken.append((0, y1 + 2, W, H))  # the x tick labels and the axis name below the plot
    for t in y["ticks"]:
        v, text = _tick(t, tick_unit)
        gy = py(v)
        out.append(f'<line class="axis-grid" x1="{x0:g}" y1="{gy:.2f}" x2="{x1:g}" y2="{gy:.2f}" data-key="ytick-{v:g}"/>')
        out.append(_svg_text(x0 - 8, gy + 4, text, "axis-label", "end", f"ytick-label-{v:g}"))
    if x.get("label"):
        out.append(_svg_text((x0 + x1) / 2, x_name_y, x["label"], "axis-label", "middle", "x-axis-label"))
    if y_name:
        # Just above the plot and below the marker labels, from the left edge so a long name is never cut off.
        out.append(_svg_text(4, y0 - 14, y_name, "axis-label", "start", "y-axis-label"))
        taken.append((4, y0 - 26, 4 + _text_width(y_name), y0 - 11))
    for m in scene.get("markers", []):
        mx, anchor, row = marker_layout[m["id"]]
        tone = m.get("tone", "slate")
        out.append(f'<line class="marker marker-{tone}" x1="{mx:.2f}" y1="{y0 - 4:g}" x2="{mx:.2f}" y2="{y1:g}" data-key="marker-{_esc(m["id"])}"/>')
        out.append(_svg_text(mx - 5 if anchor == "end" else mx + 5, 18 + row * 17, m["label"], f"marker-label marker-label-{tone}", anchor, f"marker-label-{m['id']}"))
        tw = _text_width(m["label"])
        taken.append((mx - 5 - tw, 6 + row * 17, mx - 5, 21 + row * 17) if anchor == "end" else (mx + 5, 6 + row * 17, mx + 5 + tw, 21 + row * 17))
    # Series names go after each line's end, or, without room there (phone layout), above its start.
    # Each group is spread so that no two names touch, then kept inside the plot.
    groups: dict[str, list] = {"end": [], "start": []}
    for s in ([] if narrow else scene["series"]):
        end_x = px(s["points"][-1][0])
        at_end = end_x + 30 + _text_width(s["label"]) <= W - 4
        groups["end" if at_end else "start"].append((py(s["points"][-1][1]) if at_end else py(s["points"][0][1]) - 12, s))
    label_at = {}
    for where, items in groups.items():
        items.sort(key=lambda e: e[0])
        ys = []
        for want, _ in items:
            ys.append(max(want, ys[-1] + 16) if ys else want)
        overflow = (ys[-1] - (y1 - 4)) if ys else 0
        if overflow > 0:
            ys = [v - overflow for v in ys]
        ys = [max(v, y0 + 2) for v in ys]
        for (_, s), ly in zip(items, ys):
            lx = px(s["points"][-1][0]) if where == "end" else px(s["points"][0][0]) - 18
            label_at[s["id"]] = (lx, ly)
    if narrow:
        positions = {}
        for r, row in enumerate(key_rows):
            cx = 8.0
            for name in row:
                positions[name] = (cx - 6, key_top + 6 + r * 18)
                cx += 26 + _text_width(name) + 22
        for s in scene["series"]:
            if s["label"] in positions:
                label_at[s["id"]] = positions[s["label"]]
    for s in sorted(scene["series"], key=lambda s: bool(s.get("dots"))):  # data dots on top of fitted lines
        tone = s.get("tone") or "blue"
        d = "M" + " L".join(f"{px(p[0]):.2f} {py(p[1]):.2f}" for p in s["points"])
        # Always state the dash, so switching to a solid variant clears it.
        dash = f' stroke-dasharray="{"6 4" if s.get("dashed") else "none"}"'
        cls = "line-series line-series-dots" if s.get("dots") else "line-series"  # dots: the path is kept, unstroked, for morphing
        out.append(f'<path class="{cls} dg-tone-{tone}" d="{d}"{dash} data-key="series-{_esc(s["id"])}"/>')
        if s["id"] in label_at:
            lx, ly = label_at[s["id"]]
            key_cls = "series-key series-key-dots" if s.get("dots") else "series-key"
            out.append(f'<path class="{key_cls} dg-tone-{tone}" d="M{lx + 6:.2f} {ly:.2f}h16"{dash} data-key="series-key-{_esc(s["id"])}"/>')
            out.append(_svg_text(lx + 26, ly + 4, s["label"], f"series-label series-label-{tone}", "start", f"series-label-{s['id']}"))
            taken.append((lx + 6, ly - 8, lx + 26 + _text_width(s["label"]), ly + 8))
        for p in ([] if s.get("vertices") is False else s.get("shown", s["points"])):
            tip = f'{plain(s["label"])}: {_tick(p[0], x.get("unit", ""))[1]} → {_tick(p[1], y.get("unit", ""))[1]}'
            dot = ' line-dot" r="5' if s.get("dots") else '" r="3.5'
            out.append(f'<circle class="line-point dg-tone-{tone}{dot}" cx="{px(p[0]):.2f}" cy="{py(p[1]):.2f}" data-tip="{_esc(tip)}" data-key="pt-{_esc(s["id"])}-{p[0]:g}"/>')
    line_samples = []  # points along every series, every few pixels, for label placement
    for s in scene["series"]:
        for a, b in zip(s["points"], s["points"][1:]):
            ax, ay, bx, by = px(a[0]), py(a[1]), px(b[0]), py(b[1])
            n = max(1, int(max(abs(bx - ax), abs(by - ay)) / 4))
            line_samples += [(ax + (bx - ax) * k / n, ay + (by - ay) * k / n) for k in range(n + 1)]
    for p in scene.get("points", []):
        tone = p.get("tone") or _series_tone_at(scene["series"], p, yhi - ylo)
        cx, cy = px(p["x"]), py(p["y"])
        tw = _text_width(p["label"])
        def fits(lx, ty, avoid_lines):
            box = (lx - tw / 2, ty - 12, lx + tw / 2, ty + 3)
            if box[0] < 4 or box[2] > W - 4 or box[1] < 4 or box[3] > y1 - 2:
                return False
            if hit(box):
                return False
            return not avoid_lines or not any(box[0] - 2 <= sx <= box[2] + 2 and box[1] - 2 <= sy <= box[3] + 2 for sx, sy in line_samples)
        mid = min(max(cx, x0 + tw / 2), x1 - tw / 2)
        r, l = cx + 12 + tw / 2, cx - 12 - tw / 2
        spots = [(mid, cy - 28, True), (mid, cy + 36, False), (r, cy + 4, None), (l, cy + 4, None), (l, cy - 22, None), (r, cy - 22, None),
                 (l, cy + 30, None), (r, cy + 30, None), (mid, cy - 50, True), (mid, cy + 58, False), (mid, cy - 72, True), (mid, cy + 80, False)]
        # First keep clear of lines and labels; then take the spot that touches the lines least; never sit on another label.
        def line_hits(sp):
            l, r, t, b = sp[0] - tw / 2 - 2, sp[0] + tw / 2 + 2, sp[1] - 14, sp[1] + 5
            return sum(1 for sx, sy in line_samples if l <= sx <= r and t <= sy <= b)
        clear_spot = next((sp for sp in spots if fits(sp[0], sp[1], True)), None)
        loose = [sp for sp in spots if fits(sp[0], sp[1], False)]
        lx, ty, above = clear_spot or (min(loose, key=line_hits) if loose else spots[0])
        if above is None:  # beside the point: a short horizontal leader to the label's near edge
            edge_x = lx - tw / 2 - 3 if lx > cx else lx + tw / 2 + 3
            leader = f'<path d="M{cx + (8 if lx > cx else -8):.2f} {cy:.2f}L{edge_x:.2f} {ty - 4:.2f}" data-key="callout-{_esc(p["id"])}-leader"/>'
        else:
            leader = f'<path d="M{cx:.2f} {cy - 8 if above else cy + 8:.2f}V{ty + 4 if above else ty - 16:.2f}" data-key="callout-{_esc(p["id"])}-leader"/>'
        out.append(f'<g class="line-callout dg-tone-{tone}" data-key="callout-{_esc(p["id"])}"><circle cx="{cx:.2f}" cy="{cy:.2f}" r="6" data-key="callout-{_esc(p["id"])}-dot"/>{leader}</g>')
        out.append(_svg_text(lx, ty, p["label"], f"callout-label marker-label-{tone}", "middle", f"callout-label-{p['id']}"))
        taken.append((lx - tw / 2, ty - 12, lx + tw / 2, ty + 3))
    return "".join(out) + "</svg>"


def _resample(points, xs):
    """Linear interpolation of a polyline at the given x values inside its own range."""
    pts = [(float(a), float(b)) for a, b in points]
    out = []
    for x in sorted(v for v in xs if pts[0][0] <= v <= pts[-1][0]):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            if ax <= x <= bx:
                out.append([x, ay + (by - ay) * ((x - ax) / (bx - ax) if bx != ax else 0)])
                break
    return out


def _series_tone_at(series, point, y_span):
    """The colour of the one line a note sits on; red when it sits on none or where lines cross (a break-even)."""
    hits = []
    for s in series:
        pts = s["points"]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            if ax <= point["x"] <= bx:
                y = ay if bx == ax else ay + (by - ay) * (point["x"] - ax) / (bx - ax)
                if abs(y - point["y"]) <= 0.02 * y_span:
                    hits.append(s.get("tone") or "blue")
                break
    return hits[0] if len(hits) == 1 else "red"


def render_line(spec: Any, prefix: str = "line", narrow: bool = False) -> list[str]:
    """One SVG per variant (or one for a single scene); `narrow` gives the phone layout."""
    data = validate_line(spec)
    safe = re.sub(r"[^A-Za-z0-9_-]", "-", prefix)
    if not ID_RE.fullmatch(safe):
        _fail("prefix", "valid identifier required")
    base = {k: data[k] for k in ("series", "points", "markers", "bands") if k in data}
    scenes = [{**base, **v} for v in data["variants"]] if "variants" in data else [base]
    # The same series must have the same number of vertices in every variant for the path to morph,
    # so each copy is resampled at the union of its x values; only the given points get dots.
    xs_by_id: dict[str, set] = {}
    for sc in scenes:
        for s in sc["series"]:
            xs_by_id.setdefault(s["id"], set()).update(float(p[0]) for p in s["points"])
    for sc in scenes:
        sc["series"] = [{**s, "shown": s["points"], "points": _resample(s["points"], xs_by_id[s["id"]])} for s in sc["series"]]
    keep_ticks = {float(p["x"]) for sc in scenes for p in sc.get("points", [])} | {float(m["x"]) for sc in scenes for m in sc.get("markers", [])}
    names = list(dict.fromkeys(s["label"] for sc in scenes for s in sc["series"]))  # one key layout for every variant
    return [_line_svg(data, scene, i, safe, narrow, keep_ticks, names) for i, scene in enumerate(scenes)]
