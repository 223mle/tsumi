"""Sequence diagrams that replay one message per step.

Callers name the actors and the ordered messages. This module owns the column
spacing, lifelines, label wrapping and the per-step scenes, so a reader can see
the whole exchange faintly while the current message is drawn in full.
"""
from __future__ import annotations

import html
import re
from typing import Any

import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent))  # loadable by file path as well as by name
from jawrap import plain, strip_markup, units, wrap

ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
TONES = {"blue", "teal", "violet", "amber", "rose", "slate", "red"}
KINDS = {"call", "reply", "async"}
WIDTH = 960
HEAD_Y, HEAD_H = 18, 48
FIRST_ROW, ROW_GAP = 112, 58
SELF_W = 46


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _fail(path: str, message: str) -> None:
    raise ValueError(f"{path}: {message}")


def _units(text: str) -> float:
    return units(text)


def _wrap(text: str, max_units: int, path: str, max_lines: int = 2) -> list[str]:
    lines = wrap(text, max_units, max_lines)
    if lines is None:
        _fail(path, f"label is too long for {max_lines} lines; shorten it, mark the break with \\n, or move detail to the step text")
    return lines


def validate_sequence(spec: object) -> dict[str, Any]:
    if not isinstance(spec, dict):
        _fail("sequence", "must be an object")
    extra = set(spec) - {"type", "actors", "messages", "spans"}
    if extra:
        _fail("sequence", f"unknown fields {sorted(extra)}")
    actors = spec.get("actors")
    if not isinstance(actors, list) or not 2 <= len(actors) <= 6:
        _fail("sequence.actors", "2 to 6 actors required")
    ids: set[str] = set()
    for i, actor in enumerate(actors):
        path = f"sequence.actors[{i}]"
        if not isinstance(actor, dict) or set(actor) - {"id", "label", "tone", "detail"}:
            _fail(path, "id and label required; optional tone, detail")
        aid = actor.get("id")
        if not isinstance(aid, str) or not ID_RE.fullmatch(aid) or aid in ids:
            _fail(path + ".id", "unique identifier required")
        ids.add(aid)
        if not isinstance(actor.get("label"), str) or not actor["label"].strip():
            _fail(path + ".label", "text required")
        if actor.get("tone", "slate") not in TONES:
            _fail(path + ".tone", f"one of {sorted(TONES)}")
        if not isinstance(actor.get("detail", ""), str):
            _fail(path + ".detail", "string required")
    messages = spec.get("messages")
    if not isinstance(messages, list) or not messages or len(messages) > 14:
        _fail("sequence.messages", "1 to 14 messages required; split a longer exchange into two figures")
    mids: set[str] = set()
    for i, msg in enumerate(messages):
        path = f"sequence.messages[{i}]"
        if not isinstance(msg, dict) or set(msg) - {"id", "from", "to", "label", "kind", "tone", "text", "step_label"}:
            _fail(path, "id, from, to, label required; optional kind, tone, text, step_label")
        mid = msg.get("id")
        if not isinstance(mid, str) or not ID_RE.fullmatch(mid) or mid in mids:
            _fail(path + ".id", "unique identifier required")
        mids.add(mid)
        if msg.get("from") not in ids or msg.get("to") not in ids:
            _fail(path, "from/to must name actors")
        for key in ("label",):
            if not isinstance(msg.get(key), str) or not msg[key].strip():
                _fail(path + "." + key, "text required")
        for key in ("text", "step_label"):
            if key in msg and (not isinstance(msg[key], str) or not msg[key].strip()):
                _fail(path + "." + key, "non-empty text required")
        if msg.get("kind", "call") not in KINDS:
            _fail(path + ".kind", f"one of {sorted(KINDS)}")
        if msg.get("tone", "blue") not in TONES:
            _fail(path + ".tone", f"one of {sorted(TONES)}")
    spans = spec.get("spans", [])
    if not isinstance(spans, list) or len(spans) > 3:
        _fail("sequence.spans", "up to 3 spans")
    for i, span in enumerate(spans):
        path = f"sequence.spans[{i}]"
        if not isinstance(span, dict) or set(span) - {"from", "to", "label", "tone"} or not {"from", "to", "label"} <= set(span):
            _fail(path, "from, to (message ids) and label required")
        if span["from"] not in mids or span["to"] not in mids:
            _fail(path, "from/to must name messages")
        order = [m["id"] for m in messages]
        if order.index(span["from"]) > order.index(span["to"]):
            _fail(path, "from must not come after to")
        if not isinstance(span["label"], str) or not span["label"].strip() or _units(span["label"]) > 14:
            _fail(path + ".label", "short text required (7 full-width characters)")
        if span.get("tone", "amber") not in TONES:
            _fail(path + ".tone", f"one of {sorted(TONES)}")
    return spec


