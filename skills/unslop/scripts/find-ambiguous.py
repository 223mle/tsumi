#!/usr/bin/env python3
"""Find wording whose referent or scope needs review; findings are not verdicts."""
import argparse
import json
import re
from pathlib import Path

PATTERN = re.compile(r'など|等(?=[をにがはも、。])|同梱|共有ファイル|接続先|起動ファイル|適切|大幅')


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
        for match in PATTERN.finditer(prose):
            yield {'line': line_no, 'term': match.group(), 'text': line.strip()}


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
