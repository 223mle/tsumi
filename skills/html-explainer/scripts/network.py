"""Semantic network diagrams for compact, accessible explanatory pages.

Callers describe a small grid of named nodes and semantic edges.  This module
owns the geometry, routing and SVG accessibility details so content authors do
not have to guess pixel coordinates.
"""
from __future__ import annotations

import html
import math
import re
from typing import Any

import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent))  # loadable by file path as well as by name
from jawrap import plain, units, wrap

ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
TONES = {"blue", "teal", "violet", "amber", "rose", "slate", "red"}
KINDS = {"request", "file", "conflict"}
ROUTES = {"direct", "above", "below"}


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _fail(path: str, message: str) -> None:
    raise ValueError(f"{path}: {message}")


def _id(value: object, path: str, seen: set[str]) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        _fail(path, "must be an identifier beginning with a letter")
    if value in seen:
        _fail(path, f"duplicate id {value}")
    seen.add(value)
    return value


def _text(value: object, path: str, required: bool = True) -> str:
    if not isinstance(value, str) or (required and not value.strip()):
        _fail(path, "must be a non-empty string")
    return value


def _tone(value: object, path: str, default: str) -> str:
    value = default if value is None else value
    if not isinstance(value, str) or value not in TONES:
        _fail(path, f"must be one of {sorted(TONES)}")
    return value


