"""Line breaking for short Japanese labels inside SVG.

SVG text does not wrap, so labels are split here. Breaks prefer, in order:
an explicit newline, a space or middle dot, the end of a particle or
punctuation, and a change of script (katakana to kanji, Latin to kana).
A run of one script, such as フルサービスリゾルバー, is split only when no
better point fits, and then as evenly as possible.
"""
from __future__ import annotations

import re
import unicodedata

PARTICLES = set("のをにはがでともへや、。，．）」』")
SOFT = set(" 　・/／")


def units(text: str) -> float:
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def _script(c: str) -> str:
    if "゠" <= c <= "ヿ" or c == "ー":
        return "katakana"
    if "぀" <= c <= "ゟ":
        return "hiragana"
    if "一" <= c <= "鿿" or "㐀" <= c <= "䶿":
        return "kanji"
    if c.isascii() and c.isalnum():
        return "latin"
    return "other"


def _break_cost(text: str, i: int) -> int:
    """Cost of breaking before text[i]; lower is better."""
    prev, cur = text[i - 1], text[i]
    if prev in SOFT or cur in SOFT:
        return 0
    if prev in PARTICLES:
        return 1
    if cur in "（「『(":
        return 1
    a, b = _script(prev), _script(cur)
    if a != b and "other" not in (a, b):
        # 「ー」 belongs to the katakana run before it; never start a line with a small kana.
        if cur in "ーゃゅょぁぃぅぇぉっャュョァィゥェォッ":
            return 9
        return 2
    return 6


def wrap(text: str, max_units: float, max_lines: int = 2) -> list[str] | None:
    """Split text into at most max_lines lines no wider than max_units, or return None."""
    out: list[str] = []
    for part in text.split("\n"):
        lines = _wrap_one(part.strip(), max_units, max_lines - len(out))
        if lines is None:
            return None
        out.extend(lines)
    return out if len(out) <= max_lines else None


def _wrap_one(text: str, max_units: float, max_lines: int) -> list[str] | None:
    if units(text) <= max_units:
        return [text]
    if max_lines <= 1:
        return None
    best = None
    for i in range(1, len(text)):
        head, tail = text[:i].rstrip(" 　"), text[i:].lstrip(" 　")
        if not head or not tail or units(head) > max_units:
            continue
        rest = _wrap_one(tail, max_units, max_lines - 1)
        if rest is None:
            continue
        widths = [units(head)] + [units(x) for x in rest]
        score = _break_cost(text, i) * 10 + (max(widths) - min(widths)) / 4 + len(rest) * 3
        if best is None or score < best[0]:
            best = (score, [head] + rest)
    return best[1] if best else None


def plain(text: str) -> str:
    """The label without explicit line breaks, for accessible names and matching."""
    return re.sub(r"\s*\n\s*", "", text)
