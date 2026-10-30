#!/usr/bin/env python3
"""Render a validated explainer document JSON as one portable HTML file."""
from __future__ import annotations

import argparse, html, itertools, json, math, os, re, sys, tempfile
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blocks import validate_glossary, validate_block, block_html, check_inline, inline  # noqa: E402
from diagrams import render_diagram  # noqa: E402
from jawrap import strip_markup  # noqa: E402
STATUSES = {"measured", "inferred", "proposed", "unknown", "illustrative"}
KINDS = {"flow", "bars", "timeline", "table"}
STATUS_LABELS = {"measured": "計測値", "inferred": "推定", "proposed": "提案", "unknown": "未確定", "illustrative": "説明用"}
STATUS_HELP = {"measured": "実際に測った値です。", "inferred": "根拠となる資料や条件から計算・推定した値です。", "proposed": "これから行う案で、まだ実施していません。",
               "unknown": "まだ決まっていない、または確かめていない部分です。", "illustrative": "仕組みを説明するための例で、実際の値ではありません。", "code": "コードから読み取った内容です。"}

_STATUS_TIPS = itertools.count(1)

def status_badge(status: str, label: str) -> str:
    """A figure's evidence badge that explains itself on hover, focus or tap, like a glossary term."""
    tip = f"status-tip:{next(_STATUS_TIPS)}"
    return (f'<span class="term status-term" tabindex="0" aria-describedby="{tip}"><span class="status status-{esc(status)}">{esc(label)}</span>'
            f'<span class="term-tip" role="tooltip" id="{tip}" aria-hidden="true"><b>{esc(label)}</b>{esc(STATUS_HELP.get(status, ""))}</span></span>')
ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")

def esc(v: object) -> str:
    return html.escape(str(v), quote=True)

def fail(msg: str) -> None:
    raise ValueError(msg)

def check_url(value: object, where: str) -> None:
    if not isinstance(value, str): fail(f"{where}: URL must be a string")
    p = urlparse(value)
    if p.scheme not in {"http", "https"} or not p.netloc or any(c in value for c in "<>\"'\n\r"):
        fail(f"{where}: only absolute http(s) URLs are allowed")

def check_id(value: object, where: str, seen: set[str]) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value): fail(f"{where}: invalid id")
    if value in seen: fail(f"{where}: duplicate id {value}")
    seen.add(value); return value