def validate_network(spec: object) -> dict[str, Any]:
    """Validate and return a network specification.

    The accepted shape deliberately contains semantic grid positions only. A
    caller cannot supply SVG coordinates, paths, styles or HTML.
    """
    if not isinstance(spec, dict):
        _fail("network", "must be an object")
    allowed = {"type", "columns", "rows", "nodes", "boundaries", "variants", "edges", "marks"}
    extra = set(spec) - allowed
    if extra:
        _fail("network", f"unknown fields {sorted(extra)}")
    if "marks" in spec and "edges" not in spec:
        _fail("network.marks", "top-level marks need numbered edges; put marks in each variant otherwise")
    if "edges" in spec:
        spec = _expand_steps(spec)
    if spec.get("type") != "network":
        _fail("network.type", "must be network")
    columns, rows = spec.get("columns"), spec.get("rows")
    if columns not in (3, 4) or rows not in (2, 3):
        _fail("network.grid", "columns must be 3 or 4 and rows must be 2 or 3")
    nodes = spec.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        _fail("network.nodes", "must be a non-empty array")
    ids: set[str] = set()
    occupied: set[tuple[int, int]] = set()
    node_map: dict[str, dict[str, Any]] = {}
    for i, node in enumerate(nodes):
        path = f"network.nodes[{i}]"
        if not isinstance(node, dict):
            _fail(path, "must be an object")
        if set(node) - {"id", "label", "detail", "column", "row", "tone"}:
            _fail(path, "unknown fields")
        nid = _id(node.get("id"), path + ".id", ids)
        label = _text(node.get("label"), path + ".label")
        detail = node.get("detail", "")
        if not isinstance(detail, str):
            _fail(path + ".detail", "must be a string")
        column, row = node.get("column"), node.get("row")
        if not isinstance(column, int) or isinstance(column, bool) or not 1 <= column <= columns:
            _fail(path + ".column", "must be inside the grid")
        if not isinstance(row, int) or isinstance(row, bool) or not 1 <= row <= rows:
            _fail(path + ".row", "must be inside the grid")
        if (column, row) in occupied:
            _fail(path, f"grid cell ({column}, {row}) is already occupied")
        occupied.add((column, row))
        tone = _tone(node.get("tone"), path + ".tone", "slate")
        if len(label) > 48 or len(detail) > 72:
            _fail(path, "label/detail is too long for a compact diagram")
        node_map[nid] = {"id": nid, "label": label, "detail": detail,
                         "column": column, "row": row, "tone": tone}
    boundaries = spec.get("boundaries", [])
    if not isinstance(boundaries, list):
        _fail("network.boundaries", "must be an array")
    boundary_ids: set[str] = set()
    for i, boundary in enumerate(boundaries):
        path = f"network.boundaries[{i}]"
        if not isinstance(boundary, dict):
            _fail(path, "must be an object")
        if set(boundary) - {"id", "label", "node_ids", "tone"}:
            _fail(path, "unknown fields")
        bid = _id(boundary.get("id"), path + ".id", ids | boundary_ids)
        boundary_ids.add(bid)
        label = _text(boundary.get("label"), path + ".label")
        if len(label) > 48:
            _fail(path + ".label", "too long for a compact diagram")
        member_ids = boundary.get("node_ids")
        if not isinstance(member_ids, list) or not member_ids:
            _fail(path + ".node_ids", "must be a non-empty array")
        if any(not isinstance(n, str) for n in member_ids):
            _fail(path + ".node_ids", "must contain string node ids once each")
        if len(set(member_ids)) != len(member_ids) or any(n not in node_map for n in member_ids):
            _fail(path + ".node_ids", "must contain existing node ids once each")
        _tone(boundary.get("tone"), path + ".tone", "violet")
    variants = spec.get("variants")
    if not isinstance(variants, list) or not variants:
        _fail("network.variants", "must be a non-empty array")
    variant_ids: set[str] = set()
    for vi, variant in enumerate(variants):
        path = f"network.variants[{vi}]"
        if not isinstance(variant, dict):
            _fail(path, "must be an object")
        if set(variant) - {"label", "active_nodes", "edges", "note", "step", "marks", "hidden_nodes"}:
            _fail(path, "unknown fields")
        hidden = variant.get("hidden_nodes", [])
        if not isinstance(hidden, list) or any(not isinstance(n, str) or n not in node_map for n in hidden):
            _fail(path + ".hidden_nodes", "must contain existing node ids")
        marks = variant.get("marks", [])
        if not isinstance(marks, list) or len(marks) > 3:
            _fail(path + ".marks", "up to 3 marks")
        for mi, mark in enumerate(marks):
            if (not isinstance(mark, dict) or set(mark) - {"node", "label", "tone"} or mark.get("node") not in node_map
                    or not isinstance(mark.get("label"), str) or not mark["label"].strip() or units(mark["label"]) > 16):
                _fail(f"{path}.marks[{mi}]", "node and a label of at most 8 full-width characters required")
            _tone(mark.get("tone"), f"{path}.marks[{mi}].tone", "red")
        _text(variant.get("label"), path + ".label")
        active = variant.get("active_nodes", [])
        if (not isinstance(active, list) or any(not isinstance(n, str) or n not in node_map for n in active)):
            _fail(path + ".active_nodes", "must contain existing node ids")
        note = variant.get("note", "")
        if not isinstance(note, str):
            _fail(path + ".note", "must be a string")
        edges = variant.get("edges")
        if not isinstance(edges, list):
            _fail(path + ".edges", "must be an array")
        edge_ids: set[str] = set()
        for ei, edge in enumerate(edges):
            ep = f"{path}.edges[{ei}]"
            if not isinstance(edge, dict):
                _fail(ep, "must be an object")
            if set(edge) - {"id", "from", "to", "label", "kind", "tone", "route", "label_side", "step", "text", "optional"}:
                _fail(ep, "unknown fields")
            _id(edge.get("id"), ep + ".id", edge_ids)
            source, target = edge.get("from"), edge.get("to")
            if (not isinstance(source, str) or not isinstance(target, str)
                    or source not in node_map or target not in node_map or source == target):
                _fail(ep, "from/to must name two different nodes")
            if "label" in edge:
                _text(edge["label"], ep + ".label")
            if edge.get("kind") not in KINDS:
                _fail(ep + ".kind", "must be request, file or conflict")
            _tone(edge.get("tone"), ep + ".tone", "blue")
            if not isinstance(edge.get("optional", False), bool):
                _fail(ep + ".optional", "must be true or false")
            if edge.get("route", "direct") not in ROUTES:
                _fail(ep + ".route", f"must be one of {sorted(ROUTES)}")
            if edge.get("label_side", "middle") not in {"middle", "above", "below"}:
                _fail(ep + ".label_side", "must be middle, above or below")
            if len(edge.get("label", "")) > 38:
                _fail(ep + ".label", "too long for an edge label")
    return spec


def _expand_steps(spec: dict[str, Any]) -> dict[str, Any]:
    """Turn top-level edges numbered by `step` into one variant per step.

    Every variant draws every edge so routes and labels stay put; the step
    decides which edges are done, current or still to come.
    """
    if "variants" in spec:
        _fail("network", "use either variants or edges with step numbers, not both")
    edges = spec["edges"]
    if not isinstance(edges, list) or not edges:
        _fail("network.edges", "must be a non-empty array")
    steps = []
    for i, edge in enumerate(edges):
        step = edge.get("step") if isinstance(edge, dict) else None
        if not isinstance(step, int) or isinstance(step, bool) or step < 1:
            _fail(f"network.edges[{i}].step", "positive integer required")
        if "text" in edge and (not isinstance(edge["text"], str) or not edge["text"].strip()):
            _fail(f"network.edges[{i}].text", "non-empty string required")
        steps.append(step)
    count = max(steps)
    if sorted(set(steps)) != list(range(1, count + 1)) or count < 2:
        _fail("network.edges", "steps must run 1, 2, 3 ... without gaps and have at least two steps")
    marks = spec.get("marks", [])
    if not isinstance(marks, list) or any(not isinstance(m, dict) or not isinstance(m.get("step"), int) or not 1 <= m["step"] <= count for m in marks):
        _fail("network.marks", "each mark needs a step between 1 and the last step")
    out = {k: v for k, v in spec.items() if k not in {"edges", "marks"}}
    out["variants"] = []
    for k in range(1, count + 1):
        current = [e for e in edges if e["step"] == k]
        nodes = sorted({n for e in current for n in (e.get("from"), e.get("to")) if isinstance(n, str)})
        out["variants"].append({"label": current[0].get("label") or f"手順{k}", "active_nodes": nodes, "edges": edges, "step": k,
                                "marks": [{x: v for x, v in m.items() if x != "step"} for m in marks if m["step"] == k]})
    return out


