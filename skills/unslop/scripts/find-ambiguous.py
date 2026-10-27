#!/usr/bin/env python3
"""Find wording whose referent or scope needs review; findings are not verdicts."""
import argparse
import json
import re
from pathlib import Path

RULES = (
    ('scope', re.compile(r'など|その他'),
     '列挙の範囲は何か。全件を挙げるか、例と範囲・確認先を示せるか。'),
    ('referent', re.compile(r'(?<![ぁ-んァ-ヶ])(?:これ|それ|あれ|そちら)(?=[はがをにへとも、。！？\s]|で(?!も)|$)'),
     'どの名詞を指すか。一つに決まるか。戻って探す必要があれば対象の名詞を添える。'),
    ('criterion', re.compile(r'適宜|適切に|所定の|一定の|大幅に|さまざまな|様々な'),
     '動作・条件・程度は何か。材料にある具体的な操作や基準を示せるか。'),
)


def findings(text):
    fence = None
    for line_no, line in enumerate(text.splitlines(), 1):
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        # Identifiers, destinations and URLs are not prose to rewrite.
        prose = re.sub(r'`[^`]*`|https?://\S+|\]\([^)]*\)', '', line)
        matches = [(match.start(), kind, question, match.group())
                   for kind, pattern, question in RULES
                   for match in pattern.finditer(prose)]
        for _, kind, question, term in sorted(matches):
            yield {'line': line_no, 'term': term, 'kind': kind,
                   'question': question, 'text': line.strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+', type=Path)
    args = parser.parse_args()
    for path in args.paths:
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError) as error:
            parser.exit(2, f'{path}: {error}\n')
        print(json.dumps({'path': str(path), 'review_candidates': list(findings(text)),
                          'notice': '候補ゼロでも意味・構成の合格を保証しない。候補は自動置換せず、対象・範囲・参照先を本文で確認する。'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