def _span_actor(spec: dict[str, Any], span: dict[str, Any]) -> str:
    """The actor beside which a span is drawn: the rightmost one its messages touch."""
    order = [a["id"] for a in spec["actors"]]
    ids = [m["id"] for m in spec["messages"]]
    a, b = ids.index(span["from"]), ids.index(span["to"])
    involved = {x for m in spec["messages"][a:b + 1] for x in (m["from"], m["to"])}
    return max(involved, key=order.index)


NARROW_WIDTH = 420


def _width(spec: dict[str, Any], narrow: bool = False) -> float:
    """Few actors get a narrower canvas, so columns stay close and the text stays large on a phone."""
    if narrow:
        return float(NARROW_WIDTH)
    return float(min(WIDTH, 260 * (len(spec["actors"]) - 1) + 220 + (50 if spec.get("spans") else 0)))


def _columns(spec: dict[str, Any], narrow: bool = False) -> tuple[dict[str, float], float, float]:
    count = len(spec["actors"])
    # On the phone canvas few actors get wider margins, so their boxes (up to 176 wide) stay inside it.
    edge = {2: 100.0, 3: 76.0}.get(count, 56.0) if narrow else 110.0
    left = edge
    span_right = any(_span_actor(spec, sp) == spec["actors"][-1]["id"] for sp in spec.get("spans", []))
    right = max(edge, 128.0) if narrow and span_right else edge if narrow else (160.0 if span_right else 110.0)
    if any(m["from"] == m["to"] == spec["actors"][-1]["id"] for m in spec["messages"]):
        right += 70 if narrow else 120  # room for the label beside the rightmost actor's self-call loop
    gap = (_width(spec, narrow) - left - right) / (count - 1)
    return ({a["id"]: left + i * gap for i, a in enumerate(spec["actors"])}, gap, left)