def network_steps(spec: dict[str, Any]) -> list[dict[str, str]]:
    """Default step labels and texts for a network whose edges carry step numbers."""
    edges = spec["edges"]
    return [{"label": re.sub(r"^\s*(?:[\u2460-\u2473]|\d+[.)．]?)\s*", "", plain(next(e.get("label", "") for e in edges if e["step"] == k))) or f"手順{k}",
             "text": " ".join(e["text"] for e in edges if e["step"] == k and e.get("text"))}
            for k in range(1, max(e["step"] for e in edges) + 1)]


def _visual_len(text: str) -> float:
    return units(text)


def _wrap(text: str, max_units: int = 18) -> list[str]:
    if not text:
        return [text]
    lines = wrap(text, max_units, 2)
    if lines is None:
        raise ValueError("label is too long for a compact diagram; shorten it or mark the break with \\n")
    return lines


# Top and bottom margins tried in order: compact first, wider only when a detour needs the room.
MARGINS = ((64.0, 64.0), (150.0, 64.0), (64.0, 150.0), (150.0, 150.0))


def _layout(spec: dict[str, Any], margins: tuple[float, float] = MARGINS[0]) -> tuple[dict[str, tuple[float, float]], float, float]:
    """Place nodes on the grid, dropping rows no node uses so the figure has no empty band."""
    width, margin_x, row_gap = 960.0, 120.0, 150.0
    top, bottom = margins
    if spec.get("boundaries"):
        top = max(top, 84.0)  # room for the boundary frame and its label above the first row
    used = sorted({n["row"] for n in spec["nodes"]})
    col_gap = (width - margin_x * 2) / max(1, spec["columns"] - 1)
    note_lines = max((len(_wrap(v["note"], 80)) for v in spec["variants"] if v.get("note")), default=0)
    height = top + bottom + (len(used) - 1) * row_gap + (20 + 16 * (note_lines - 1) if note_lines else 0)
    return ({n["id"]: (margin_x + (n["column"] - 1) * col_gap,
                        top + used.index(n["row"]) * row_gap)
             for n in spec["nodes"]}, col_gap, height)


def _ports(source: tuple[float, float], target: tuple[float, float]) -> tuple[tuple[float, float], tuple[float, float]]:
    sx, sy = source; tx, ty = target
    if abs(sx - tx) >= abs(sy - ty):
        return ((sx + (72 if tx >= sx else -72), sy), (tx - (72 if tx >= sx else -72), ty))
    return ((sx, sy + (36 if ty >= sy else -36)), (tx, ty - (36 if ty >= sy else -36)))


def _controls(source: tuple[float, float], target: tuple[float, float], route: str):
    """Endpoints and control points of an edge's cubic curve.

    Detours bulge across the edge's direction: above/below for a mostly
    horizontal edge, left/right (named above/below) for a mostly vertical one.
    """
    (sx, sy), (tx, ty) = _ports(source, target)
    vertical = abs(source[0] - target[0]) < abs(source[1] - target[1])
    if route == "direct":
        if vertical:
            cy = (sy + ty) / 2
            return (sx, sy), (sx, cy), (tx, cy), (tx, ty)
        cx = (sx + tx) / 2
        return (sx, sy), (cx, sy), (cx, ty), (tx, ty)
    near = route in {"above", "below"}
    if vertical:
        off = 40 if near and sx == tx and abs(ty - sy) <= 140 else 140  # clears a node half-width (72) at the curve's turn
        lane = min(sx, tx) - off if route.endswith("above") else max(sx, tx) + off
        return (sx, sy), (lane, sy), (lane, ty), (tx, ty)
    # A detour leaves and enters through the box's top or bottom edge, so the arrowhead points into the box.
    edge = -36 if route.endswith("above") else 36
    toward = 36 if target[0] >= source[0] else -36  # off centre, toward the other box, clear of edges that leave straight down
    sx, sy, tx, ty = source[0] + toward, source[1] + edge, target[0] - toward, target[1] + edge
    off = 40 if near and sy == ty and abs(tx - sx) <= 140 else 64
    lane = min(sy, ty) - off if route.endswith("above") else max(sy, ty) + off
    return (sx, sy), (sx, lane), (tx, lane), (tx, ty)


