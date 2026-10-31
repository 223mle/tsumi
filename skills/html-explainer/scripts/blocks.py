"""Body blocks and inline markup for explainer documents.

Text arrives as plain strings. Only a small inline vocabulary is recognised
after escaping, so authors cannot inject HTML:

    **強調**            -> <strong>
    `code`              -> <code>
    [[用語]]            -> a glossary term with its definition on hover, focus or tap
    [[表示|用語]]       -> the same term shown with different wording
    [表示](https://…)   -> an external link
"""
from __future__ import annotations

import html
import itertools
import re
from typing import Any, Callable
from urllib.parse import urlparse

TONES = {"note": "補足", "key": "要点", "warn": "注意", "example": "例"}
BLOCK_TYPES = {"p", "list", "callout", "code", "stats", "compare", "details", "figure", "diagram"}
_TIP_IDS = itertools.count(1)
INLINE_RE = re.compile(r"\*\*(.+?)\*\*|`([^`]+)`|\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]|\[([^\]]+)\]\((https?://[^)\s]+)\)")


def _fail(msg: str) -> None:
    raise ValueError(msg)


def _text(value: object, where: str, max_len: int | None = None) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(f"{where}: non-empty string required")
    if max_len is not None and len(value) > max_len:
        _fail(f"{where}: at most {max_len} characters; move detail into the body")
    return value


def _url_ok(value: str) -> bool:
    p = urlparse(value)
    return p.scheme in {"http", "https"} and bool(p.netloc) and not any(c in value for c in "<>\"'\n\r")


def check_inline(text: str, where: str, glossary: dict[str, str]) -> None:
    """Reject unknown glossary terms and malformed links before rendering."""
    for m in INLINE_RE.finditer(text):
        term = m.group(4) or m.group(3)
        if m.group(3) is not None and term.strip() not in glossary:
            _fail(f"{where}: [[{term}]] is not in glossary")
        if m.group(6) is not None and not _url_ok(m.group(6)):
            _fail(f"{where}: link must be an absolute http(s) URL")


def inline(text: str, glossary: dict[str, str]) -> str:
    out, pos = [], 0
    for m in INLINE_RE.finditer(text):
        out.append(html.escape(text[pos:m.start()]))
        if m.group(1) is not None:
            out.append(f"<strong>{html.escape(m.group(1))}</strong>")
        elif m.group(2) is not None:
            out.append(f"<code>{html.escape(m.group(2))}</code>")
        elif m.group(3) is not None:
            shown, term = m.group(3), (m.group(4) or m.group(3)).strip()
            definition = glossary.get(term, "")
            tip = f"term-tip:{next(_TIP_IDS)}"  # ":" is not allowed in author ids, so it cannot collide
            # The definition is a description of the term, not part of its name; Esc hides it (behavior.js).
            out.append(f'<span class="term" tabindex="0" data-term="{html.escape(term)}" aria-describedby="{tip}">{html.escape(shown)}'
                       f'<span class="term-tip" role="tooltip" id="{tip}" aria-hidden="true"><b>{html.escape(term)}</b>{html.escape(definition)}</span></span>')
        else:
            out.append(f'<a href="{html.escape(m.group(6), quote=True)}">{html.escape(m.group(5))}</a>')
        pos = m.end()
    out.append(html.escape(text[pos:]))
    return "".join(out)


def validate_glossary(value: object) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, list):
        _fail("glossary: array required")
    terms: dict[str, str] = {}
    for i, item in enumerate(value):
        if not isinstance(item, dict) or set(item) != {"term", "definition"}:
            _fail(f"glossary[{i}]: term and definition required")
        term = _text(item["term"], f"glossary[{i}].term", 30).strip()
        if term in terms:
            _fail(f"glossary[{i}]: duplicate term {term}")
        terms[term] = _text(item["definition"], f"glossary[{i}].definition", 120)
    return terms