def number(v: object, where: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        fail(f"{where}: finite number required")
    try:
        converted = float(v)
    except (OverflowError, ValueError):
        fail(f"{where}: finite number required")
    if not math.isfinite(converted):
        fail(f"{where}: finite number required")
    return converted

def validate(doc: object) -> dict:
    if not isinstance(doc, dict): fail("document: object required")
    schema = json.loads((ROOT / "assets" / "document.schema.json").read_text(encoding="utf-8"))
    schema_validate(doc, schema, "document", schema)
    allowed = {"title", "lead", "sources", "sections", "takeaways", "glossary"}
    unknown = set(doc) - allowed
    if unknown: fail(f"document: unknown fields {sorted(unknown)}")
    for key in ("title", "lead"):
        if not isinstance(doc.get(key), str) or not doc[key].strip(): fail(f"document.{key}: non-empty string required")
    glossary = validate_glossary(doc.get("glossary"))
    check_inline(doc["lead"], "document.lead", glossary)
    takeaways = doc.get("takeaways", [])
    if not isinstance(takeaways, list) or len(takeaways) > 4 or not all(isinstance(t, str) and t.strip() and len(t) <= 90 for t in takeaways):
        fail("document.takeaways: up to 4 sentences of at most 90 characters")
    for i, t in enumerate(takeaways): check_inline(t, f"document.takeaways[{i}]", glossary)
    if not isinstance(doc.get("sections"), list) or not doc["sections"]: fail("document.sections: non-empty array required")
    sources = doc.get("sources", [])
    if not isinstance(sources, list): fail("document.sources: array required")
    source_ids: set[str] = set()
    all_ids: set[str] = {"main", "sources", "glossary"}  # ids the page generates itself
    for i, source in enumerate(sources):
        if not isinstance(source, dict) or not {"id", "title"}.issubset(source) or set(source) - {"id", "title", "note", "url"}: fail(f"sources[{i}]: id and title required; note or url required")
        if not source.get("note") and not source.get("url"): fail(f"sources[{i}]: note or url required")
        check_id(source["id"], f"sources[{i}].id", source_ids)
        check_id(source["id"], f"sources[{i}].id", all_ids)
        if not isinstance(source["title"], str) or not source["title"].strip(): fail(f"sources[{i}].title: string required")
        if "note" in source and (not isinstance(source["note"], str) or not source["note"].strip()): fail(f"sources[{i}].note: non-empty string required")
        if "url" in source: check_url(source["url"], f"sources[{i}].url")
    section_ids = all_ids; figure_ids = all_ids
    for si, sec in enumerate(doc["sections"]):
        if not isinstance(sec, dict): fail(f"sections[{si}]: object required")
        unknown = set(sec) - {"id", "title", "paragraphs", "callout", "figures", "blocks"}
        if unknown: fail(f"sections[{si}]: unknown fields {sorted(unknown)}")
        check_id(sec.get("id"), f"sections[{si}].id", section_ids)
        if not isinstance(sec.get("title"), str) or not sec["title"].strip(): fail(f"sections[{si}].title: string required")
        if "paragraphs" in sec and (not isinstance(sec["paragraphs"], list) or not all(isinstance(x, str) for x in sec["paragraphs"])): fail(f"sections[{si}].paragraphs: strings required")
        if "callout" in sec and not isinstance(sec["callout"], str): fail(f"sections[{si}].callout: string required")
        for pi, para in enumerate(sec.get("paragraphs", [])): check_inline(para, f"sections[{si}].paragraphs[{pi}]", glossary)
        blocks = sec.get("blocks", [])
        if not isinstance(blocks, list): fail(f"sections[{si}].blocks: array required")
        for bi, block in enumerate(blocks):
            validate_block(block, f"sections[{si}].blocks[{bi}]", glossary,
                           lambda f, w: validate_figure(f, w, source_ids, figure_ids),
                           lambda b, w: check_diagram(b, w, figure_ids, glossary, source_ids))
        figs = sec.get("figures", [])
        if not isinstance(figs, list): fail(f"sections[{si}].figures: array required")
        for fi, fig in enumerate(figs): validate_figure(fig, f"sections[{si}].figures[{fi}]", source_ids, figure_ids)
    return doc

def check_diagram(bundle: object, where: str, seen: set[str], glossary: dict[str, str], source_ids: set[str]) -> None:
    try:
        render_diagram(bundle)
    except (ValueError, TypeError, KeyError) as exc:
        fail(f"{where}: {exc}")
    check_id(bundle["id"], where + ".id", seen)
    refs = bundle.get("source_ids", [])
    if any(r not in source_ids for r in refs): fail(f"{where}.source_ids: unknown source id")
    if bundle.get("status") in {"measured", "inferred"} and not refs: fail(f"{where}: {bundle['status']} figure requires source_ids")
    prose = [bundle["caption"], *bundle.get("notes", []), *(st.get("text", "") for st in bundle.get("steps", []))]
    prose += [m.get("text", "") for p in bundle["panels"] for m in p["spec"].get("messages", []) + p["spec"].get("edges", [])]
    for text in filter(None, prose): check_inline(text, where, glossary)

WARNINGS: list[str] = []  # notes printed after a successful render, such as figures without a phone layout

PROSE_KEYS = {"title", "lead", "takeaways", "text", "items", "paragraphs", "caption", "summary", "verdict", "notes", "definition", "callout"}

def prose_strings(value: object, key: str = "") -> list[str]:
    """Sentences a reader sees, in document order, without diagram labels."""
    if isinstance(value, str):
        return [value] if key in PROSE_KEYS and value.strip() else []
    if isinstance(value, list):
        return [t for item in value for t in prose_strings(item, key)]
    if isinstance(value, dict):
        return [t for k, v in value.items() for t in prose_strings(v, k if k in PROSE_KEYS or not isinstance(v, str) else k)]
    return []

def reading_minutes(body_html: str) -> int:
    """Estimate reading time from visible prose at about 500 Japanese characters a minute."""
    text = re.sub(r"<svg.*?</svg>|<template.*?</template>|<[^>]+>|\s", "", body_html, flags=re.S)
    return max(1, round(len(html.unescape(text)) / 500))

def schema_validate(value: object, schema: dict, where: str, root: dict) -> None:
    """Small schema subset used so the checked-in JSON schema remains the contract."""
    if "$ref" in schema:
        target = root
        for part in schema["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        schema_validate(value, target, where, root); return
    if "enum" in schema and value not in schema["enum"]: fail(f"{where}: invalid enum value")
    typ = schema.get("type")
    if typ == "object":
        if not isinstance(value, dict): fail(f"{where}: object required")
        missing = set(schema.get("required", [])) - set(value)
        if missing: fail(f"{where}: missing {sorted(missing)}")
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(schema.get("properties", {}));
            if extra: fail(f"{where}: unknown fields {sorted(extra)}")
        for key, subschema in schema.get("properties", {}).items():
            if key in value: schema_validate(value[key], subschema, f"{where}.{key}", root)
    elif typ == "array":
        if not isinstance(value, list): fail(f"{where}: array required")
        if "minItems" in schema and len(value) < schema["minItems"]: fail(f"{where}: too few items")
        for i, item in enumerate(value): schema_validate(item, schema.get("items", {}), f"{where}[{i}]", root)
    elif typ == "string":
        if not isinstance(value, str): fail(f"{where}: string required")
        if len(value) < schema.get("minLength", 0): fail(f"{where}: non-empty string required")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value): fail(f"{where}: invalid format")
    elif typ == "number" and (isinstance(value, bool) or not isinstance(value, (int, float))): fail(f"{where}: number required")

def validate_figure(fig: object, where: str, source_ids: set[str], seen: set[str]) -> None:
    if not isinstance(fig, dict): fail(f"{where}: object required")
    required = {"id", "kind", "title", "summary", "caption", "status"}
    if not required.issubset(fig): fail(f"{where}: missing {sorted(required - set(fig))}")
    common = required | {"source_ids", "unit", "axis_max", "steps", "rows", "columns"}
    if set(fig) - common: fail(f"{where}: unknown fields {sorted(set(fig)-common)}")
    check_id(fig["id"], where+".id", seen)
    if not isinstance(fig["kind"], str) or fig["kind"] not in KINDS: fail(f"{where}.kind: one of {sorted(KINDS)} required")
    for key in ("title", "summary", "caption"):
        if not isinstance(fig[key], str) or not fig[key].strip(): fail(f"{where}.{key}: non-empty string required")
    if not isinstance(fig["status"], str) or fig["status"] not in STATUSES: fail(f"{where}.status: invalid status")
    refs = fig.get("source_ids", [])
    if not isinstance(refs, list) or not all(isinstance(x, str) and x in source_ids for x in refs): fail(f"{where}.source_ids: unknown source id")
    if fig["status"] in {"measured", "inferred"} and not refs: fail(f"{where}: {fig['status']} figure requires source_ids")
    if "unit" in fig and not isinstance(fig["unit"], str): fail(f"{where}.unit: string required")
    if "axis_max" in fig and (number(fig["axis_max"], where+".axis_max") <= 0): fail(f"{where}.axis_max: positive required")
    if fig["kind"] == "flow":
        steps = fig.get("steps")
        if not isinstance(steps, list) or len(steps) < 2: fail(f"{where}.steps: at least two steps required")
        for i, step in enumerate(steps):
            if not isinstance(step, dict) or set(step) - {"label", "detail", "to_next"} or not all(isinstance(step.get(x), str) and step[x].strip() for x in ("label", "detail")): fail(f"{where}.steps[{i}]: label and detail required")
            if i < len(steps)-1 and (not isinstance(step.get("to_next"), str) or not step["to_next"].strip()): fail(f"{where}.steps[{i}].to_next: required for non-final step")
    elif fig["kind"] == "bars":
        if not isinstance(fig.get("unit"), str) or not fig["unit"].strip(): fail(f"{where}.unit: required for bars")
        rows = fig.get("rows"); validate_numeric_rows(rows, where, "value")
        maxval = max(float(r["value"]) for r in rows)
        if "axis_max" in fig and float(fig["axis_max"]) < maxval: fail(f"{where}.axis_max: below row value")
    elif fig["kind"] == "timeline":
        if not isinstance(fig.get("unit"), str) or not fig["unit"].strip(): fail(f"{where}.unit: required for timeline")
        rows = fig.get("rows")
        if not isinstance(rows, list) or not rows: fail(f"{where}.rows: non-empty array required")
        end = 0.0
        for i, row in enumerate(rows):
            if not isinstance(row, dict) or set(row) != {"label", "start", "duration"} or not isinstance(row.get("label"), str): fail(f"{where}.rows[{i}]: label, start, duration required")
            start, duration = number(row["start"], where+f".rows[{i}].start"), number(row["duration"], where+f".rows[{i}].duration")
            if start < 0 or duration <= 0: fail(f"{where}.rows[{i}]: start >= 0 and duration > 0 required")
            row_end = start + duration
            if not math.isfinite(row_end): fail(f"{where}.rows[{i}]: start + duration must be finite")
            end = max(end, row_end)
        if "axis_max" in fig and float(fig["axis_max"]) < end: fail(f"{where}.axis_max: below timeline end")
    elif fig["kind"] == "table":
        cols, rows = fig.get("columns"), fig.get("rows")
        if not isinstance(cols, list) or not cols or not all(isinstance(x, str) and x.strip() for x in cols): fail(f"{where}.columns: non-empty strings required")
        if not isinstance(rows, list) or not rows: fail(f"{where}.rows: non-empty array required")
        for i, row in enumerate(rows):
            if not isinstance(row, list) or len(row) != len(cols) or not all(isinstance(x, str) for x in row): fail(f"{where}.rows[{i}]: cell count/type mismatch")

def validate_numeric_rows(rows: object, where: str, key: str) -> None:
    if not isinstance(rows, list) or not rows: fail(f"{where}.rows: non-empty array required")
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {"label", key} or not isinstance(row.get("label"), str): fail(f"{where}.rows[{i}]: label and {key} required")
        if number(row[key], f"{where}.rows[{i}].{key}") < 0: fail(f"{where}.rows[{i}].{key}: non-negative required")

def fmt(v: float) -> str:
    if v == 0: return "0"
    if abs(v) >= 1 and v.is_integer(): return str(int(v))
    text = f"{v:.6g}"
    return text if text != "0" else f"{v:.6g}"

def ticks(mx: float, count: int = 5) -> list[float]:
    """Round ticks (1, 2, 2.5 or 5 times a power of ten) from 0 up to mx; mx itself if no round step fits."""
    try:
        if mx > 0 and math.isfinite(mx):
            for step in sorted(m * 10.0 ** e for e in range(math.floor(math.log10(mx)) - 2, math.floor(math.log10(mx)) + 2) for m in (1, 2, 2.5, 5)):
                if not step or not math.isfinite(step):
                    continue
                n = mx / step
                if n <= count + 1 and abs(n - round(n)) < 1e-9:
                    return [float(step * i) for i in range(round(n) + 1)]
    except (OverflowError, ZeroDivisionError):
        pass  # extreme values: fall back to evenly divided ticks
    # Multiply by the fraction first: mx * i can overflow for a valid finite
    # max value even though every tick is within [0, mx].
    return [mx * (i / count) for i in range(count + 1)]

def figure_html(fig: dict, source_titles: dict[str, str] | None = None) -> str:
    kind, fid = fig["kind"], esc(fig["id"]); body = ""
    if kind == "flow":
        items = []
        for i, step in enumerate(fig["steps"]):
            items.append(f'<li class="flow-node"><span class="flow-label">{esc(step["label"])}</span><span class="flow-detail">{esc(step["detail"])}</span></li>')
            if i < len(fig["steps"])-1: items.append(f'<li class="flow-arrow"><span class="arrow" aria-hidden="true">→</span><span>{esc(step["to_next"])}</span></li>')
        body = '<ol class="flow">' + ''.join(items) + '</ol>'
    elif kind == "bars":
        mx = float(fig.get("axis_max", max(r["value"] for r in fig["rows"]))); axis = ''.join(f'<span>{esc(fmt(x))}</span>' for x in ticks(mx))
        ratio = mx if mx > 0 else 1.0; rows = ''.join(f'<div class="chart-row"><span class="chart-label">{esc(r["label"])}</span><span class="chart-track"><span class="chart-fill" style="width:{float(r["value"])/ratio*100:.4f}%"></span></span><strong class="chart-value">{esc(fmt(float(r["value"])))}{esc(fig["unit"])}</strong></div>' for r in fig["rows"])
        body = f'<div class="chart">{rows}<div class="chart-axis"><span class="axis-spacer"></span><span class="axis-ticks">{axis}</span><span>{esc(fig["unit"])}</span></div></div>'
    elif kind == "timeline":
        mx = float(fig.get("axis_max", max(r["start"]+r["duration"] for r in fig["rows"]))); axis = ''.join(f'<span>{esc(fmt(x))}</span>' for x in ticks(mx))
        rows = ''.join(f'<div class="chart-row"><span class="chart-label">{esc(r["label"])}</span><span class="chart-track"><span class="chart-fill" style="left:{r["start"]/mx*100:.4f}%;width:{r["duration"]/mx*100:.4f}%"></span></span><strong class="chart-value">{esc(fmt(float(r["start"])))}〜{esc(fmt(float(r["start"]+r["duration"])))}{esc(fig["unit"])}</strong></div>' for r in fig["rows"])
        body = f'<div class="chart timeline">{rows}<div class="chart-axis"><span class="axis-spacer"></span><span class="axis-ticks">{axis}</span><span>{esc(fig["unit"])}</span></div></div>'
    else:
        head = ''.join(f'<th scope="col">{esc(c)}</th>' for c in fig["columns"])
        # data-label lets a phone show each row as a card with its column names (style.css, .table-stack).
        rows = ''.join('<tr>' + ''.join((f'<th scope="row">{esc(c)}</th>' if j == 0 else f'<td data-label="{esc(fig["columns"][j])}">{esc(c)}</td>') for j, c in enumerate(row)) + '</tr>' for row in fig["rows"])
        body = f'<p class="table-summary">{esc(fig["summary"])}</p><div class="table-wrap" tabindex="0" role="region" aria-label="表: {esc(fig["summary"].rstrip("。"))}"><p class="scroll-hint">横にスクロールして表全体を確認できます。</p><table class="{"table-stack" if len(fig["columns"]) >= 4 else ""}"><caption class="visually-hidden">{esc(fig["summary"])}</caption><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
    source_titles = source_titles or {}
    status = esc(fig["status"]); refs = ''.join(f'<a class="source-ref" href="#{esc(x)}">{esc(source_titles.get(x, x))}</a>' for x in fig.get("source_ids", []))
    summary = f'<p class="summary">{esc(fig["summary"])}</p>' if kind != "table" else ""
    return f'<figure id="{fid}" class="explainer-figure" data-kind="{kind}"><h3>{esc(fig["title"])}</h3>{summary}{body}<figcaption>{status_badge(fig["status"], STATUS_LABELS[fig["status"]])} {esc(fig["caption"])} {refs}</figcaption></figure>'

def render(doc: dict) -> str:
    css_path, js_path = ROOT / "assets" / "style.css", ROOT / "assets" / "behavior.js"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    js = js_path.read_text(encoding="utf-8") if js_path.exists() else ""
    glossary = {g["term"].strip(): g["definition"] for g in doc.get("glossary", [])}
    has_diagram = any(b.get("type") == "diagram" for sec in doc["sections"] for b in sec.get("blocks", []))
    if has_diagram:
        css += (ROOT / "assets" / "diagrams.css").read_text(encoding="utf-8")
        js += (ROOT / "assets" / "diagrams.js").read_text(encoding="utf-8")
    toc = ''.join(f'<li><a href="#{esc(s["id"])}"><span class="toc-num">{i}</span><span class="toc-text">{esc(s["title"])}</span></a></li>' for i, s in enumerate(doc["sections"], 1))
    source_titles = {s["id"]: s["title"] for s in doc.get("sources", [])}
    sections = []
    for num, sec in enumerate(doc["sections"], 1):
        paras = ''.join(f'<p>{inline(p, glossary)}</p>' for p in sec.get("paragraphs", [])); callout = f'<aside class="callout callout-key"><p>{esc(sec["callout"])}</p></aside>' if sec.get("callout") else ''
        body = ''.join(block_html(b, glossary, lambda f: figure_html(f, source_titles), lambda d: render_diagram(d, lambda t: inline(t, glossary), source_titles, WARNINGS)) for b in sec.get("blocks", []))
        figs = ''.join(figure_html(f, source_titles) for f in sec.get("figures", []))
        sections.append(f'<section id="{esc(sec["id"])}"><h2><span class="section-number">{num}</span>{esc(sec["title"])}</h2>{paras}{callout}{body}{figs}</section>')
    takeaways = ''.join(f'<li>{inline(t, glossary)}</li>' for t in doc.get("takeaways", []))
    takeaway_box = f'<div class="takeaways"><p class="takeaways-title">この資料の要点</p><ol>{takeaways}</ol></div>' if takeaways else ''
    gloss = ''.join(f'<div><dt>{esc(t)}</dt><dd>{esc(d)}</dd></div>' for t, d in glossary.items())
    glossary_section = f'<section id="glossary" class="glossary"><h2>用語</h2><dl>{gloss}</dl></section>' if gloss else ''
    if gloss: toc += '<li><a href="#glossary"><span class="toc-num">・</span><span class="toc-text">用語</span></a></li>'
    source_items = []
    for s in doc.get("sources", []):
        label = esc(s["title"])
        if "url" in s: label = f'<a href="{esc(s["url"])}">{label}</a>'
        if "note" in s: label += f' <span class="source-note">{esc(s["note"])}</span>'
        source_items.append(f'<li id="{esc(s["id"])}">{label}</li>')
    sources = ''.join(source_items)
    source_section = f'<section id="sources" class="sources"><h2>参考資料</h2><ul>{sources}</ul></section>' if sources else ''
    return '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>' + esc(doc["title"]) + f'</title><style>{css}</style></head><body><div class="progress" aria-hidden="true"><span></span></div><a class="skip-link" href="#main">本文へ移動</a><div class="layout"><nav class="toc" aria-label="目次"><div class="toc-title">目次</div><ol>{toc}</ol><div class="theme-controls" aria-label="表示テーマ"><button type="button" data-theme-set="system">自動</button><button type="button" data-theme-set="light">明るい</button><button type="button" data-theme-set="dark">暗い</button></div></nav><main id="main"><header><p class="meta">読了の目安 約{reading_minutes("".join(sections))}分</p><h1>{esc(doc["title"])}</h1><p class="lead">{inline(doc["lead"], glossary)}</p>{takeaway_box}</header>{"".join(sections)}{glossary_section}{source_section}</main></div><script>{js}</script></body></html>'

def main() -> int:
    ap = argparse.ArgumentParser(description="Render explainer JSON to portable HTML")
    ap.add_argument("input", type=Path); ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--text-out", type=Path, help="also write the prose as plain text, for unslop's find-ambiguous.py")
    args = ap.parse_args()
    try:
        doc = validate(json.loads(args.input.read_text(encoding="utf-8")))
        output = render(doc)
        for note in dict.fromkeys(WARNINGS): print(f"render: note: {note}", file=sys.stderr)
        if args.text_out:
            plain = [strip_markup(t) for t in prose_strings(doc)]
            args.text_out.write_text("\n\n".join(plain) + "\n", encoding="utf-8")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{args.output.name}.", dir=args.output.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as temp:
                temp.write(output)
                temp.flush()
                os.fsync(temp.fileno())
            os.replace(temp_name, args.output)
            temp_name = None
        finally:
            if temp_name is not None:
                try:
                    os.unlink(temp_name)
                except OSError:
                    pass
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"render: {exc}", file=sys.stderr); return 2
    return 0

if __name__ == "__main__": raise SystemExit(main())