def _path(source: tuple[float, float], target: tuple[float, float], route: str) -> str:
    (sx, sy), (c1x, c1y), (c2x, c2y), (tx, ty) = _controls(source, target, route)
    return f"M {sx:g} {sy:g} C {c1x:g} {c1y:g}, {c2x:g} {c2y:g}, {tx:g} {ty:g}"


def _path_points(source: tuple[float, float], target: tuple[float, float], route: str, count: int = 20) -> list[tuple[float, float]]:
    """Sample the cubic path for deterministic obstacle and canvas checks."""
    (sx, sy), c1, c2, (tx, ty) = _controls(source, target, route)
    points = []
    for i in range(count + 1):
        t = i / count
        u = 1 - t
        points.append((u**3 * sx + 3*u*u*t*c1[0] + 3*u*t*t*c2[0] + t**3 * tx,
                       u**3 * sy + 3*u*u*t*c1[1] + 3*u*t*t*c2[1] + t**3 * ty))
    return points


def _route_is_safe(source: tuple[float, float], target: tuple[float, float], route: str,
                   obstacles: dict[str, tuple[float, float, float, float]], endpoint_ids: set[str],
                   height: float = 380, canvas_width: float = 960) -> bool:
    points = _path_points(source, target, route)
    if any(not (0 <= x <= canvas_width and 0 <= y <= height) for x, y in points):
        return False
    for oid, (left, top, right, bottom) in obstacles.items():
        if oid in endpoint_ids:
            continue
        if any(left - 4 <= x <= right + 4 and top - 4 <= y <= bottom + 4 for x, y in points):
            return False
    return True


def _label_is_safe(midpoint: tuple[float, float], words: list[str], side: str,
                   obstacles: dict[str, tuple[float, float, float, float]], endpoint_ids: set[str],
                   canvas_height: float = 380, canvas_width: float = 960) -> bool:
    width = max(_visual_len(word) for word in words) * 6.2 + 8
    height = 20 * len(words) + 4
    offset = -15 if side == "above" else 15 if side == "below" else 0
    left, right = midpoint[0] - width / 2, midpoint[0] + width / 2
    top, bottom = midpoint[1] + offset - height / 2, midpoint[1] + offset + height / 2
    if left < 0 or right > canvas_width or top < 0 or bottom > canvas_height:
        return False
    for oid, (node_left, node_top, node_right, node_bottom) in obstacles.items():
        if left <= node_right + 4 and right >= node_left - 4 and top <= node_bottom + 4 and bottom >= node_top - 4:
            return False
    return True


def _path_midpoint(source: tuple[float, float], target: tuple[float, float], route: str) -> tuple[float, float]:
    return _path_points(source, target, route, 2)[1]


NARROW_WIDTH = 420


def _layout_narrow(spec: dict[str, Any], extra_gap: float = 0.0, bottom_room: bool = False) -> tuple[dict[str, tuple[float, float]], float, float]:
    """The phone layout: the grid turned on its side, so a left-to-right flow reads top to bottom."""
    rows = sorted({n["row"] for n in spec["nodes"]})
    cols = sorted({n["column"] for n in spec["nodes"]})
    if len(rows) > 2:
        raise ValueError("network: no phone layout for three rows; put the main path on two rows to get one")
    xs = [NARROW_WIDTH / 2] if len(rows) == 1 else [NARROW_WIDTH / 2 - 105, NARROW_WIDTH / 2 + 105]
    top = 84.0 if spec.get("boundaries") else 64.0
    gap = 132.0 + extra_gap  # render_network retries with more room when a label or mark does not fit
    note_lines = max((len(_wrap(v["note"], 60)) for v in spec["variants"] if v.get("note")), default=0)
    height = top + 64 + (len(cols) - 1) * gap + (20 + 16 * (note_lines - 1) if note_lines else 0)
    # Two side-by-side boxes on the bottom row get room below them, so an edge between them can detour
    # underneath instead of crossing the lines that arrive from above. Every scene shares this height.
    column = {n["id"]: n["column"] for n in spec["nodes"]}
    edges = spec.get("edges", []) + [e for v in spec["variants"] for e in v.get("edges", [])]
    if bottom_room and len(rows) > 1 and any(column[e["from"]] == column[e["to"]] == cols[-1] for e in edges):
        height += 72
    return ({n["id"]: (xs[rows.index(n["row"])], top + cols.index(n["column"]) * gap) for n in spec["nodes"]},
            gap, height)