def validate_block(block: object, where: str, glossary: dict[str, str],
                   check_figure: Callable[[object, str], None], check_diagram: Callable[[object, str], None]) -> None:
    if not isinstance(block, dict) or block.get("type") not in BLOCK_TYPES:
        _fail(f"{where}: type must be one of {sorted(BLOCK_TYPES)}")
    kind = block["type"]
    allowed = {
        "p": {"text"}, "list": {"items", "ordered"}, "callout": {"tone", "title", "text"},
        "code": {"code", "language", "caption"}, "stats": {"items"}, "compare": {"columns", "caption"},
        "details": {"summary", "paragraphs"}, "figure": {"figure"}, "diagram": {"bundle"},
    }[kind] | {"type"}
    extra = set(block) - allowed
    if extra:
        _fail(f"{where}: unknown fields {sorted(extra)}")

    def prose(value: object, w: str, max_len: int | None = None) -> None:
        check_inline(_text(value, w, max_len), w, glossary)

    if kind == "p":
        prose(block.get("text"), where + ".text")
    elif kind == "list":
        items = block.get("items")
        if not isinstance(items, list) or not 2 <= len(items) <= 9:
            _fail(f"{where}.items: 2 to 9 items required")
        for i, item in enumerate(items):
            prose(item, f"{where}.items[{i}]", 200)
        if "ordered" in block and not isinstance(block["ordered"], bool):
            _fail(f"{where}.ordered: boolean required")
    elif kind == "callout":
        if block.get("tone", "note") not in TONES:
            _fail(f"{where}.tone: one of {sorted(TONES)}")
        if "title" in block:
            _text(block["title"], where + ".title", 40)
        prose(block.get("text"), where + ".text", 300)
    elif kind == "code":
        if not isinstance(block.get("code"), str) or not block["code"].strip():
            _fail(f"{where}.code: non-empty string required")
        if block["code"].count("\n") > 40:
            _fail(f"{where}.code: at most 40 lines; show the relevant excerpt")
        for key in ("language", "caption"):
            if key in block:
                _text(block[key], f"{where}.{key}", 80)
    elif kind == "stats":
        items = block.get("items")
        if not isinstance(items, list) or not 2 <= len(items) <= 4:
            _fail(f"{where}.items: 2 to 4 numbers required")
        for i, item in enumerate(items):
            if not isinstance(item, dict) or set(item) - {"value", "label", "note"} or not {"value", "label"} <= set(item):
                _fail(f"{where}.items[{i}]: value and label required; optional note")
            _text(item["value"], f"{where}.items[{i}].value", 12)
            _text(item["label"], f"{where}.items[{i}].label", 40)
            if "note" in item:
                prose(item["note"], f"{where}.items[{i}].note", 60)
    elif kind == "compare":
        cols = block.get("columns")
        if not isinstance(cols, list) or not 2 <= len(cols) <= 3:
            _fail(f"{where}.columns: 2 or 3 columns required")
        for i, col in enumerate(cols):
            w = f"{where}.columns[{i}]"
            if not isinstance(col, dict) or set(col) - {"title", "label", "items", "verdict", "tone"} or not {"title", "items"} <= set(col):
                _fail(f"{w}: title and items required; optional label, verdict, tone")
            _text(col["title"], w + ".title", 40)
            if "label" in col:
                _text(col["label"], w + ".label", 20)
            if col.get("tone", "neutral") not in {"neutral", "good", "bad", "accent"}:
                _fail(f"{w}.tone: neutral, good, bad or accent")
            if not isinstance(col["items"], list) or not 1 <= len(col["items"]) <= 6:
                _fail(f"{w}.items: 1 to 6 items required")
            for j, item in enumerate(col["items"]):
                prose(item, f"{w}.items[{j}]", 120)
            if "verdict" in col:
                prose(col["verdict"], w + ".verdict", 80)
        if "caption" in block:
            prose(block["caption"], where + ".caption", 200)
    elif kind == "details":
        _text(block.get("summary"), where + ".summary", 60)
        paras = block.get("paragraphs")
        if not isinstance(paras, list) or not paras:
            _fail(f"{where}.paragraphs: non-empty array required")
        for i, para in enumerate(paras):
            prose(para, f"{where}.paragraphs[{i}]")
    elif kind == "figure":
        check_figure(block.get("figure"), where + ".figure")
    else:
        check_diagram(block.get("bundle"), where + ".bundle")


def block_html(block: dict[str, Any], glossary: dict[str, str],
               figure_html: Callable[[dict], str], diagram_html: Callable[[dict], str]) -> str:
    kind = block["type"]
    il = lambda t: inline(t, glossary)  # noqa: E731
    if kind == "p":
        return f"<p>{il(block['text'])}</p>"
    if kind == "list":
        tag = "ol" if block.get("ordered") else "ul"
        return f'<{tag} class="prose-list">' + "".join(f"<li>{il(x)}</li>" for x in block["items"]) + f"</{tag}>"
    if kind == "callout":
        tone = block.get("tone", "note")
        title = html.escape(block.get("title", TONES[tone]))
        return f'<aside class="callout callout-{tone}"><p class="callout-title"><span class="callout-icon" aria-hidden="true"></span>{title}</p><p>{il(block["text"])}</p></aside>'
    if kind == "code":
        lang = html.escape(block.get("language", ""))
        head = f'<div class="code-head"><span>{lang}</span></div>' if lang else ""
        cap = f'<figcaption>{html.escape(block["caption"])}</figcaption>' if block.get("caption") else ""
        label = html.escape(block.get("caption") or (lang + " のコード" if lang else "コード"))
        return f'<figure class="code-block">{head}<pre tabindex="0" aria-label="{label}"><code>{html.escape(block["code"])}</code></pre>{cap}</figure>'
    if kind == "stats":
        cells = "".join(
            f'<div class="stat"><span class="stat-value">{html.escape(i["value"])}</span><span class="stat-label">{html.escape(i["label"])}</span>'
            + (f'<span class="stat-note">{il(i["note"])}</span>' if i.get("note") else "") + "</div>"
            for i in block["items"])
        return f'<div class="stats" style="--n:{len(block["items"])}">{cells}</div>'
    if kind == "compare":
        cols = []
        for col in block["columns"]:
            tone = col.get("tone", "neutral")
            label = f'<span class="compare-label">{html.escape(col["label"])}</span>' if col.get("label") else ""
            items = "".join(f"<li>{il(x)}</li>" for x in col["items"])
            verdict = f'<p class="compare-verdict">{il(col["verdict"])}</p>' if col.get("verdict") else ""
            cols.append(f'<div class="compare-col compare-{tone}">{label}<h4>{html.escape(col["title"])}</h4><ul>{items}</ul>{verdict}</div>')
        cap = f'<p class="compare-caption">{il(block["caption"])}</p>' if block.get("caption") else ""
        return f'<div class="compare" style="--n:{len(cols)}">{"".join(cols)}</div>{cap}'
    if kind == "details":
        body = "".join(f"<p>{il(p)}</p>" for p in block["paragraphs"])
        return f'<details class="more"><summary>{html.escape(block["summary"])}</summary>{body}</details>'
    if kind == "figure":
        return figure_html(block["figure"])
    return diagram_html(block["bundle"])