def render_sequence(spec: object, prefix: str = "sequence", narrow: bool = False) -> list[str]:
    """Return one SVG per message: earlier messages solid, the current one marked, later ones faint.

    With `narrow`, lay out for a phone (up to four actors); labels that do not fit raise ValueError.
    """
    data = validate_sequence(spec)
    if narrow and len(data["actors"]) > 4:
        raise ValueError("sequence: no phone layout for more than four actors; merge or drop actors to get one")
    safe = re.sub(r"[^A-Za-z0-9_-]", "-", prefix)
    xs, gap, left = _columns(data, narrow)
    canvas = _width(data, narrow)  # used below for self-call room
    max_lines = 3 if narrow else 2
    min_width = "" if narrow else f' style="--min-width:{canvas * 0.72:.0f}px"'
    msgs = data["messages"]
    label_units = max(10, int((gap - 28) / 6.6))
    rows: list[float] = []
    layouts = []
    y = FIRST_ROW
    for i, msg in enumerate(msgs):
        self_call = msg["from"] == msg["to"]
        span_cols = 1 if self_call else round(abs(xs[msg["to"]] - xs[msg["from"]]) / gap)
        # A self-call's label sits right of its loop, so it may only use the room left on the canvas.
        units = min(label_units, int((canvas - (xs[msg["from"]] + SELF_W + 8) - 4) / 6.6)) if self_call else max(label_units, int((abs(xs[msg["to"]] - xs[msg["from"]]) - 28) / 6.6))
        if self_call and units < 8:
            _fail(f"sequence.messages[{i}].label", "no room right of this self-call; give the actor a neighbour on its right or shorten the label")
        lines = _wrap(msg["label"], units, f"sequence.messages[{i}].label", max_lines)
        extra = 18 * (len(lines) - 1)
        y += extra
        rows.append(y)
        layouts.append((lines, self_call, span_cols))
        y += ROW_GAP + (22 if self_call else 0)
    height = y + 4
    # Actor names are 14px wide-screen and 12px on the phone layout (see diagrams.css).
    actor_lines = {a["id"]: _wrap(a["label"], int((min(gap, 200) - 20) / 7.2) if not narrow else int((gap - 10) / 6.2), f"sequence.actors[{a['id']}].label") for a in data["actors"]}
    out = []
    for step in range(len(msgs)):
        vid = f"{safe}-s{step}"
        cur = msgs[step]
        title = f"手順{step + 1}: {plain(cur['label'])}"
        parts = [f'<svg class="dg-sequence" viewBox="0 0 {canvas:g} {height:g}" role="img"{min_width} aria-labelledby="{vid}-title" aria-describedby="{vid}-desc">',
                 f'<title id="{vid}-title">{_esc(title)}</title><desc id="{vid}-desc">{_esc(strip_markup(cur.get("text", cur["label"])))}</desc><defs>']
        for tone in sorted(TONES):
            parts.append(f'<marker id="{vid}-solid-{tone}" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" orient="auto-start-reverse"><path class="dg-arrow-head dg-tone-{tone}" d="M0 0L10 5L0 10Z"/></marker>')
            parts.append(f'<marker id="{vid}-open-{tone}" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" orient="auto-start-reverse"><path class="dg-arrow-open dg-tone-{tone}" d="M1 1L9 5L1 9"/></marker>')
        parts.append('</defs>')
        involved = {cur["from"], cur["to"]}
        for actor in data["actors"]:
            x = xs[actor["id"]]
            key = f"actor:{actor['id']}"
            state = " is-current" if actor["id"] in involved else ""
            lines = actor_lines[actor["id"]]
            ty = HEAD_Y + HEAD_H / 2 - (len(lines) - 1) * 8
            tspans = "".join(f'<tspan x="{x:g}" dy="{0 if j == 0 else 16}">{_esc(line)}</tspan>' for j, line in enumerate(lines))
            w = min(gap - (8 if narrow else 16), 176, 2 * left - 8)  # never wider than the margin allows at the edges
            parts.append(f'<g class="dg-actor dg-tone-{actor.get("tone", "slate")}{state}" data-key="{key}" data-ref="{_esc(plain(actor["label"]))}">'
                         f'<line class="dg-lifeline" data-key="{key}:life" x1="{x:g}" y1="{HEAD_Y + HEAD_H:g}" x2="{x:g}" y2="{height - 8:g}"/>'
                         f'<rect data-key="{key}:box" x="{x - w / 2:g}" y="{HEAD_Y}" width="{w:g}" height="{HEAD_H}" rx="8"/>'
                         f'<text data-key="{key}:label" class="dg-actor-label" data-label="true" x="{x:g}" y="{ty + 5:g}" text-anchor="middle">{tspans}</text></g>')
        actor_order = [a["id"] for a in data["actors"]]
        for si, span in enumerate(data.get("spans", [])):
            order = [m["id"] for m in msgs]
            a, b = order.index(span["from"]), order.index(span["to"])
            y1, y2 = rows[a], rows[b]
            # Measure beside the rightmost actor taking part in the measured messages, where no arrow of the span passes.
            edge_id = _span_actor(data, span)
            edge_x = xs[edge_id]
            bx = edge_x + 42
            for j in range(a, b + 1):
                # A self-call on that actor puts its loop and label right of the lifeline; measure past them.
                if layouts[j][1] and msgs[j]["from"] == edge_id:
                    bx = max(bx, edge_x + SELF_W + 8 + max(_units(line) for line in layouts[j][0]) * 6.6 + 16)
            lx, anchor = bx + 12, "start"
            if lx + _units(span["label"]) * 6.6 > canvas:
                _fail(f"sequence.spans[{si}]", "no room right of the measured messages; shorten the label or end the span before the self-call")
            op = "1" if step >= b else "0.35"
            key = f"span:{si}"
            mid = (y1 + y2) / 2
            future = " is-future" if step < b else ""
            parts.append(f'<g class="dg-span dg-tone-{span.get("tone", "amber")}{future}" data-key="{key}">'
                         f'<path data-key="{key}:line" opacity="{op}" d="M{bx - 7:g} {y1:g}H{bx + 7:g}M{bx:g} {y1:g}V{y2:g}M{bx - 7:g} {y2:g}H{bx + 7:g}"/>'
                         f'<text data-key="{key}:label" class="dg-span-label" data-label="true" x="{lx:g}" y="{mid + 4:g}" text-anchor="{anchor}">{_esc(span["label"])}</text></g>')
        for i, msg in enumerate(msgs):
            lines, self_call, _ = layouts[i]
            y = rows[i]
            x1, x2 = xs[msg["from"]], xs[msg["to"]]
            kind = msg.get("kind", "call")
            tone = msg.get("tone", "slate" if kind == "reply" else "blue")
            key = f"msg:{msg['id']}"
            state = "is-current" if i == step else "is-done" if i < step else "is-future"
            fade = "" if i <= step else ' opacity="0.26"'  # lines and numbers fade; the label stays legible in muted ink
            marker = f"url(#{vid}-{'open' if kind != 'call' else 'solid'}-{tone})"
            if self_call:
                d = f"M{x1 + 6:g} {y:g}H{x1 + SELF_W:g}V{y + 22:g}H{x1 + 8:g}"
                lx, anchor, ly = x1 + SELF_W + 8, "start", y + 4
            else:
                direction = 1 if x2 > x1 else -1
                d = f"M{x1 + 6 * direction:g} {y:g}H{x2 - 8 * direction:g}"
                lx, anchor, ly = (x1 + x2) / 2, "middle", y - 10 - 18 * (len(lines) - 1)
            tspans = "".join(f'<tspan x="{lx:g}" dy="{0 if j == 0 else 18}">{_esc(line)}</tspan>' for j, line in enumerate(lines))
            num_x = x1 - 20 if self_call or x2 > x1 else x1 + 20
            parts.append(f'<g class="dg-msg dg-msg-{kind} dg-tone-{tone} {state}" data-key="{key}">'
                         f'<path class="dg-msg-line" data-key="{key}:line" data-flow="{"request" if kind == "call" else "file"}" d="{d}" marker-end="{marker}"{fade}/>'
                         f'<text class="dg-msg-label" data-label="true" data-key="{key}:label" x="{lx:g}" y="{ly:g}" text-anchor="{anchor}">{tspans}</text>'
                         f'<g class="dg-step-num" data-key="{key}:num" transform="translate({num_x:g} {y:g})"{fade}><circle r="10"/><text text-anchor="middle" y="4">{i + 1}</text></g></g>')
        parts.append('</svg>')
        out.append("".join(parts))
    return out


def sequence_steps(spec: dict[str, Any]) -> list[dict[str, str]]:
    """Default step labels and texts derived from the messages."""
    return [{"label": m.get("step_label", plain(m["label"])), "text": m.get("text", "")} for m in spec["messages"]]