def render_network(spec: object, prefix: str = "diagram", narrow: bool = False) -> list[str]:
    """Render one self-contained accessible SVG per variant, in the most compact layout whose routes fit.

    With `narrow`, render the phone layout instead; it raises ValueError when an edge cannot be placed,
    and the caller then keeps only the wide layout.
    """
    data = validate_network(spec)
    if narrow:
        # Taller row gaps give long labels and detours more room before the phone layout gives up.
        attempts = [(extra, bottom, beside, strict) for strict in (True, False) for extra in (0.0, 48.0, 96.0)
                    for bottom in (False, True) for beside in (True, False)]  # the shortest figure that fits
        for n, (extra, bottom, beside, strict) in enumerate(attempts):
            try:
                return _render(data, prefix, None, extra, beside, strict, bottom)
            except _NoRoute:
                if n == len(attempts) - 1:
                    raise
    # Strict first (no label on a line, no line through a label); only if nothing fits, allow the overlap.
    attempts = [(margins, strict) for strict in (True, False) for margins in MARGINS]
    for n, (margins, strict) in enumerate(attempts):
        try:
            return _render(data, prefix, margins, strict=strict)
        except _NoRoute:
            if n == len(attempts) - 1:
                raise


def _crosses(path, others) -> bool:
    """Whether a sampled path crosses any earlier sampled path."""
    def side(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
    def hit(p, q, r, t):
        return side(p, q, r) * side(p, q, t) < 0 and side(r, t, p) * side(r, t, q) < 0
    return any(hit(a, b, c, e) for other in others for a, b in zip(path, path[1:]) for c, e in zip(other, other[1:]))


class _NoRoute(ValueError):
    pass


def _port_shifts(edges, positions):
    """Offsets for edge ends that share a node side, ordered by where the other end lies so they do not cross."""
    sides: dict[tuple[str, str], list] = {}
    pairs: dict[tuple[str, str], int] = {}
    for e in edges:
        key = tuple(sorted((e["from"], e["to"])))
        pairs[key] = pairs.get(key, 0) + 1
    for e in edges:
        if pairs[tuple(sorted((e["from"], e["to"])))] > 1:
            continue  # edges of one pair are already separated by their above/below detours
        (ax, ay), (bx, by) = positions[e["from"]], positions[e["to"]]
        horizontal = abs(ax - bx) >= abs(ay - by)
        for node, here, there, end in ((e["from"], (ax, ay), (bx, by), 0), (e["to"], (bx, by), (ax, ay), 1)):
            if horizontal:
                side = (node, "right" if there[0] > here[0] else "left")
                order = there[1]
            else:
                side = (node, "bottom" if there[1] > here[1] else "top")
                order = there[0]
            sides.setdefault(side, []).append((order, e["id"], end, horizontal))
    shifts: dict[str, list] = {}
    for items in sides.values():
        if len(items) < 2:
            continue
        items.sort()
        for k, (_, eid, end, horizontal) in enumerate(items):
            off = (k - (len(items) - 1) / 2) * 14
            pair = shifts.setdefault(eid, [(0, 0), (0, 0)])
            pair[end] = (0, off) if horizontal else (off, 0)
    return {k: tuple(v) for k, v in shifts.items()}


def _place_label(words, label_sides, mx, my, margins, obstacles, endpoint_ids, height, canvas, label_boxes, placed_paths, route, vertical=False):
    """A free spot for an edge label near the edge's middle, or None."""
    half = (max(_visual_len(word) for word in words) * 6.2 + 8) / 2 + 6
    # On the phone layout a label may also sit beside a vertical line instead of on it.
    beside = [("middle", mx + half), ("middle", mx - half)] if not margins else []
    # On the phone layout a short vertical edge would vanish under its label, so try beside the line first.
    spots = beside + [(side, mx) for side in label_sides] if vertical else [(side, mx) for side in label_sides] + beside
    for side, lx0 in spots:
        if not _label_is_safe((lx0, my), words, side, obstacles, endpoint_ids, height, canvas): continue
        offset = -15 if side == "above" else 15 if side == "below" else 0
        bw = max(_visual_len(word) for word in words) * 8 + 16; bh = 20 * len(words) + 4
        box = (lx0 - bw / 2, my + offset - bh / 2, lx0 + bw / 2, my + offset + bh / 2)
        if any(box[0] < r[2] + 6 and box[2] > r[0] - 6 and box[1] < r[3] + 6 and box[3] > r[1] - 6 for r in label_boxes): continue
        if any(box[0] + 4 <= x <= box[2] - 4 and box[1] + 2 <= y <= box[3] - 2 for pts in placed_paths for x, y in pts): continue
        return (route, lx0, my, offset, box, words)
    return None


def _render(data: dict[str, Any], prefix: str, margins: tuple[float, float] | None, extra_gap: float = 0.0,
            beside_first: bool = True, strict: bool = True, bottom_room: bool = False) -> list[str]:
    """Draw every variant; margins None selects the narrow phone layout."""
    safe_prefix = re.sub(r"[^A-Za-z0-9_-]", "-", prefix)
    positions, _, height = _layout(data, margins) if margins else _layout_narrow(data, extra_gap, bottom_room)
    canvas = 960 if margins else NARROW_WIDTH
    node_map = {n["id"]: n for n in data["nodes"]}
    obstacles = {n["id"]: (positions[n["id"]][0] - 72, positions[n["id"]][1] - 36,
                           positions[n["id"]][0] + 72, positions[n["id"]][1] + 36)
                 for n in data["nodes"]}
    out: list[str] = []
    for vi, variant in enumerate(data["variants"]):
        vid = f"{safe_prefix}-v{vi}"
        title = f"{variant['label']}の経路図"
        names = {n["id"]: plain(n["label"]) for n in data["nodes"]}
        flow = [f'{names[e["from"]]}→{names[e["to"]]}' + (f'「{plain(e["label"])}」' if e.get("label") else "") for e in variant["edges"]]
        flow += [f'{names[m["node"]]}「{m["label"]}」' for m in variant.get("marks", [])]
        desc = variant.get("note", "").strip() or "、".join(flow) or "経路なし"
        parts = [f'<svg class="dg-network" viewBox="0 0 {canvas} {height:g}" role="img" aria-labelledby="{vid}-title" aria-describedby="{vid}-desc">',
                 f'<title id="{vid}-title">{_esc(title)}</title>',
                 f'<desc id="{vid}-desc">{_esc(desc)}</desc>',
                 '<defs>']
        for marker_kind in ('file','request'):
            for marker_tone in sorted(TONES):
                parts.append(f'<marker id="{vid}-arrow-{marker_kind}-{marker_tone}" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="12" markerHeight="12" orient="auto"><path class="dg-arrow-head dg-tone-{marker_tone}" d="M0 0L10 5L0 10Z"/></marker>')
        parts.append('</defs>')
        active = set(variant.get("active_nodes", []))
        for boundary in data.get("boundaries", []):
            coords = [positions[n] for n in boundary["node_ids"]]
            xs = [p[0] for p in coords]; ys = [p[1] for p in coords]
            x, y = min(xs) - 98, min(ys) - 70
            w, h = max(xs) - min(xs) + 196, max(ys) - min(ys) + 122
            for other in data["nodes"]:
                if other["id"] not in boundary["node_ids"]:
                    ox, oy = positions[other["id"]]
                    if x <= ox <= x + w and y <= oy <= y + h:
                        _fail(f"network.boundaries[{boundary['id']}].node_ids", "boundary would swallow an unrelated node")
            key = f"boundary:{boundary['id']}"
            parts.append(f'<g class="dg-boundary dg-tone-{boundary.get("tone", "violet")}" data-key="{_esc(key)}"><rect data-key="{_esc(key)}:rect" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="14"/><text data-key="{_esc(key)}:label" x="{x+18:g}" y="{y+25:g}" class="dg-boundary-label" data-label="true">{_esc(boundary["label"])}</text></g>')
        edge_pairs: dict[tuple[str, str], int] = {}
        label_boxes = []
        mark_parts = []
        for mark in variant.get("marks", []):
            nx, ny = positions[mark["node"]]
            mw = units(mark["label"]) * 6.5 + 18
            # Straddle the node's top-right corner: clear of a centred label and of a boundary title at the top left.
            mx, top = nx + 72 - mw / 2 + 10, ny - 36 - 15
            if not margins:
                # Phone layout: edges arrive at the node's top centre, so keep the tag right of that line.
                mx = min(nx + 14 + mw / 2, canvas - 4 - mw / 2)
            label_boxes.append((mx - mw / 2, top, mx + mw / 2, top + 22))
            mkey = f"mark:{mark['node']}"
            mark_parts.append(f'<g class="dg-mark dg-tone-{mark.get("tone", "red")}" data-key="{mkey}" transform="translate({mx:g},{top + 11:g})">'
                              f'<rect data-key="{mkey}:rect" x="{-mw / 2:g}" y="-11" width="{mw:g}" height="22" rx="11"/>'
                              f'<text data-key="{mkey}:label" data-label="true" text-anchor="middle" y="4">{_esc(mark["label"])}</text></g>')
        # Marks are the first label boxes; edges must route around them as around nodes.
        placed_paths: list[list[tuple[float, float]]] = []
        # A node hidden in this variant is not drawn, so its cell is free for this variant's edges.
        node_obstacles = {k: v for k, v in obstacles.items() if k not in variant.get("hidden_nodes", [])}
        edge_obstacles = dict(node_obstacles)
        edge_obstacles.update((f"mark:{mark['node']}", box) for mark, box in zip(variant.get("marks", []), label_boxes))
        shifts = _port_shifts(variant["edges"], positions)
        for edge in variant["edges"]:
            sx, sy = positions[edge["from"]]; tx, ty = positions[edge["to"]]
            # Edges that meet the same side of a node attach a little apart, so their directions stay readable.
            (dsx, dsy), (dtx, dty) = shifts.get(edge["id"], ((0, 0), (0, 0)))
            sx, sy, tx, ty = sx + dsx, sy + dsy, tx + dtx, ty + dty
            key = f"edge:{edge['id']}"; kind = edge["kind"]
            pair = tuple(sorted((edge["from"], edge["to"])))
            count = edge_pairs.get(pair, 0)
            edge_pairs[pair] = count + 1
            route = edge.get("route", "direct")
            if route == "direct" and count:
                route = "above" if count % 2 else "below"
            endpoint_ids = {edge["from"], edge["to"], f"mark:{edge['from']}", f"mark:{edge['to']}"}
            if edge.get("route", "direct") != "direct" and margins:
                # An explicitly requested side is kept; the layout widens instead, and fails loudly if it cannot.
                candidates = [route]
            elif edge.get("route", "direct") != "direct":
                # The phone layout turns the grid on its side, so the requested side is only a preference there.
                candidates = [route, "below" if route == "above" else "above"]
            else:
                candidates = (["direct", "above", "below"] if route == "direct"
                              else [route, "below" if route == "above" else "above"])
            # Narrower wrappings are tried on each route before the edge is sent on a detour.
            wraps = []
            for units_per_line in (18, 12, 8):
                try:
                    w = _wrap(edge["label"], units_per_line) if edge.get("label") else []
                except ValueError:
                    continue
                if w not in wraps:
                    wraps.append(w)
            if not wraps:
                _wrap(edge["label"])  # raises the usual "too long" error
            requested_side = edge.get("label_side", "middle")
            label_sides = [requested_side] if requested_side != "middle" else ["middle", "above", "below"]
            candidates += [f"far-{route}"] if edge.get("route", "direct") != "direct" and margins else ["far-above", "far-below"]
            choice = None
            for candidate in candidates:
                if not _route_is_safe((sx, sy),(tx, ty),candidate,edge_obstacles,endpoint_ids,height,canvas): continue
                points=_path_points((sx, sy),(tx, ty),candidate)
                # Neither may a line run through an earlier label, nor a label sit on an earlier line.
                if strict and any(r[0]<=x<=r[2] and r[1]<=y<=r[3] for r in label_boxes[len(variant.get("marks", [])):] for x,y in points[2:-2]): continue
                # Nor may a detour cross an earlier line; a direct edge may, as a straight crossing reads clearly.
                if strict and candidate!="direct" and _crosses(_path_points((sx, sy),(tx, ty),candidate,40)[3:-3],placed_paths): continue
                mx,my = _path_midpoint((sx, sy),(tx, ty),candidate)
                if not wraps[0]:
                    choice=(candidate,mx,my,0,None,[]);break
                for words in wraps:
                    choice=_place_label(words,label_sides,mx,my,margins,node_obstacles,endpoint_ids,height,canvas,label_boxes,placed_paths if strict else [],candidate,beside_first and abs(sx-tx)<abs(sy-ty))
                    if choice:break
                if choice:break
            if choice is None:
                raise _NoRoute(f"network.variants[{vi}].edges[{edge['id']}]: no route and label slot fit"
                               + (f" on the requested side ({edge['route']})" if edge.get("route", "direct") != "direct" else "")
                               + "; rearrange nodes, shorten the label or drop route")
            route,lx,ly,offset,box,words=choice
            if box: label_boxes.append(box)
            placed_paths.append(_path_points((sx, sy),(tx, ty),route,40)[3:-3])
            d=_path((sx, sy),(tx, ty),route);tone=edge.get("tone","blue")
            state, opacity = "", ""
            if "step" in variant:
                state = " is-current" if edge["step"] == variant["step"] else " is-done" if edge["step"] < variant["step"] else " is-future"
                opacity = f' opacity="{"0.16" if state == " is-future" else "1"}"'
            if kind == "conflict":
                # Two things that clash: a red dashed line with a cross at its middle, no direction.
                parts.append(f'<path data-key="{_esc(key)}:path" class="dg-edge dg-edge-conflict dg-tone-{_esc(edge.get("tone", "red"))}{state}"{opacity} d="{d}"/>')
                parts.append(f'<g data-key="{_esc(key)}:cross" class="dg-conflict-cross dg-tone-{_esc(edge.get("tone", "red"))}"{opacity} transform="translate({lx:g},{ly:g})"><circle r="9"/><path d="M-4 -4L4 4M4 -4L-4 4"/></g>')
                if words:
                    offset = offset or -22
            else:
                optional = " dg-edge-optional" if edge.get("optional") else ""
                parts.append(f'<path data-key="{_esc(key)}:path" data-flow="{kind}" class="dg-edge dg-tone-{_esc(tone)}{state}{optional}"{opacity} d="{d}" marker-end="url(#{vid}-arrow-{kind}-{tone})"/>')
            if not words:
                continue
            tspans = "".join(
                f'<tspan x="0" dy="{20 if j else 0}">{_esc(word)}</tspan>'
                for j, word in enumerate(words)
            )
            label_width = _visual_len(max(words, key=_visual_len)) * 6.2 + 8
            parts.append(
                f'<g data-key="{_esc(key)}:label" class="dg-edge-label{state}" data-label="true"{opacity} '
                f'transform="translate({lx:g},{ly+offset:g})"><rect x="{-label_width/2:g}" '
                f'y="{-10*len(words)-2:g}" width="{label_width:g}" height="{20*len(words)+4:g}" '
                f'rx="4"/><text text-anchor="middle">{tspans}</text></g>'
            )
        for node in data["nodes"]:
            x, y = positions[node["id"]]; key = f"node:{node['id']}"; node_w, node_h = 144, 72
            # Fading is an opacity attribute, not CSS, so the script can animate it and a hidden node stays hidden.
            border = " active" if node["id"] in active else " inactive" if active and "step" not in variant else ""
            hide = ""
            box_fade = ' opacity="0.35"' if border == " inactive" else ""  # the box fades; its text turns muted (diagrams.css)
            if node["id"] in variant.get("hidden_nodes", []):
                border, hide = "", ' opacity="0" aria-hidden="true"'
            label_lines = _wrap(node["label"]); detail_lines = _wrap(node.get("detail", "")) if node.get("detail", "") else []
            if len(label_lines) + len(detail_lines) > 3:
                _fail(f"network.nodes[{node['id']}]", "label and detail exceed three lines; move detail to caption")
            # Centre the label and detail block vertically inside the node.
            line_count = len(label_lines) + len(detail_lines)
            label_y = y + 5 - (line_count - 1) * 9
            detail_y = label_y + 18 * len(label_lines) + (-1 if detail_lines else 0)
            label = "".join(f'<tspan x="{x:g}" dy="{0 if i == 0 else 18}">{_esc(line)}</tspan>' for i, line in enumerate(label_lines))
            detail = "".join(f'<tspan x="{x:g}" dy="{0 if i == 0 else 16}">{_esc(line)}</tspan>' for i, line in enumerate(detail_lines))
            parts.append(f'<g data-key="{_esc(key)}" class="dg-node dg-tone-{_esc(node.get("tone", "slate"))}{border}"{hide} data-ref="{_esc(plain(node["label"]))}" data-obstacle="{x-72:g},{y-36:g},{node_w},{node_h}"><rect data-key="{_esc(key)}:rect" x="{x-72:g}" y="{y-36:g}" width="{node_w}" height="{node_h}" rx="8"{box_fade}/><text data-key="{_esc(key)}:label" x="{x:g}" y="{label_y:g}" class="dg-node-label" data-label="true" text-anchor="middle">{label}</text><text data-key="{_esc(key)}:detail" x="{x:g}" y="{detail_y:g}" class="dg-node-detail" data-label="true" text-anchor="middle">{detail}</text></g>')
        parts.extend(mark_parts)
        note_x = 120 if margins else 16
        note_lines = _wrap(variant.get("note", ""), 80 if margins else 60) if variant.get("note", "") else []
        note = "".join(f'<tspan x="{note_x}" dy="{0 if i == 0 else 16}">{_esc(line)}</tspan>'
                        for i, line in enumerate(note_lines))
        parts.append(f'<text data-key="variant-note" class="dg-variant-note" x="{note_x}" y="{height - 14 - 16 * (len(note_lines) - 1 if note_lines else 0):g}" data-label="true">{note}</text></svg>')
        svg = "".join(parts)
        keys = re.findall(r'data-key="([^"]+)"', svg)
        if len(keys) != len(set(keys)):
            _fail(f"network.variants[{vi}]", "rendered data-key values must be unique")
        out.append(svg)
    return out

