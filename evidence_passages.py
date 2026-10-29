"""Passage-level, source-grounded PDF highlighting for Finnish textbook.

PDF text lines are grouped by visually indented paragraphs. Claude is offered
IDs of passages actually retrieved from the PDF and selects passages supporting
its answer. No exact phrase matching is needed to position the orange overlay.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

import fitz

from book_search import tokens


def _joined(lines: list[str]) -> str:
    out = ''
    for item in lines:
        item = ' '.join(item.split())
        if not item:
            continue
        if out.endswith('-') and item[:1].islower():
            out = out[:-1] + item  # Finnish words split across PDF lines
        else:
            out = (out + ' ' + item).strip()
    return out


@lru_cache(maxsize=100)
def page_passages(pdf_path: str, number: int) -> tuple[dict, ...]:
    """Return stable, real-PDF passage IDs, original Finnish text and line rectangles.

    IDs have scope only within a single page. Each rectangle is a visible text
    line rather than a guessed word or entire page.
    """
    with fitz.open(str(pdf_path)) as pdf:
        if not 1 <= number <= len(pdf):
            return ()
        page = pdf[number - 1]
        data = page.get_text('dict', sort=True)
        result: list[dict] = []

        def record(group: list[dict]):
            if not group:
                return
            text = _joined([line['text'] for line in group])
            if len(text) < 48 or not len(re.findall(r'\w+', text)) >= 7:
                return
            # Normalized percentages in page coordinates; rendering at ANY zoom works.
            rects = []
            for line in group:
                b = fitz.Rect(line['box'])
                if b.is_empty or b.width < 1 or b.height < 1:
                    continue
                rects.append({'x': round(max(0, b.x0 - .8) / page.rect.width * 100, 3),
                              'y': round(max(0, b.y0 - 1) / page.rect.height * 100, 3),
                              'w': round(min(b.width + 1.6, page.rect.width - b.x0) / page.rect.width * 100, 3),
                              'h': round((b.height + 2) / page.rect.height * 100, 3)})
            if not rects:
                return
            result.append({'id': f's{len(result)}', 'page': number,
                           'text': text, 'rects': rects})

        for block in data['blocks']:
            if block.get('type', 0) != 0 or 'lines' not in block:
                continue
            lines = []
            for l in block['lines']:
                spans = [s['text'] for s in l.get('spans', []) if s.get('text')]
                txt = ''.join(spans).strip()
                if not txt:
                    continue
                box = fitz.Rect(l['bbox'])
                if box.y0 < 49 or box.y1 > page.rect.height - 30:
                    continue  # running header / printed page number
                lines.append({'text': txt, 'box': l['bbox']})
            if not lines:
                continue
            min_x = min(l['box'][0] for l in lines)
            group = []
            last_y = None
            for line in lines:
                x, y = line['box'][0], line['box'][1]
                # Many pages have several independent indented paragraphs in one
                # PyMuPDF block. Separate them, rather than highlighting the block.
                indent = x - min_x >= 10.5
                gap = last_y is not None and y - last_y > 24
                if group and (indent or gap):
                    record(group)
                    group = []
                group.append(line)
                last_y = y
            record(group)
        return tuple(result)


def overlap(a: str, b: str) -> float:
    """Soft lexical overlap handles inflection and excerpt boundaries."""
    aa, bb = set(tokens(a)), set(tokens(b))
    if not aa or not bb:
        return 0.0
    match = len(aa.intersection(bb))
    return match / max(4, min(len(aa), len(bb)))


def offered_passages(pdf_path: str | Path, excerpts: list[dict], max_per_page: int = 12) -> dict[int, list[dict]]:
    """Only offer actual source passages related to the retrieved excerpts."""
    page_chunks: dict[int, list[str]] = {}
    for chunk in excerpts:
        page_chunks.setdefault(int(chunk['page']), []).append(chunk['text'])
    chosen = {}
    for page, chunks in page_chunks.items():
        paragraphs = list(page_passages(str(pdf_path), page))
        # Full-page user requests can offer all paragraphs (up to a safe cap).
        ranking = [(max(overlap(p['text'], excerpt) for excerpt in chunks), p)
                   for p in paragraphs]
        good = [p for score, p in ranking if score >= .24]
        if not good and ranking:
            good = [p for _, p in sorted(ranking, key=lambda t: -t[0])[:3]]
        good = sorted(good, key=lambda p: -max(overlap(p['text'], chunk) for chunk in chunks))[:max_per_page]
        # Restore PDF reading order so the model gets coherent context.
        chosen[page] = sorted(good, key=lambda p: int(p['id'][1:]))
    return chosen


def selected_passages(model_evidence, pages: set[int], offered: dict[int, list[dict]],
                      legacy_quotes=None, fallback_query='') -> dict[int, list[str]]:
    """Validate model IDs; supplement missing citation-page support conservatively."""
    allowed = {p: {item['id']: item for item in spans} for p, spans in offered.items()}
    result = {p: [] for p in pages if allowed.get(p)}
    if isinstance(model_evidence, list):
        for item in model_evidence[:40]:
            if not isinstance(item, dict) or type(item.get('page')) is not int:
                continue
            page = item['page']
            if page not in result or not isinstance(item.get('ids'), list):
                continue
            for val in item['ids'][:10]:
                if isinstance(val, str) and val in allowed[page] and val not in result[page] and len(result[page]) < 8:
                    result[page].append(val)

    # Old Claude output may still provide Finnish quote snippets. Use their
    # *meaningful word overlap* to locate a paragraph; no verbatim match needed.
    for item in (legacy_quotes or [])[:24] if isinstance(legacy_quotes, list) else []:
        if not isinstance(item, dict) or type(item.get('page')) is not int:
            continue
        page = item['page']
        if page not in result or result[page]:
            continue
        quote = str(item.get('quote') or '').strip()
        if len(quote) < 12:
            continue
        candidates = sorted(offered[page], key=lambda p: -overlap(quote, p['text']))
        if candidates and overlap(quote, candidates[0]['text']) >= .22:
            result[page] = [candidates[0]['id']]

    # The book answer already has a validated citation to this page. If the
    # model omitted passage IDs, highlight the most topic-relevant retrieved
    # passages, not arbitrary headings, search tokens or unrelated pages.
    for page, ids in result.items():
        if ids or not offered.get(page):
            continue
        scored = sorted([(overlap(fallback_query, p['text']), p['id']) for p in offered[page]],
                        reverse=True)
        result[page] = [s[1] for s in scored[:2] if s[0] >= .08]
        if not result[page]:
            result[page] = [offered[page][0]['id']]
    return {page: ids[:8] for page, ids in result.items() if ids}
